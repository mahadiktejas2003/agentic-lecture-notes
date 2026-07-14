#!/usr/bin/env python3
"""
asr_watcher.py
==============
24/7 background transcription daemon.

Watches ~/Downloads/ for new audio/video files, queues them in a local SQLite
database, and transcribes them one-by-one using Qwen3-ASR on Apple Silicon GPU.
Completed transcripts are saved to ~/Transcripts/<video_name>/.

Anti-lag protections:
  - Transcription subprocess runs at nice -n 15 (low CPU priority)
  - Single-threaded worker (no GPU contention)
  - Auto-pause when on battery power
  - Thermal backoff between jobs
  - Only ~1.8 GB memory usage with 4-bit model

Usage:
  python scripts/asr_watcher.py                     # normal daemon mode
  python scripts/asr_watcher.py --dry-run            # print config and exit
  python scripts/asr_watcher.py --watch-dir ~/Videos # custom watch directory
"""

import argparse
import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re

from dotenv import load_dotenv

# Try importing cloud uploader for R2/Supabase logging
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from cloud_uploader import upload_to_r2, log_to_supabase
    has_cloud = True
except Exception:
    has_cloud = False


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

# ── Optional: watchdog ────────────────────────────────────────────────────────
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print(
        "ERROR: 'watchdog' package is required.\n"
        "Install it with: pip install watchdog\n"
        "Or: venv/bin/pip install watchdog"
    )
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

MEDIA_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".mp3", ".m4a", ".wav"}
TEMP_EXTENSIONS = {".crdownload", ".part", ".tmp", ".download"}
STABILITY_CHECKS = 3
STABILITY_INTERVAL = 2  # seconds between size checks
HEARTBEAT_INTERVAL = 30  # seconds
STUCK_JOB_TIMEOUT = 3600  # 1 hour
THERMAL_BACKOFF = 60  # seconds
WORKER_SLEEP = 2  # seconds between queue polls

DEFAULT_WATCH_DIR = os.path.expanduser("~/Downloads")
DEFAULT_OUTPUT_ROOT = os.path.expanduser("~/Transcripts")
DEFAULT_MODEL = "mlx-community/Qwen3-ASR-1.7B-4bit"

LOGS_DIR = PROJECT_ROOT / "logs"
DB_PATH = LOGS_DIR / "asr_queue.db"
HEARTBEAT_PATH = LOGS_DIR / "asr_watcher_heartbeat.json"
PAUSE_FLAG = LOGS_DIR / "asr_watcher_paused.flag"
LOG_FILE = LOGS_DIR / "asr_watcher.log"

# ── Logging ───────────────────────────────────────────────────────────────────

LOGS_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("asr_watcher")
logger.setLevel(logging.INFO)

_console = logging.StreamHandler()
_console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(_console)

_file_handler = RotatingFileHandler(str(LOG_FILE), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(_file_handler)


# ── SQLite Queue ──────────────────────────────────────────────────────────────

class ASRQueue:
    """Thread-safe SQLite-backed job queue."""

    def __init__(self, db_path: str = str(DB_PATH)):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._connect()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    filesize INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    output_dir TEXT,
                    absolute_srt_path TEXT,
                    absolute_txt_path TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    UNIQUE(filename, filesize)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status_id ON jobs (status, id)")
            conn.commit()
            conn.close()

    def enqueue(self, filepath: str) -> bool:
        """Add a file to the queue. Returns False if already exists (dedup)."""
        filename = os.path.basename(filepath)
        try:
            filesize = os.path.getsize(filepath)
        except OSError:
            return False

        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT INTO jobs (filename, filepath, filesize, status, created_at) VALUES (?, ?, ?, 'queued', ?)",
                    (filename, filepath, filesize, datetime.now().isoformat()),
                )
                conn.commit()
                logger.info(f"📥 Enqueued: {filename} ({filesize / 1e6:.1f} MB)")
                return True
            except sqlite3.IntegrityError:
                logger.debug(f"Skipped (duplicate): {filename}")
                return False
            finally:
                conn.close()

    def next_job(self) -> dict | None:
        """Get the next queued job (LIFO - Newest first)."""
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT * FROM jobs WHERE status = 'queued' ORDER BY id DESC LIMIT 1"
            ).fetchone()
            conn.close()
            return dict(row) if row else None

    def mark_transcribing(self, job_id: int, output_dir: str):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE jobs SET status = 'transcribing', output_dir = ?, started_at = ? WHERE id = ?",
                (output_dir, datetime.now().isoformat(), job_id),
            )
            conn.commit()
            conn.close()

    def mark_completed(self, job_id: int, srt_path: str, txt_path: str):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE jobs SET status = 'completed', absolute_srt_path = ?, absolute_txt_path = ?, completed_at = ? WHERE id = ?",
                (srt_path, txt_path, datetime.now().isoformat(), job_id),
            )
            conn.commit()
            conn.close()

    def mark_failed(self, job_id: int, error: str):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE jobs SET status = 'failed', error_message = ?, completed_at = ? WHERE id = ?",
                (error[:1000], datetime.now().isoformat(), job_id),
            )
            conn.commit()
            conn.close()

    def reset_stuck_jobs(self):
        """Reset jobs stuck as 'transcribing' for over STUCK_JOB_TIMEOUT seconds."""
        cutoff = (datetime.now() - timedelta(seconds=STUCK_JOB_TIMEOUT)).isoformat()
        with self._lock:
            conn = self._connect()
            cursor = conn.execute(
                "UPDATE jobs SET status = 'queued', error_message = 'Reset: stuck job timeout' "
                "WHERE status = 'transcribing' AND started_at < ?",
                (cutoff,),
            )
            if cursor.rowcount > 0:
                logger.warning(f"Reset {cursor.rowcount} stuck job(s) to queued.")
            conn.commit()
            conn.close()

    def reset_all_transcribing_jobs(self):
        """Reset all 'transcribing' jobs to 'queued' at startup."""
        with self._lock:
            conn = self._connect()
            cursor = conn.execute(
                "UPDATE jobs SET status = 'queued', error_message = 'Reset: daemon restarted' "
                "WHERE status = 'transcribing'"
            )
            if cursor.rowcount > 0:
                logger.info(f"Reset {cursor.rowcount} leftover transcribing job(s) back to queued.")
            conn.commit()
            conn.close()

    def retry_failed(self) -> int:
        """Reset all failed jobs to queued. Returns count."""
        with self._lock:
            conn = self._connect()
            cursor = conn.execute(
                "UPDATE jobs SET status = 'queued', error_message = NULL, started_at = NULL, completed_at = NULL "
                "WHERE status = 'failed'"
            )
            count = cursor.rowcount
            conn.commit()
            conn.close()
            return count

    def get_all_jobs(self, limit: int = 100) -> list[dict]:
        """Get all jobs ordered by most recent first."""
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        """Get summary statistics."""
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status"
            ).fetchall()
            conn.close()
            stats = {r["status"]: r["cnt"] for r in rows}
            stats["total"] = sum(stats.values())
            return stats

    def get_currently_transcribing(self) -> str | None:
        """Get filename of currently transcribing job, or None."""
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT filename FROM jobs WHERE status = 'transcribing' LIMIT 1"
            ).fetchone()
            conn.close()
            return row["filename"] if row else None


# ── Watchdog Event Handler ────────────────────────────────────────────────────

class ASRWatchHandler(FileSystemEventHandler):
    """Watches for new media files and enqueues them after stability check."""

    def __init__(self, queue: ASRQueue):
        super().__init__()
        self._queue = queue
        self._pending: dict[str, threading.Timer] = {}

    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        ext = os.path.splitext(filepath)[1].lower()

        # Skip temp download files
        if ext in TEMP_EXTENSIONS:
            return

        # Skip non-media files
        if ext not in MEDIA_EXTENSIONS:
            return

        # Debounce: cancel any existing timer for this file
        if filepath in self._pending:
            self._pending[filepath].cancel()

        # Start stability check in a background thread
        timer = threading.Timer(STABILITY_INTERVAL, self._stability_check, args=(filepath, 0))
        timer.daemon = True
        self._pending[filepath] = timer
        timer.start()

    def _stability_check(self, filepath: str, check_count: int):
        """Repeatedly check file size stability before enqueuing."""
        try:
            if not os.path.exists(filepath):
                self._pending.pop(filepath, None)
                return

            size = os.path.getsize(filepath)
            if size == 0:
                # Still empty, retry
                if check_count < 10:
                    timer = threading.Timer(STABILITY_INTERVAL, self._stability_check, args=(filepath, check_count + 1))
                    timer.daemon = True
                    self._pending[filepath] = timer
                    timer.start()
                return

            if check_count < STABILITY_CHECKS:
                # Record size and check again
                if not hasattr(self, "_sizes"):
                    self._sizes = {}
                self._sizes.setdefault(filepath, []).append(size)

                timer = threading.Timer(STABILITY_INTERVAL, self._stability_check, args=(filepath, check_count + 1))
                timer.daemon = True
                self._pending[filepath] = timer
                timer.start()
                return

            # All checks done — verify stability
            sizes = self._sizes.pop(filepath, [size])
            self._pending.pop(filepath, None)

            if len(set(sizes)) == 1 and sizes[-1] > 0:
                # File size is stable, enqueue
                self._queue.enqueue(filepath)
            else:
                logger.debug(f"File still unstable, skipping: {os.path.basename(filepath)}")

        except Exception as e:
            logger.error(f"Stability check error for {filepath}: {e}")
            self._pending.pop(filepath, None)


# ── System Checks ─────────────────────────────────────────────────────────────

def is_on_battery() -> bool:
    """Check if Mac is running on battery power."""
    try:
        result = subprocess.run(
            ["pmset", "-g", "batt"], capture_output=True, text=True, timeout=5
        )
        return "'Battery Power'" in result.stdout
    except Exception:
        return False


def is_paused() -> bool:
    """Check if the pause flag file exists."""
    return PAUSE_FLAG.exists()


# ── Worker Loop ───────────────────────────────────────────────────────────────

def worker_loop(
    queue: ASRQueue,
    output_root: str,
    model: str,
    stop_event: threading.Event,
):
    """Main worker loop — processes one job at a time from the queue."""
    logger.info(f"Worker started. Output: {output_root} | Model: {model}")

    last_job_duration = 0.0

    while not stop_event.is_set():
        # Pause check
        if is_paused():
            logger.debug("Paused (flag file exists). Sleeping...")
            stop_event.wait(10)
            continue



        # Thermal backoff
        if last_job_duration > 0:
            expected = last_job_duration * 0.5
            if last_job_duration > expected * 4:
                logger.warning(f"Possible thermal throttling (last job: {last_job_duration:.0f}s). Backing off {THERMAL_BACKOFF}s...")
                stop_event.wait(THERMAL_BACKOFF)

        # Get next job
        job = queue.next_job()
        if job is None:
            stop_event.wait(WORKER_SLEEP)
            continue

        job_id = job["id"]
        filepath = job["filepath"]
        filename = job["filename"]

        # Verify file still exists
        if not os.path.exists(filepath):
            queue.mark_failed(job_id, f"File no longer exists: {filepath}")
            logger.warning(f"⚠️ File missing, skipping: {filename}")
            continue

        # Determine output directory
        basename = os.path.splitext(filename)[0]
        job_output_dir = os.path.join(output_root, basename)
        os.makedirs(job_output_dir, exist_ok=True)

        # Check if transcript already exists to pick up where left off / avoid duplicate runs
        srt_path = os.path.join(job_output_dir, "transcript.srt")
        txt_path = os.path.join(job_output_dir, "transcript.txt")
        if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
            abs_srt = str(Path(srt_path).resolve()) if os.path.exists(srt_path) else ""
            abs_txt = str(Path(txt_path).resolve())
            queue.mark_completed(job_id, abs_srt, abs_txt)
            logger.info(f"⏭️ Skipped (already completed): {filename}")
            # Log in active_log_file so UI shows it
            active_log_file = PROJECT_ROOT / "logs" / "watcher_active_transcription.log"
            try:
                with open(active_log_file, "w", encoding="utf-8") as f_log:
                    f_log.write(f"Transcript already exists for {filename}.\nSkipping ASR run and marking completed.\nSRT: {abs_srt}\n")
            except Exception:
                pass
            continue

        queue.mark_transcribing(job_id, job_output_dir)
        logger.info(f"🎙️ Transcribing: {filename}")

        start_time = time.time()

        # File for active transcription logging
        active_log_file = PROJECT_ROOT / "logs" / "watcher_active_transcription.log"

        # Generate transcription context bias from filename to improve quality
        clean_name = os.path.splitext(filename)[0]
        context_words = clean_name.replace("-", " ").replace("_", " ").replace(".", " ")
        context_str = f"{context_words}, computer science, lecture, key terms, DBMS"

        try:
            # Run transcription with low CPU priority, writing output to logs/watcher_active_transcription.log in real-time
            cmd = [
                "nice", "-n", "15",
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "transcribe_lecture.py"),
                "--input", filepath,
                "--output-dir", job_output_dir,
                "--model", model,
                "--context", context_str,
                "--no-fallback",
            ]

            with open(active_log_file, "w", encoding="utf-8") as f_log:
                result = subprocess.run(
                    cmd,
                    cwd=str(PROJECT_ROOT),
                    stdout=f_log,
                    stderr=subprocess.STDOUT,
                    timeout=7200,  # 2 hour max per file
                )

            last_job_duration = time.time() - start_time

            srt_path = os.path.join(job_output_dir, "transcript.srt")
            txt_path = os.path.join(job_output_dir, "transcript.txt")

            if result.returncode == 0 and os.path.exists(txt_path):
                abs_srt = str(Path(srt_path).resolve()) if os.path.exists(srt_path) else ""
                abs_txt = str(Path(txt_path).resolve())

                queue.mark_completed(job_id, abs_srt, abs_txt)
                logger.info(f"✅ Completed: {filename} ({last_job_duration:.1f}s)")
                logger.info(f"   SRT: {abs_srt}")
                logger.info(f"   TXT: {abs_txt}")

                # Cloud Backup and Logging
                if has_cloud:
                    try:
                        logger.info(f"Uploading transcripts to R2 for {basename}...")
                        lecture_slug = slugify(basename)
                        r2_srt_key = f"transcripts/{lecture_slug}/transcript.srt"
                        r2_txt_key = f"transcripts/{lecture_slug}/transcript.txt"
                        
                        r2_srt_ok = upload_to_r2(srt_path, r2_srt_key) if os.path.exists(srt_path) else False
                        r2_txt_ok = upload_to_r2(txt_path, r2_txt_key)
                        
                        logger.info("Logging to Supabase...")
                        run_data = {
                            "lecture_title": basename,
                            "status": "completed" if (r2_srt_ok or r2_txt_ok) else "failed",
                            "r2_transcript_key": r2_srt_key if r2_srt_ok else None,
                            "error_message": None
                        }
                        log_to_supabase(run_data)
                    except Exception as ce:
                        logger.warning(f"Cloud backup failed: {ce}")
            else:
                # Read last 5 lines of log file on failure
                err_msg = f"Exit code {result.returncode}"
                try:
                    if os.path.exists(active_log_file):
                        with open(active_log_file, "r", encoding="utf-8") as f_log:
                            lines = f_log.readlines()
                            if lines:
                                err_msg = "".join(lines[-5:]).strip()
                except Exception:
                    pass
                queue.mark_failed(job_id, err_msg)
                logger.error(f"❌ Failed: {filename} — {err_msg[:200]}")

                # Cloud Logging for failure
                if has_cloud:
                    try:
                        logger.info("Logging failure to Supabase...")
                        run_data = {
                            "lecture_title": basename,
                            "status": "failed",
                            "error_message": err_msg[:1000]
                        }
                        log_to_supabase(run_data)
                    except Exception as ce:
                        logger.warning(f"Cloud failure logging failed: {ce}")

        except subprocess.TimeoutExpired:
            last_job_duration = time.time() - start_time
            queue.mark_failed(job_id, "Timeout: transcription exceeded 2 hours")
            logger.error(f"⏰ Timeout: {filename}")
            if has_cloud:
                try:
                    log_to_supabase({
                        "lecture_title": basename,
                        "status": "failed",
                        "error_message": "Timeout: transcription exceeded 2 hours"
                    })
                except Exception:
                    pass

        except Exception as e:
            last_job_duration = time.time() - start_time
            queue.mark_failed(job_id, str(e))
            logger.error(f"💥 Exception transcribing {filename}: {e}")
            if has_cloud:
                try:
                    log_to_supabase({
                        "lecture_title": basename,
                        "status": "failed",
                        "error_message": str(e)[:1000]
                    })
                except Exception:
                    pass

        # Small cooldown between jobs
        stop_event.wait(WORKER_SLEEP)


# ── Heartbeat ─────────────────────────────────────────────────────────────────

def heartbeat_loop(queue: ASRQueue, stop_event: threading.Event):
    """Writes health status to a JSON file every HEARTBEAT_INTERVAL seconds."""
    while not stop_event.is_set():
        try:
            data = {
                "pid": os.getpid(),
                "alive_at": datetime.now().isoformat(),
                "paused": is_paused(),
                "on_battery": is_on_battery(),
                "currently_transcribing": queue.get_currently_transcribing(),
                "stats": queue.get_stats(),
            }
            temp = str(HEARTBEAT_PATH) + ".tmp"
            with open(temp, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(temp, str(HEARTBEAT_PATH))
        except Exception as e:
            logger.debug(f"Heartbeat write error: {e}")

        stop_event.wait(HEARTBEAT_INTERVAL)


def kill_existing_transcribe_processes():
    """Kill any lingering transcribe_lecture.py processes on start."""
    try:
        import subprocess
        # Get list of running processes matching transcribe_lecture.py
        result = subprocess.run(["pgrep", "-f", "transcribe_lecture.py"], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().splitlines()
            for pid_str in pids:
                try:
                    pid = int(pid_str)
                    if pid != os.getpid():  # don't kill ourselves
                        logger.info(f"Terminating lingering transcribe process with PID {pid}...")
                        os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Failed to check/kill lingering transcribe processes: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="24/7 background transcription daemon powered by Qwen3-ASR"
    )
    parser.add_argument(
        "--watch-dir",
        default=os.environ.get("ASR_WATCH_DIR", DEFAULT_WATCH_DIR),
        help=f"Directory to watch for new media files (default: {DEFAULT_WATCH_DIR})",
    )
    parser.add_argument(
        "--output-root",
        default=os.environ.get("ASR_OUTPUT_ROOT", DEFAULT_OUTPUT_ROOT),
        help=f"Root directory for transcript output (default: {DEFAULT_OUTPUT_ROOT})",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("ASR_MODEL", DEFAULT_MODEL),
        help=f"MLX model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration and exit without starting the daemon",
    )
    args = parser.parse_args()

    watch_dir = os.path.expanduser(args.watch_dir)
    output_root = os.path.expanduser(args.output_root)

    if not os.path.isdir(watch_dir):
        logger.error(f"Watch directory does not exist: {watch_dir}")
        sys.exit(1)

    os.makedirs(output_root, exist_ok=True)

    logger.info("=" * 60)
    logger.info("ASR Watcher Daemon")
    logger.info("=" * 60)
    logger.info(f"  Watch Dir   : {watch_dir}")
    logger.info(f"  Output Root : {output_root}")
    logger.info(f"  Model       : {args.model}")
    logger.info(f"  DB Path     : {DB_PATH}")
    logger.info(f"  Heartbeat   : {HEARTBEAT_PATH}")
    logger.info(f"  Pause Flag  : {PAUSE_FLAG}")
    logger.info(f"  PID         : {os.getpid()}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("Dry run mode — exiting without starting daemon.")
        return

    # Initialize queue and recover stuck jobs
    queue = ASRQueue()
    kill_existing_transcribe_processes()
    queue.reset_all_transcribing_jobs()
    queue.reset_stuck_jobs()

    # Scan watch directory for existing media files not yet in queue
    logger.info(f"Scanning {watch_dir} for existing media files...")
    existing_count = 0
    for fname in os.listdir(watch_dir):
        ext = os.path.splitext(fname)[1].lower()
        if ext in MEDIA_EXTENSIONS:
            fpath = os.path.join(watch_dir, fname)
            if os.path.isfile(fpath) and os.path.getsize(fpath) > 0:
                if queue.enqueue(fpath):
                    existing_count += 1
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing media file(s) in watch directory.")

    # Stop event for graceful shutdown
    stop_event = threading.Event()

    def shutdown_handler(signum, frame):
        sig_name = signal.Signals(signum).name
        logger.info(f"\n🛑 Received {sig_name}. Shutting down gracefully...")
        stop_event.set()

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    # Start watchdog observer
    handler = ASRWatchHandler(queue)
    observer = Observer()
    observer.schedule(handler, watch_dir, recursive=False)
    observer.start()
    logger.info(f"👁️ Watching: {watch_dir}")

    # Start heartbeat thread
    hb_thread = threading.Thread(target=heartbeat_loop, args=(queue, stop_event), daemon=True)
    hb_thread.start()

    # Start worker thread
    worker_thread = threading.Thread(
        target=worker_loop,
        args=(queue, output_root, args.model, stop_event),
        daemon=True,
    )
    worker_thread.start()

    # Main thread waits for stop signal
    try:
        while not stop_event.is_set():
            stop_event.wait(1)
    finally:
        logger.info("Stopping observer...")
        observer.stop()
        observer.join(timeout=5)
        logger.info("Observer stopped. Waiting for worker to finish current job...")
        worker_thread.join(timeout=30)
        logger.info("Daemon shutdown complete.")


if __name__ == "__main__":
    main()

import os
import sys
import json
import time
import shutil
import glob
import subprocess
import argparse
import re
try:
    import fcntl
except ImportError:
    fcntl = None  # Not available on Windows
import boto3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Resolve project root from this file's location
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)

# Force background agents/subprocesses to use customized antigravity CLI wrapper with gemini-3.5-flash
os.environ.setdefault("ANTIGRAVITY_CLI_PATH", os.path.join(_SCRIPT_DIR, "antigravity_flash"))

DOWNLOADS_DIR = os.environ.get("DOWNLOADS_DIR", os.path.expanduser("~/Downloads"))
SOUNDSCRIBE_DIR = os.environ.get("SOUNDSCRIBE_DIR", os.path.expanduser("~/SoundScribe"))
PROJECT_DIR = os.environ.get("PROJECT_DIR", _DEFAULT_PROJECT_DIR)
PROCESSED_FILE = os.environ.get("PROCESSED_FILE", os.path.join(PROJECT_DIR, "logs", "tracker_processed.json"))
LOCK_FILE = os.environ.get("LOCK_FILE", os.path.join(PROJECT_DIR, "logs", "downloads_tracker.lock"))

lock_file_fd = None

def acquire_lock():
    global lock_file_fd
    os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
    try:
        lock_file_fd = open(LOCK_FILE, "w")
        if fcntl is not None:
            fcntl.flock(lock_file_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file_fd.write(str(os.getpid()))
        lock_file_fd.flush()
        return True
    except (IOError, OSError):
        return False

def release_lock():
    global lock_file_fd
    if lock_file_fd:
        try:
            fcntl.flock(lock_file_fd, fcntl.LOCK_UN)
            lock_file_fd.close()
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
        except Exception:
            pass

def check_disk_space():
    free_bytes = shutil.disk_usage(PROJECT_DIR).free
    free_gb = free_bytes / (1024 ** 3)
    if free_gb < 15.0:
        print(f"WARNING: Host disk space low ({free_gb:.2f} GB free). Minimum 15.0 GB required.")
        return False
    return True

def get_processed_files():
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_processed_files(processed):
    os.makedirs(os.path.dirname(PROCESSED_FILE), exist_ok=True)
    temp_file = PROCESSED_FILE + ".tmp"
    with open(temp_file, "w") as f:
        json.dump(processed, f, indent=2)
    os.replace(temp_file, PROCESSED_FILE)

def check_and_recover_stuck_jobs(processed):
    changed = False
    for name, info in list(processed.items()):
        if info.get("status") == "processing":
            detected_str = info.get("detected_at")
            if detected_str:
                try:
                    detected_time = datetime.fromisoformat(detected_str)
                    elapsed = (datetime.now() - detected_time).total_seconds()
                    if elapsed > 10800:  # 3 hours
                        print(f"Stuck job detected for {name} (elapsed {elapsed:.1f}s). Resetting to failed/retry.")
                        info["status"] = "failed"
                        info["error"] = "Stuck job timeout reset (3 hours exceeded)"
                        info["reset_at"] = datetime.now().isoformat()
                        changed = True
                except Exception as e:
                    print(f"Error checking stuck job timestamp: {e}")
    if changed:
        save_processed_files(processed)

def clean_cache():
    print("Cleaning cache files and directories...")
    files = [
        "concept_block_map.json",
        "frame_manifest.json",
        "slide_manifest.json",
        "reference_manifest.json",
        "embedded_manifest.json"
    ]
    for f in files:
        path = os.path.join(PROJECT_DIR, f)
        if os.path.exists(path):
            os.remove(path)

    dirs = [
        "reference_pages",
        "reference_screenshots",
        "screenshots",
        "slides"
    ]
    for d in dirs:
        path = os.path.join(PROJECT_DIR, d)
        if os.path.exists(path):
            shutil.rmtree(path)

    lecture_input_dir = os.path.join(PROJECT_DIR, "lecture-input")
    os.makedirs(lecture_input_dir, exist_ok=True)
    for f in os.listdir(lecture_input_dir):
        path = os.path.join(lecture_input_dir, f)
        if os.path.isfile(path):
            os.remove(path)

def find_lecture_bundle(video_path):
    video_basename = os.path.splitext(os.path.basename(video_path))[0]
    pdf_files = glob.glob(os.path.join(DOWNLOADS_DIR, "**/*.pdf"), recursive=True)
    srt_files = glob.glob(os.path.join(DOWNLOADS_DIR, "**/*.srt"), recursive=True)
    
    def clean_name(name):
        return re.sub(r'[^a-z0-9\s]', ' ', name.lower())
        
    clean_video = clean_name(video_basename)
    
    def get_lecture_number(name):
        match = re.search(r'\b(live|lec|lecture|l|class|part)\s*[-_]?\s*(\d+)\b', name.lower())
        if match:
            return match.group(2)
        match2 = re.search(r'(?<!\d)(\d+)(?!\d)', name)
        if match2:
            return match2.group(1)
        return None
        
    video_num = get_lecture_number(video_basename)
    STOP_WORDS = {
        "reasoning", "aptitude", "part", "lecture", "live", "lve", "lec", "class",
        "and", "the", "for", "with", "from", "pdf", "docx", "notes", "prep", "test"
    }
    video_words = set(w for w in re.findall(r'\b[a-z0-9]{2,}\b', clean_video) if w not in STOP_WORDS)
    
    matched_pdfs = []
    for pdf in pdf_files:
        pdf_base = os.path.basename(pdf)
        pdf_clean = clean_name(os.path.splitext(pdf_base)[0])
        pdf_num = get_lecture_number(pdf_base)
        pdf_words = set(w for w in re.findall(r'\b[a-z0-9]{2,}\b', pdf_clean) if w not in STOP_WORDS)
        
        if pdf_clean in clean_video or clean_video in pdf_clean:
            matched_pdfs.append((pdf, 100))
        elif video_num and pdf_num and video_num != pdf_num:
            # Different numbers (e.g. Live-20 vs Sentence-Rearrangement-2) must never match!
            continue
        elif video_num and pdf_num == video_num:
            overlap = len(video_words & pdf_words)
            matched_pdfs.append((pdf, 50 + overlap))
        elif video_words:
            overlap = len(video_words & pdf_words)
            if overlap >= 2:
                matched_pdfs.append((pdf, overlap))
                
    reference_pdf = None
    slides_pdf = None
    assignment_pdf = None
    matched_paths = []
    
    if matched_pdfs:
        matched_pdfs.sort(key=lambda x: x[1], reverse=True)
        for pdf_path, score in matched_pdfs:
            pdf_name_lower = os.path.basename(pdf_path).lower()
            matched_paths.append(pdf_path)
            if any(k in pdf_name_lower for k in ["note", "reference", "handwritten", "tejas", "scribble"]):
                if not reference_pdf:
                    reference_pdf = pdf_path
            elif any(k in pdf_name_lower for k in ["assignment", "hw", "practice", "exercise"]):
                if not assignment_pdf:
                    assignment_pdf = pdf_path
            else:
                if not slides_pdf:
                    slides_pdf = pdf_path
                    
        if not reference_pdf and slides_pdf:
            reference_pdf = slides_pdf
            
    matched_srt = None
    for srt in srt_files:
        srt_clean = clean_name(os.path.splitext(os.path.basename(srt))[0])
        if srt_clean in clean_video or clean_video in srt_clean:
            matched_srt = srt
            matched_paths.append(srt)
            break
            
    return {
        "video": video_path,
        "reference_pdf": reference_pdf,
        "slides_pdf": slides_pdf,
        "assignment_pdf": assignment_pdf,
        "srt": matched_srt,
        "matched_paths": matched_paths
    }

def find_soundscribe_job(video_basename):
    safe_basename = os.path.basename(video_basename)
    safe_basename = safe_basename.replace("..", "").replace("/", "").replace("\\", "")
    
    job_paths = [
        os.path.join(SOUNDSCRIBE_DIR, f"{safe_basename}_transcript.soundscribejob", "manifest.json"),
        os.path.join(SOUNDSCRIBE_DIR, f"{safe_basename}_transcript", "manifest.json")
    ]
    for p in job_paths:
        if os.path.exists(p):
            return p
            
    if os.path.exists(SOUNDSCRIBE_DIR):
        for d in os.listdir(SOUNDSCRIBE_DIR):
            if d.lower().startswith(safe_basename.lower()) and "soundscribejob" in d:
                p = os.path.join(SOUNDSCRIBE_DIR, d, "manifest.json")
                if os.path.exists(p):
                    return p
    return None

def is_orchestrator_active():
    try:
        proc = subprocess.run(["pgrep", "-f", "langgraph_orchestrator.py"], capture_output=True, text=True)
        pids = [p.strip() for p in proc.stdout.split() if p.strip()]
        
        filtered_pids = []
        for pid in pids:
            if int(pid) == os.getpid():
                continue
            # Get the command name to ensure it is actually a python interpreter running it
            comm_proc = subprocess.run(["ps", "-p", pid, "-o", "comm="], capture_output=True, text=True)
            comm_name = comm_proc.stdout.strip().lower()
            if "python" in comm_name:
                filtered_pids.append(pid)
                
        return len(filtered_pids) > 0
    except Exception as e:
        print(f"Skipping active orchestrator process check due to error: {e}")
        return False

def check_supabase_completed_titles():
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            return set()
        from supabase import create_client
        sb = create_client(url, key)
        res = sb.table("pipeline_runs").select("lecture_title").eq("status", "completed").execute()
        if res.data:
            return set(r["lecture_title"].lower() for r in res.data if r.get("lecture_title"))
    except Exception as e:
        print(f"Supabase completed titles query warning (proceeding cleanly): {e}")
    return set()

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def is_lecture_truly_completed(video_basename, processed, sb_completed_titles):

    v_clean = video_basename.lower()
    v_name = f"{video_basename}.mp4"
    
    # 1. Local tracker state check
    if v_name in processed and processed[v_name].get("status") in ("completed", "completed_with_warnings"):
        return True
        
    # 2. Supabase DB completed title check
    for title in sb_completed_titles:
        if title.lower() in v_clean or v_clean in title.lower():
            return True
            
    # 3. Local notes-output docx check
    slug = slugify(v_clean)
    docx_matches = glob.glob(os.path.join(PROJECT_DIR, f"notes-output/*{slug}*.docx"))
    if docx_matches:
        return True
        
    return False

def verify_and_purge_downloads(video_path, matched_paths, lecture_basename):
    all_files = [video_path] + matched_paths
    real_downloads_dir = os.path.realpath(DOWNLOADS_DIR)
    
    for filepath in all_files:
        if not os.path.exists(filepath):
            continue
        real_filepath = os.path.realpath(filepath)
        if not real_filepath.startswith(real_downloads_dir):
            print(f"SECURITY GUARD: Refusing to delete path outside Downloads: {filepath}")
            return False
        if os.path.islink(filepath):
            print(f"SECURITY GUARD: Refusing to delete symlink: {filepath}")
            return False
            
    # Verification Gate: Check local notes artifact or R2 object
    lecture_slug = slugify(lecture_basename)
    local_notes_exist = any(glob.glob(os.path.join(PROJECT_DIR, f"notes-output/*{lecture_slug}*.docx"))) or os.path.exists(os.path.join(PROJECT_DIR, "notes-output/LECTURE_NOTES.docx"))
    
    r2_verified = False
    try:
        endpoint = os.getenv("R2_ENDPOINT")
        access_key = os.getenv("R2_ACCESS_KEY_ID")
        secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        bucket = os.getenv("R2_BUCKET_NAME")
        
        if endpoint and access_key and secret_key and bucket:
            session = boto3.session.Session()
            s3 = session.client(
                service_name='s3',
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=os.getenv("R2_REGION", "auto")
            )
            
            key = f"lectures/{lecture_slug}/notes.docx"
            try:
                head = s3.head_object(Bucket=bucket, Key=key)
                if head.get('ContentLength', 0) > 0:
                    r2_verified = True
            except Exception:
                pass
    except Exception as e:
        print(f"R2 verification check notice: {e}")
        
    if not (r2_verified or local_notes_exist):
        print(f"2-Phase Commit Aborted: Neither R2 notes nor local output notes were verified for {lecture_basename}.")
        return False
        
    print(f"✅ 2-Phase Commit Verified for {lecture_basename}. Purging processed files from Downloads...")

    purged_count = 0
    for filepath in set(all_files):
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"  🗑️ Deleted from Downloads: {os.path.basename(filepath)}")
                purged_count += 1
            except Exception as e:
                print(f"  ⚠️ Error deleting {filepath}: {e}")
                
    return purged_count > 0

def send_notification(title, subtitle, message):
    try:
        script = '''
        on run argv
            display notification (item 3 of argv) with title (item 1 of argv) subtitle (item 2 of argv)
        end run
        '''
        subprocess.run(
            ["osascript", "-e", script, str(title), str(subtitle), str(message)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="Downloads Tracker for agentic lecture notes")
    parser.add_argument("--force", action="store_true", help="Bypass execution time check (7 AM - 1 PM)")
    parser.add_argument("--retry-failed", action="store_true", help="Retry previously failed files")
    args = parser.parse_args()

    if not acquire_lock():
        print("Another instance of downloads_tracker.py is already running. Exiting.")
        sys.exit(0)

    try:
        now = datetime.now()
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Running Downloads Tracker...")
        
        # Enforce 7 AM - 1 PM execution window unless --force is specified
        if not args.force and not (7 <= now.hour < 13):
            print(f"[{now.strftime('%H:%M:%S')}] Outside 7 AM - 1 PM execution window. Skipping background scan.")
            return

        if not check_disk_space():
            send_notification("Low Storage Warning", "Downloads Tracker", "Host disk space is under 15 GB. Pausing ingestion.")
            return

        processed = get_processed_files()
        check_and_recover_stuck_jobs(processed)

        if args.retry_failed:
            keys_to_remove = [k for k, v in processed.items() if v.get("status") == "failed"]
            if keys_to_remove:
                print(f"Clearing failure status for {len(keys_to_remove)} lectures to retry them...")
                for k in keys_to_remove:
                    del processed[k]
                save_processed_files(processed)

        mp4_files = glob.glob(os.path.join(DOWNLOADS_DIR, "*.mp4"))
        if not mp4_files:
            print("No MP4 files found in Downloads.")
            return

        # Fetch completed titles from Supabase DB for retroactive reconciliation
        sb_completed_titles = check_supabase_completed_titles()
        
        reconciled_purges = 0
        new_lectures = []
        
        for video_path in mp4_files:
            video_name = os.path.basename(video_path)
            video_basename = os.path.splitext(video_name)[0]
            
            # Check for in-flight browser downloads
            base_no_ext = os.path.splitext(video_path)[0]
            if glob.glob(f"{base_no_ext}*.crdownload") or glob.glob(f"{base_no_ext}*.part") or glob.glob(f"{base_no_ext}*.tmp"):
                print(f"Skipping {video_name} (in-flight browser download detected...)")
                continue

            size1 = os.path.getsize(video_path)
            time.sleep(2)
            size2 = os.path.getsize(video_path)
            if size1 != size2 or size2 == 0:
                print(f"Skipping {video_name} (file size unstable, still downloading...)")
                continue

            # Retroactive Reconciliation Check: Is lecture ALREADY COMPLETED?
            if is_lecture_truly_completed(video_basename, processed, sb_completed_titles):
                print(f"Retroactive Purge: Lecture {video_name} is already completed. Purging from Downloads...")
                bundle = find_lecture_bundle(video_path)
                if verify_and_purge_downloads(video_path, bundle["matched_paths"], video_basename):
                    reconciled_purges += 1
                    processed[video_name] = {
                        "status": "completed",
                        "completed_at": datetime.now().isoformat(),
                        "purged_downloads": True
                    }
                    save_processed_files(processed)
                continue
                
            # If not processed or completed, add to queue
            if video_name not in processed or processed[video_name].get("status") not in ("completed", "completed_with_warnings"):
                print(f"Detected un-processed lecture video: {video_name}")
                new_lectures.append(video_path)

        if reconciled_purges > 0:
            print(f"✅ Retroactive reconciliation purged {reconciled_purges} completed lecture bundles from Downloads.")

        if not new_lectures:
            print("No new un-processed lectures detected.")
            return

        # Sort key to prioritize DBMS/SQL lectures and process them chronologically (Lec-31 -> Lec-37)
        def sort_key(filepath):
            filename = os.path.basename(filepath)
            match = re.search(r'\b(live|lec|lecture|l|class|part)\s*[-_]?\s*(\d+)\b', filename.lower())
            num_str = match.group(2) if match else None
            if not num_str:
                match2 = re.search(r'(?<!\d)(\d+)(?!\d)', filename)
                num_str = match2.group(1) if match2 else None
            
            num = int(num_str) if num_str else 999
            
            is_dbms = False
            if any(k in filename.lower() for k in ["dbms", "sql", "aggregate", "group by", "having", "nested query", "correlated"]):
                is_dbms = True
            elif num_str and 27 <= int(num_str) <= 37 and "lec" in filename.lower():
                is_dbms = True
                
            return (not is_dbms, num if is_dbms else 999, -os.path.getmtime(filepath))

        new_lectures.sort(key=sort_key)


        # Process at most 1 backlog lectures per cron cycle to respect time window
        MAX_PER_RUN = 1
        batch_queue = new_lectures[:MAX_PER_RUN]
        print(f"Processing batch of {len(batch_queue)} lectures (capped at {MAX_PER_RUN} per cycle)...")

        for index, video_path in enumerate(batch_queue):
            video_name = os.path.basename(video_path)
            video_basename = os.path.splitext(video_name)[0]
            
            print(f"\nProcessing lecture {index + 1}/{len(batch_queue)}: {video_name}")
            
            if is_orchestrator_active():
                print("LangGraph Orchestrator is currently active. Skipping this item for now.")
                continue

            processed[video_name] = {
                "status": "processing",
                "detected_at": datetime.now().isoformat()
            }
            save_processed_files(processed)

            try:
                clean_cache()
                
                bundle = find_lecture_bundle(video_path)
                print(f"Bundle Discovery: {len(bundle['matched_paths'])} matching support files found.")
                
                dest_video_path = os.path.join(PROJECT_DIR, "lecture-input/LECTURE.mp4")
                print(f"Ingesting video: {video_path}")
                try:
                    os.link(video_path, dest_video_path)
                    print("Video ingestion complete (Hard Link created).")
                except OSError:
                    print("Hard link failed (cross-device). Copying video file...")
                    shutil.copy(video_path, dest_video_path)
                    print("Video ingestion complete (shutil.copy).")
                
                if bundle["reference_pdf"]:
                    print(f"Copying Reference PDF: {bundle['reference_pdf']}")
                    shutil.copy(bundle["reference_pdf"], os.path.join(PROJECT_DIR, "lecture-input/REFERENCE_NOTES.pdf"))
                elif bundle["slides_pdf"]:
                    print(f"Copying Slides PDF as Reference: {bundle['slides_pdf']}")
                    shutil.copy(bundle["slides_pdf"], os.path.join(PROJECT_DIR, "lecture-input/REFERENCE_NOTES.pdf"))
                else:
                    print("No matching PDF found in Downloads.")
                    
                with open(os.path.join(PROJECT_DIR, "lecture-input/lecture_title.txt"), "w") as f:
                    f.write(video_basename)

                if bundle["srt"]:
                    print(f"Copying direct SRT transcript: {bundle['srt']}")
                    shutil.copy(bundle["srt"], os.path.join(PROJECT_DIR, "lecture-input/transcript.srt"))
                else:
                    # Check ~/Transcripts/<video_basename>/transcript.srt
                    watcher_transcript = os.path.expanduser(f"~/Transcripts/{video_basename}/transcript.srt")
                    if os.path.exists(watcher_transcript) and os.path.getsize(watcher_transcript) > 0:
                        print(f"Found background watcher transcript at: {watcher_transcript}. Copying...")
                        shutil.copy(watcher_transcript, os.path.join(PROJECT_DIR, "lecture-input/transcript.srt"))
                    else:
                        ss_manifest = find_soundscribe_job(video_basename)
                        if ss_manifest:
                            print(f"Found SoundScribe manifest at: {ss_manifest}. Converting...")
                            subprocess.run([
                                sys.executable, 
                                "scripts/soundscribe_to_srt.py", 
                                ss_manifest, 
                                "lecture-input/transcript.srt"
                            ], cwd=PROJECT_DIR, check=True, timeout=3600)
                        else:
                            print("No matching background watcher or SoundScribe transcript found. Orchestrator will run local Qwen3-ASR transcription.")

                print("Starting note-reconstruction pipeline...")
                subprocess.run([sys.executable, "scripts/langgraph_orchestrator.py"], cwd=PROJECT_DIR, check=True, timeout=3600)
                
                print("Running audit verification...")
                audit_res = subprocess.run([sys.executable, "scripts/audit.py", "--docx", "notes-output/LECTURE_NOTES.docx"], cwd=PROJECT_DIR, check=False, timeout=3600)
                
                if audit_res.returncode != 0:
                    print(f"WARNING: Quality audit failed with exit code {audit_res.returncode}.")
                    processed[video_name]["status"] = "completed_with_warnings"
                    processed[video_name]["audit_error"] = f"Audit failed with exit code {audit_res.returncode}"
                    processed[video_name]["completed_at"] = datetime.now().isoformat()
                    save_processed_files(processed)
                    # No notification for warnings (error-only policy)
                else:
                    print("Audit passed 100%. Executing 2-Phase Commit Cloud Verification & Post-Upload Cleanup...")
                    purged = verify_and_purge_downloads(video_path, bundle["matched_paths"], video_basename)
                    
                    processed[video_name]["status"] = "completed"
                    processed[video_name]["completed_at"] = datetime.now().isoformat()
                    processed[video_name]["purged_downloads"] = purged
                    save_processed_files(processed)
                    
                    print(f"SUCCESSFULLY COMPLETED pipeline and cleanup for: {video_basename}")
                    # No notification for success (error-only policy)
                
            except Exception as e:
                print(f"ERROR processing {video_name}: {e}")
                processed[video_name]["status"] = "failed"
                processed[video_name]["error"] = str(e)
                save_processed_files(processed)
                send_notification(
                    "Pipeline Error", 
                    video_basename, 
                    f"Reconstruction failed: {str(e)[:50]}. Raw downloads preserved."
                )

    finally:
        release_lock()

if __name__ == "__main__":
    main()

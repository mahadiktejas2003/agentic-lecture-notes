#!/usr/bin/env python3
"""
soundscribe_fallback.py
=======================
Fallback transcription engine using the SoundScribe Agent CLI.

SoundScribe exposes a local file-based automation interface (workspace pattern):
  inbox/   – agent reads JSON job manifests placed here
  jobs/    – agent writes status JSON files here
  outputs/ – transcript files land here (via status.outputs)
  logs/    – persistent log lines

This module:
  1. Copies the audio/video file into the SoundScribe workspace tmp/ folder.
  2. Submits a transcribe_file job via the soundscribe-agent.mjs CLI.
  3. Polls the jobs/<id>.status.json file until the job reaches
     "completed", "failed", or "cancelled" (up to `timeout` seconds).
  4. Reads the output TXT/SRT files and writes them to `output_dir`.
  5. Returns the path to the saved transcript.srt on success.

Prerequisites:
  - SoundScribe.app must be running with Agent Mode enabled.
  - SOUNDSCRIBE_AGENT_WORKSPACE env var points to the workspace folder.
  - Node.js must be available on PATH.

Usage (standalone):
  python scripts/soundscribe_fallback.py \
    --input lecture-input/LECTURE.mp4 \
    --output-dir lecture-input \
    [--language auto] [--timeout 3600]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

# ─── Constants ────────────────────────────────────────────────────────────────

_SS_WORKSPACE = os.environ.get(
    "SOUNDSCRIBE_AGENT_WORKSPACE",
    "/Users/tejasmahadik/Downloads/Transcription-SoundScribe",
)

_SS_CLI = (
    "/Users/tejasmahadik/Library/Containers/"
    "com.francis.masterplan.Qwen3-ASR-Mac/Data/Library/Application Support/"
    "SoundScribe/AgentTools/soundscribe-agent.mjs"
)

_POLL_INTERVAL = 3   # seconds between status polls
_DEFAULT_TIMEOUT = 3600  # 1 hour

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _run_cli(*args: str, timeout_secs: int = 30) -> dict:
    """Run soundscribe-agent.mjs with the given arguments.

    Returns the parsed JSON dict from stdout.
    Raises RuntimeError on non-zero exit or JSON decode failure.
    """
    env = os.environ.copy()
    env["SOUNDSCRIBE_AGENT_WORKSPACE"] = _SS_WORKSPACE

    cmd = ["node", _SS_CLI, *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout_secs,
    )
    raw = result.stdout.strip()
    if not raw:
        raise RuntimeError(
            f"soundscribe-agent returned no output. stderr: {result.stderr.strip()}"
        )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"soundscribe-agent output is not valid JSON: {raw!r}"
        ) from exc


def _read_status(job_id: str) -> dict | None:
    """Read the job status JSON written by SoundScribe into jobs/<id>.status.json."""
    status_path = os.path.join(_SS_WORKSPACE, "jobs", f"{job_id}.status.json")
    if not os.path.exists(status_path):
        return None
    try:
        with open(status_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _wait_for_job(job_id: str, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """Poll the workspace jobs directory until the job reaches a terminal state.

    Returns the final status dict.
    Raises TimeoutError if `timeout` seconds elapse without completion.
    """
    deadline = time.time() + timeout
    dots = 0
    while time.time() < deadline:
        status = _read_status(job_id)
        if status:
            state = status.get("state", "")
            if state in ("completed", "failed", "cancelled"):
                return status
            pct = status.get("progress_pct", "")
            dot_str = "." * (dots % 4)
            pct_str = f" {pct}%" if pct else ""
            print(
                f"  [SoundScribe] Job {job_id[:8]}… state={state}{pct_str}{dot_str}",
                flush=True,
            )
        else:
            print(f"  [SoundScribe] Waiting for job {job_id[:8]} to appear…", flush=True)

        dots += 1
        time.sleep(_POLL_INTERVAL)

    raise TimeoutError(
        f"SoundScribe job {job_id} did not complete within {timeout} seconds."
    )


def _build_srt_from_txt(txt_content: str, duration_hint: float = 0.0) -> str:
    """
    Build a minimal SRT string from plain transcript text when no SRT output
    is available. Splits on sentence boundaries, distributing timestamps evenly.
    """
    # Split into rough sentences
    sentences = re.split(r"(?<=[।.!?])\s+", txt_content.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return ""

    total = duration_hint if duration_hint > 0 else len(sentences) * 4.0
    seg_duration = total / len(sentences)

    def fmt(secs: float) -> str:
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        s = int(secs % 60)
        ms = int(round((secs - int(secs)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for idx, sentence in enumerate(sentences, 1):
        start = (idx - 1) * seg_duration
        end = idx * seg_duration
        lines.append(f"{idx}")
        lines.append(f"{fmt(start)} --> {fmt(end)}")
        lines.append(sentence)
        lines.append("")
    return "\n".join(lines)


def _get_media_duration(path: str) -> float:
    """Return media duration in seconds via ffprobe, or 0.0 on failure."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ]
        r = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


# ─── Public API ───────────────────────────────────────────────────────────────


def transcribe_via_soundscribe(
    input_path: str,
    output_dir: str,
    language: str = "auto",
    timeout: int = _DEFAULT_TIMEOUT,
) -> tuple[str, str]:
    """
    Transcribe an audio/video file using the SoundScribe app (fallback path).

    Parameters
    ----------
    input_path : str
        Absolute or relative path to the audio/video file.
    output_dir : str
        Directory where transcript.txt and transcript.srt will be written.
    language : str
        Language hint for SoundScribe (e.g. "auto", "hi", "en").
        SoundScribe accepts "auto" as a valid value.
    timeout : int
        Maximum seconds to wait for the job to complete.

    Returns
    -------
    (txt_path, srt_path) : tuple[str, str]
        Paths to the written transcript.txt and transcript.srt files.

    Raises
    ------
    RuntimeError  – if transcription fails or outputs are not found.
    TimeoutError  – if the job does not finish within `timeout` seconds.
    """
    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path!r}")

    os.makedirs(output_dir, exist_ok=True)

    # Verify SoundScribe workspace is reachable
    print("[SoundScribe Fallback] Verifying agent workspace…", flush=True)
    doctor = _run_cli("doctor")
    if not doctor.get("ok"):
        raise RuntimeError(
            f"SoundScribe workspace check failed: {doctor.get('error', doctor)}"
        )
    print(f"  Workspace OK: {doctor.get('workspace')}", flush=True)

    # Map language codes that SoundScribe may not know
    ss_language = language
    if language in ("hi", "Hindi"):
        ss_language = "hi"
    elif language in ("en", "English"):
        ss_language = "en"
    elif language is None:
        ss_language = "auto"

    print(
        f"[SoundScribe Fallback] Submitting job for '{os.path.basename(input_path)}' "
        f"(language={ss_language})…",
        flush=True,
    )

    # Submit the job (no --wait; we poll manually for better progress output)
    submit_result = _run_cli(
        "transcribe",
        input_path,
        "--language", ss_language,
        "--srt",          # ask for SRT output too
    )
    job_id = submit_result.get("job_id")
    if not job_id:
        raise RuntimeError(
            f"SoundScribe did not return a job_id. Response: {submit_result}"
        )
    print(f"  Job submitted: {job_id}", flush=True)

    # Poll until completion
    print(f"[SoundScribe Fallback] Waiting for job to finish (timeout={timeout}s)…", flush=True)
    final_status = _wait_for_job(job_id, timeout=timeout)

    if final_status.get("state") != "completed":
        err = final_status.get("error") or final_status.get("message") or str(final_status)
        raise RuntimeError(f"SoundScribe job ended in state '{final_status.get('state')}': {err}")

    print("[SoundScribe Fallback] Job completed successfully!", flush=True)

    # Retrieve output files from status
    outputs = final_status.get("outputs", {})
    print(f"  Outputs reported: {list(outputs.keys())}", flush=True)

    txt_src = outputs.get("txt") or outputs.get("text")
    srt_src = outputs.get("srt")

    # Paths are relative to the workspace
    def resolve_output(rel: str) -> str | None:
        if not rel:
            return None
        if os.path.isabs(rel):
            return rel if os.path.exists(rel) else None
        abs_path = os.path.join(_SS_WORKSPACE, rel)
        return abs_path if os.path.exists(abs_path) else None

    txt_abs = resolve_output(txt_src)
    srt_abs = resolve_output(srt_src)

    # Fallback: scan outputs/ directory for this job_id prefix
    if not txt_abs:
        outputs_dir = os.path.join(_SS_WORKSPACE, "outputs")
        for fname in sorted(os.listdir(outputs_dir)):
            if fname.startswith(job_id[:8]) or job_id[:8] in fname:
                full = os.path.join(outputs_dir, fname)
                if fname.endswith(".txt") and not txt_abs:
                    txt_abs = full
                elif fname.endswith(".srt") and not srt_abs:
                    srt_abs = full

    if not txt_abs:
        raise RuntimeError(
            f"SoundScribe completed job {job_id} but transcript TXT was not found. "
            f"Outputs dict: {outputs}"
        )

    # Copy TXT
    final_txt = os.path.join(output_dir, "transcript.txt")
    shutil.copy2(txt_abs, final_txt)
    print(f"  Saved TXT: {final_txt}", flush=True)

    # Copy or generate SRT
    final_srt = os.path.join(output_dir, "transcript.srt")
    if srt_abs:
        shutil.copy2(srt_abs, final_srt)
        print(f"  Saved SRT: {final_srt}", flush=True)
    else:
        # SoundScribe did not produce SRT – synthesise one from TXT
        print("  [SoundScribe Fallback] SRT not produced; synthesising from TXT…", flush=True)
        with open(txt_abs, "r", encoding="utf-8") as f:
            txt_content = f.read()
        duration = _get_media_duration(input_path)
        srt_content = _build_srt_from_txt(txt_content, duration_hint=duration)
        with open(final_srt, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"  Saved synthesised SRT: {final_srt}", flush=True)

    return final_txt, final_srt


# ─── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SoundScribe fallback transcription (uses local SoundScribe.app via Agent CLI)"
    )
    parser.add_argument("--input", required=True, help="Path to input audio/video file")
    parser.add_argument("--output-dir", default="lecture-input", help="Output directory")
    parser.add_argument("--language", default="auto", help="Language code or 'auto'")
    parser.add_argument("--timeout", type=int, default=_DEFAULT_TIMEOUT,
                        help="Timeout in seconds (default 3600)")
    args = parser.parse_args()

    try:
        txt, srt = transcribe_via_soundscribe(
            input_path=args.input,
            output_dir=args.output_dir,
            language=args.language,
            timeout=args.timeout,
        )
        print(f"\nSuccess!\n  TXT: {txt}\n  SRT: {srt}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

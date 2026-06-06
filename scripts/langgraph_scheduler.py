#!/usr/bin/env python3
import os
import sys
import time
import json
import datetime
import schedule
import subprocess
import threading

LOG_FILE = "logs/pipeline_runs.jsonl"

def verify_files():
    required_files = [
        "AGENTS.md",
        ".agents/skills/frame-extraction/SKILL.md",
        ".agents/skills/transcript-mapping/SKILL.md",
        ".agents/skills/slide-parsing/SKILL.md",
        ".agents/skills/note-composition/SKILL.md"
    ]
    for f in required_files:
        if not os.path.exists(f) or not os.access(f, os.R_OK):
            print(f"Error: Required file '{f}' is missing or unreadable.", file=sys.stderr)
            return False
    return True

def log_run(status, failed_gates=None, notes_path="notes-output/LECTURE_NOTES.docx"):
    if failed_gates is None:
        failed_gates = []
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "status": status,
        "failed_gates": failed_gates,
        "notes_path": notes_path
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"Logged run status '{status}' to {LOG_FILE}")

def run_pipeline_task():
    print(f"\n[{datetime.datetime.now().isoformat()}] Scheduled Run Started.")
    
    if not verify_files():
        print("Scheduler Abort: Verification failed.", file=sys.stderr)
        log_run("aborted", ["Verification failed"], "")
        return
        
    # Start thread for heartbeat timeout (2 hours = 7200 seconds)
    heartbeat_active = threading.Event()
    
    def heartbeat_monitor():
        # Wait for 2 hours
        if not heartbeat_active.wait(timeout=7200):
            print(f"WARNING: Pipeline run starting at {datetime.datetime.now().isoformat()} has been running for over 2 hours!", file=sys.stderr)
            
    monitor_thread = threading.Thread(target=heartbeat_monitor, daemon=True)
    monitor_thread.start()
    
    try:
        # Run auto_ingest.sh to check Downloads and ingest new files first!
        print("Running scripts/auto_ingest.sh...")
        subprocess.run(["/bin/bash", "scripts/auto_ingest.sh"], check=True)
        
        # Then run orchestrator
        print("Running scripts/langgraph_orchestrator.py...")
        res = subprocess.run([sys.executable, "scripts/langgraph_orchestrator.py"], capture_output=True, text=True)
        
        # Deactivate heartbeat monitor
        heartbeat_active.set()
        
        if res.returncode == 0:
            print("Pipeline run completed successfully.")
            log_run("success", [], "notes-output/LECTURE_NOTES.docx")
        else:
            print(f"Pipeline run failed with exit code {res.returncode}.", file=sys.stderr)
            print(res.stderr, file=sys.stderr)
            log_run("failed", ["orchestrator failed"], "notes-output/LECTURE_NOTES.docx")
            
    except Exception as e:
        heartbeat_active.set()
        print(f"Exception encountered during pipeline run: {e}", file=sys.stderr)
        log_run("error", [str(e)], "")

def main():
    print("Starting LangGraph Scheduler Daemon...")
    print("Verification check on startup:")
    if not verify_files():
        print("Scheduler startup halted due to missing files.", file=sys.stderr)
        sys.exit(1)
    print("Verification check passed.")
    
    # Run once immediately on start for validation
    run_pipeline_task()
    
    # Schedule every 4 hours
    schedule.every(4).hours.do(run_pipeline_task)
    
    print("Scheduler daemon running. Press Ctrl+C to exit.")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nScheduler daemon stopped.")
            break

if __name__ == "__main__":
    main()

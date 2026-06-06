#!/usr/bin/env python3
import os
import sys
import json
import datetime
import hashlib

def get_transcript_hash():
    path = "lecture-input/transcript.srt"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    return "unknown"

def store_run(status, audit_score=15, failed_gates=None, docx_path="notes-output/LECTURE_NOTES.docx"):
    if failed_gates is None:
        failed_gates = []
        
    memory_dir = "agent_memory"
    os.makedirs(memory_dir, exist_ok=True)
    
    run_record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "transcript_hash": get_transcript_hash(),
        "status": status,
        "audit_score": audit_score,
        "failed_gates": failed_gates,
        "notes_path": docx_path
    }
    
    record_file = os.path.join(memory_dir, f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(run_record, f, indent=2)
        
    print(f"Memory run record stored successfully at: {record_file}")
    
    # Log failures separately if any gates failed (Phase 5 Task 18.a)
    if failed_gates:
        failures_dir = os.path.join(memory_dir, "failures")
        os.makedirs(failures_dir, exist_ok=True)
        failure_file = os.path.join(failures_dir, f"fail_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(failure_file, "w", encoding="utf-8") as f:
            json.dump(run_record, f, indent=2)
        print(f"Failure record logged at: {failure_file}")

if __name__ == "__main__":
    status = sys.argv[1] if len(sys.argv) > 1 else "success"
    score = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    failed_gates_arg = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else []
    store_run(status, score, failed_gates_arg)

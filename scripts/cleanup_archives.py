#!/usr/bin/env python3
import os
import re
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def cleanup_notes_output(directory="notes-output"):
    if not os.path.exists(directory):
        return
        
    # Group timestamped files by their lecture title prefix
    # Pattern: LECTURE_NOTES_{title}_{timestamp}.docx
    # timestamp format: YYYY-MM-DD_HH-MM-SS
    pattern = re.compile(r'^LECTURE_NOTES_(.*)_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.docx$')
    
    groups = {}
    for f in os.listdir(directory):
        path = os.path.join(directory, f)
        if os.path.isfile(path):
            match = pattern.match(f)
            if match:
                title = match.group(1)
                mtime = os.path.getmtime(path)
                if title not in groups:
                    groups[title] = []
                groups[title].append((path, mtime, f))
                
    for title, files in groups.items():
        # Sort files by modification time descending (most recent first)
        files.sort(key=lambda x: x[1], reverse=True)
        
        # Keep the most recent file (the single final one)
        # Delete all other files
        to_delete = files[1:]
        for path, mtime, f in to_delete:
            try:
                os.remove(path)
                logging.info(f"Deleted stale/redundant draft archive: {f}")
            except Exception as e:
                logging.error(f"Failed to delete stale archive {path}: {e}")

def cleanup_directory(directory, pattern_func, max_age_days=14, keep_recent=5):
    if not os.path.exists(directory):
        return
    
    files = []
    for f in os.listdir(directory):
        path = os.path.join(directory, f)
        if os.path.isfile(path) and pattern_func(f):
            files.append((path, os.path.getmtime(path)))
            
    # Sort files by modification time descending (most recent first)
    files.sort(key=lambda x: x[1], reverse=True)
    
    now = time.time()
    seconds_limit = max_age_days * 24 * 3600
    
    # We only consider files for deletion if they are beyond the keep_recent count
    files_to_check = files[keep_recent:]
    
    for path, mtime in files_to_check:
        age_seconds = now - mtime
        if age_seconds > seconds_limit:
            try:
                os.remove(path)
                logging.info(f"Cleaned up old backup: {path} (age: {age_seconds / (24 * 3600):.1f} days)")
            except Exception as e:
                logging.error(f"Failed to delete {path}: {e}")

def main():
    # 1. Clean notes-output redundant archive files
    logging.info("Cleaning up notes-output redundant archive files...")
    cleanup_notes_output("notes-output")
    
    # 2. Clean lecture-input backups
    logging.info("Cleaning up lecture-input backups...")
    cleanup_directory(
        directory="lecture-input/backups",
        pattern_func=lambda f: (f.startswith("LECTURE_backup_") or f.startswith("transcript_backup_") or f.startswith("SLIDES_backup_")),
        max_age_days=14,
        keep_recent=5
    )

if __name__ == "__main__":
    main()

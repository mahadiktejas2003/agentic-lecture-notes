import os
import sys
import json
import time
import shutil
import glob
import subprocess
from datetime import datetime

DOWNLOADS_DIR = "/Users/tejasmahadik/Downloads"
SOUNDSCRIBE_DIR = "/Users/tejasmahadik/SoundScribe"
PROCESSED_FILE = "/Users/tejasmahadik/Documents/agentic-lecture-notes/logs/tracker_processed.json"
PROJECT_DIR = "/Users/tejasmahadik/Documents/agentic-lecture-notes"

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
    with open(PROCESSED_FILE, "w") as f:
        json.dump(processed, f, indent=2)

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
        "reference_screenshots"
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

def find_pdf_for_lecture(video_basename):
    # Try fuzzy matching pdf in Downloads
    # video_basename: e.g. "Live-12 Reasoning Syllogism Part-3 -1"
    # Find any pdf file in Downloads
    pdf_files = glob.glob(os.path.join(DOWNLOADS_DIR, "*.pdf"))
    if not pdf_files:
        return None
        
    # Standard clean name comparison
    clean_video = video_basename.lower().replace("-", " ").replace("_", " ")
    
    # Try exact match first
    for pdf in pdf_files:
        pdf_name = os.path.basename(pdf).lower().replace("-", " ").replace("_", " ")
        if pdf_name.replace(".pdf", "") in clean_video:
            return pdf
            
    # Try prefix/partial matches
    # e.g., if clean_video starts with "live 12", look for a pdf containing "live 12" or "syllogism"
    words = [w for w in clean_video.split() if len(w) > 3 and w not in ["reasoning", "aptitude", "part", "lecture"]]
    for pdf in pdf_files:
        pdf_name = os.path.basename(pdf).lower().replace("-", " ").replace("_", " ")
        for word in words:
            if word in pdf_name:
                return pdf
                
    return None

def find_soundscribe_job(video_basename):
    # Try to find matching job in SoundScribe
    # e.g. SOUNDSCRIBE_DIR / "{video_basename}_transcript.soundscribejob/manifest.json"
    job_paths = [
        os.path.join(SOUNDSCRIBE_DIR, f"{video_basename}_transcript.soundscribejob", "manifest.json"),
        os.path.join(SOUNDSCRIBE_DIR, f"{video_basename}_transcript", "manifest.json")
    ]
    for p in job_paths:
        if os.path.exists(p):
            return p
            
    # Fuzzy matching folders
    for d in os.listdir(SOUNDSCRIBE_DIR):
        if d.lower().startswith(video_basename.lower()) and "soundscribejob" in d:
            p = os.path.join(SOUNDSCRIBE_DIR, d, "manifest.json")
            if os.path.exists(p):
                return p
    return None

def main():
    now = datetime.now()
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Running Downloads Tracker...")
    
    # Restrict execution time between 7 AM to 1 PM (hours 7 to 13)
    if not (7 <= now.hour < 13):
        print("Outside tracking hours (7 AM to 1 PM). Skipping.")
        return

    # Prevent concurrent execution collision with active orchestrator
    try:
        proc = subprocess.run(["pgrep", "-f", "langgraph_orchestrator.py"], capture_output=True, text=True)
        pids = [p.strip() for p in proc.stdout.split() if p.strip()]
        if pids:
            print("LangGraph Orchestrator is currently active. Skipping tracking loop to avoid collision.")
            return
    except Exception as lock_err:
        print(f"Skipping lock check due to error: {lock_err}")


    # Check for MP4 files in Downloads
    mp4_files = glob.glob(os.path.join(DOWNLOADS_DIR, "*.mp4"))
    if not mp4_files:
        print("No MP4 files found in Downloads.")
        return

    processed = get_processed_files()
    new_lectures = []

    for video_path in mp4_files:
        video_name = os.path.basename(video_path)
        
        # Check if already processed or processing
        if video_name in processed:
            continue
            
        # Verify file size is stable (not currently downloading)
        size1 = os.path.getsize(video_path)
        time.sleep(2)
        size2 = os.path.getsize(video_path)
        if size1 != size2 or size2 == 0:
            print(f"Skipping {video_name} (still downloading...)")
            continue
            
        print(f"Detected new lecture video: {video_name}")
        new_lectures.append(video_path)

    if not new_lectures:
        print("No new complete lectures detected.")
        return

    # Process the first new lecture found
    video_path = new_lectures[0]
    video_name = os.path.basename(video_path)
    video_basename = os.path.splitext(video_name)[0]
    
    # Save status
    processed[video_name] = {
        "status": "processing",
        "detected_at": datetime.now().isoformat()
    }
    save_processed_files(processed)

    try:
        clean_cache()
        
        # Copy video
        print(f"Copying video: {video_path}")
        shutil.copy(video_path, os.path.join(PROJECT_DIR, "lecture-input/LECTURE.mp4"))
        
        # Find and copy PDF
        pdf_path = find_pdf_for_lecture(video_basename)
        if pdf_path:
            print(f"Found and copying matching PDF: {pdf_path}")
            shutil.copy(pdf_path, os.path.join(PROJECT_DIR, "lecture-input/REFERENCE_NOTES.pdf"))
        else:
            print("No matching PDF found in Downloads.")
            
        # Write title
        with open(os.path.join(PROJECT_DIR, "lecture-input/lecture_title.txt"), "w") as f:
            f.write(video_basename)

        # Convert SoundScribe or let the orchestrator do local transcription
        ss_manifest = find_soundscribe_job(video_basename)
        if ss_manifest:
            print(f"Found SoundScribe manifest at: {ss_manifest}. Converting...")
            subprocess.run([
                "venv/bin/python", 
                "scripts/soundscribe_to_srt.py", 
                ss_manifest, 
                "lecture-input/transcript.srt"
            ], cwd=PROJECT_DIR, check=True)
        else:
            print("No matching SoundScribe transcript found. Orchestrator will run local Qwen3-ASR transcription.")

        # Run pipeline
        print("Starting note-reconstruction pipeline...")
        subprocess.run(["venv/bin/python", "scripts/langgraph_orchestrator.py"], cwd=PROJECT_DIR, check=True)
        
        # Run audit check
        subprocess.run(["venv/bin/python", "scripts/audit.py", "--docx", "notes-output/LECTURE_NOTES.docx"], cwd=PROJECT_DIR, check=False)
        
        # Mark as completed
        processed[video_name]["status"] = "completed"
        processed[video_name]["completed_at"] = datetime.now().isoformat()
        save_processed_files(processed)
        print(f"SUCCESSFULLY COMPLETED pipeline for: {video_basename}")
        
    except Exception as e:
        print(f"ERROR processing {video_name}: {e}")
        processed[video_name]["status"] = "failed"
        processed[video_name]["error"] = str(e)
        save_processed_files(processed)

if __name__ == "__main__":
    main()

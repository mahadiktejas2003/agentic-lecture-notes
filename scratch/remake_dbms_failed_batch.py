import os
import shutil
import subprocess
import sys
import time
import boto3
from dotenv import load_dotenv

PROJECT_DIR = "/Users/tejasmahadik/Documents/agentic-lecture-notes"
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

# Verify credentials
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "lecture-notes")
R2_REGION = os.getenv("R2_REGION", "auto")

if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
    print("Error: R2 credentials missing in .env")
    sys.exit(1)

s3 = boto3.client(
    service_name='s3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name=R2_REGION
)

lectures = [
    {
        "folder": "lec-9-one-to-many-relationship",
        "title": "Lec-9 One to Many Relationship",
        "has_slides": True
    },
    {
        "folder": "lec-10-many-to-many-relationship",
        "title": "Lec-10 Many to Many Relationship",
        "has_slides": True
    },
    {
        "folder": "lec-12-closure-method-1",
        "title": "Lec-12 Closure Method",
        "has_slides": False
    },
    {
        "folder": "lec-14-functional-dependency",
        "title": "Lec-14 Functional Dependency",
        "has_slides": False
    },
    {
        "folder": "lec-15-types-of-functional-dependency",
        "title": "Lec-15 Types of Functional Dependency",
        "has_slides": False
    }
]

def clean_input_dir():
    input_dir = os.path.join(PROJECT_DIR, "lecture-input")
    if os.path.exists(input_dir):
        shutil.rmtree(input_dir)
    os.makedirs(input_dir)

def clean_root_cache():
    for f in ["concept_block_map.json", "frame_manifest.json", "slide_manifest.json", "workspace_state.json"]:
        p = os.path.join(PROJECT_DIR, f)
        if os.path.exists(p):
            os.remove(p)

def download_file(r2_key, local_path):
    print(f"Downloading s3://{R2_BUCKET_NAME}/{r2_key} to {local_path}...")
    s3.download_file(R2_BUCKET_NAME, r2_key, local_path)

def process_lecture(lec):
    folder = lec["folder"]
    title = lec["title"]
    has_slides = lec["has_slides"]
    
    print(f"\n=======================================================")
    print(f"STARTING RECONSTRUCTION FOR: {title}")
    print(f"=======================================================")
    
    clean_input_dir()
    clean_root_cache()
    
    input_dir = os.path.join(PROJECT_DIR, "lecture-input")
    
    # Download sources
    try:
        download_file(f"lectures/{folder}/video.mp4", os.path.join(input_dir, "LECTURE.mp4"))
        download_file(f"lectures/{folder}/transcript.srt", os.path.join(input_dir, "transcript.srt"))
        if has_slides:
            download_file(f"lectures/{folder}/slides.pdf", os.path.join(input_dir, "SLIDES.pdf"))
            
        with open(os.path.join(input_dir, "lecture_title.txt"), "w", encoding="utf-8") as f:
            f.write(title)
            
    except Exception as e:
        print(f"Failed to download sources for {title}: {e}")
        return False

    # Run orchestrator
    print("Running orchestrator...")
    res = subprocess.run([
        "venv/bin/python", "scripts/langgraph_orchestrator.py"
    ], cwd=PROJECT_DIR, capture_output=True, text=True)
    
    print(f"Orchestrator exit code: {res.returncode}")
    if res.returncode != 0:
        print("Stdout:\n", res.stdout)
        print("Stderr:\n", res.stderr)
        return False
        
    # Copy generated notes to local archive
    archive_dir = os.path.join(PROJECT_DIR, "local-archive", folder)
    os.makedirs(archive_dir, exist_ok=True)
    
    notes_src = os.path.join(PROJECT_DIR, "notes-output", "LECTURE_NOTES.docx")
    notes_dest = os.path.join(archive_dir, "notes.docx")
    short_src = os.path.join(PROJECT_DIR, "notes-output", "LECTURE_SHORTNOTE.md")
    short_dest = os.path.join(archive_dir, "short-note.md")
    
    if os.path.exists(notes_src):
        shutil.copy2(notes_src, notes_dest)
        print(f"Archived notes.docx to {notes_dest}")
    if os.path.exists(short_src):
        shutil.copy2(short_src, short_dest)
        print(f"Archived short-note.md to {short_dest}")
        
    print(f"SUCCESSFULLY COMPLETED RECONSTRUCTION FOR: {title}\n")
    return True

def main():
    results = {}
    for lec in lectures:
        success = process_lecture(lec)
        results[lec["title"]] = "SUCCESS" if success else "FAILED"
        print("Waiting 15 seconds before processing the next lecture to respect API limits...")
        time.sleep(15)
        
    print("\n=======================================================")
    print("FAILED DBMS RECONSTRUCTION BATCH SUMMARY")
    print("=======================================================")
    for title, status in results.items():
        print(f"{title}: {status}")

if __name__ == "__main__":
    main()

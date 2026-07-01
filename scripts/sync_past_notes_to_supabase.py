#!/usr/bin/env python3
import os
import sys
import re
import boto3
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Set CWD to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
os.chdir(project_root)
sys.path.append(os.path.join(project_root, "scripts"))

from cloud_uploader import upload_to_r2, log_to_supabase

load_dotenv()

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def main():
    print("=== Syncing Past Local Notes to Supabase & R2 ===")
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not all([url, key]):
        print("Error: Supabase credentials missing")
        sys.exit(1)
        
    supabase: Client = create_client(url, key)
    
    # Check what lectures are already in Supabase to avoid duplicates
    try:
        res = supabase.table("pipeline_runs").select("lecture_title").execute()
        existing_titles = {run["lecture_title"].strip().lower() for run in res.data}
    except Exception as e:
        print(f"Error querying Supabase: {e}")
        sys.exit(1)
        
    notes_dir = "notes-output"
    if not os.path.exists(notes_dir):
        print(f"Error: {notes_dir} folder not found")
        sys.exit(1)
        
    files = os.listdir(notes_dir)
    pattern = r"LECTURE_NOTES_(.+)_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.docx"
    
    # 1. Gather all local runs
    local_runs = []
    for f in files:
        match = re.match(pattern, f)
        if match:
            raw_title = match.group(1)
            date_str = match.group(2)
            time_str = match.group(3)
            
            # Clean title
            title = raw_title.replace("_", " ").strip()
            
            # Parse datetime (local time is GMT+5:30)
            local_time_str = f"{date_str} {time_str.replace('-', ':')}"
            dt = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M:%S")
            iso_with_tz = f"{date_str}T{time_str.replace('-', ':')}+05:30"
            
            local_runs.append({
                "filename": f,
                "title": title,
                "created_at": iso_with_tz,
                "dt": dt,
                "filepath": os.path.join(notes_dir, f)
            })
            
    if not local_runs:
        print("No past generated notes found in notes-output.")
        sys.exit(0)
        
    # 2. Group by lecture title and keep only the latest run for each lecture
    grouped_runs = {}
    for run in local_runs:
        title_key = run["title"].lower()
        if title_key not in grouped_runs:
            grouped_runs[title_key] = run
        else:
            # Keep the latest run by datetime
            if run["dt"] > grouped_runs[title_key]["dt"]:
                grouped_runs[title_key] = run
                
    print(f"Found {len(grouped_runs)} unique lectures in local notes-output.")
    
    # 3. Filter out lectures that are already logged in Supabase
    runs_to_sync = []
    for title_key, run in grouped_runs.items():
        if run["title"].lower() in existing_titles:
            print(f"Skipping: '{run['title']}' is already registered in Supabase.")
        else:
            runs_to_sync.append(run)
            
    if not runs_to_sync:
        print("All local lectures are already registered in Supabase. Nothing to sync!")
        sys.exit(0)
        
    print(f"Syncing {len(runs_to_sync)} past lecture notes to R2 and Supabase...")
    
    # 4. Upload and log each run
    for run in runs_to_sync:
        lecture_title = run["title"]
        lecture_slug = slugify(lecture_title)
        notes_key = f"lectures/{lecture_slug}/notes.docx"
        
        print(f"\n--- Syncing: {lecture_title} ---")
        print(f"Local file: {run['filepath']}")
        print(f"R2 key: {notes_key}")
        
        # Upload notes file to R2
        r2_success = upload_to_r2(run["filepath"], notes_key)
        
        if r2_success:
            # Log to Supabase
            run_data = {
                "created_at": run["created_at"],
                "lecture_title": lecture_title,
                "status": "completed",
                "audit_score": 18,
                "r2_video_key": None,  # No video was uploaded for past runs
                "r2_notes_key": notes_key,
                "error_message": "Past run synced from local notes-output folder. Video was not uploaded."
            }
            try:
                # Direct supabase insert with custom created_at timestamp
                data = supabase.table("pipeline_runs").insert(run_data).execute()
                print(f"✅ Logged to Supabase: ID {data.data[0]['id']}")
            except Exception as e:
                print(f"❌ Supabase log failed: {e}")
        else:
            print(f"❌ Skipping Supabase log due to R2 upload failure.")
            
    print("\n=== Sync Process Completed ===")

if __name__ == "__main__":
    main()

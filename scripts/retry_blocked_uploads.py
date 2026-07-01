#!/usr/bin/env python3
import os
import sys
import boto3
from dotenv import load_dotenv
from supabase import create_client, Client
import re

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
    print("=== Retrying Blocked R2 Uploads (Retry Queue) ===")
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not all([url, key]):
        print("Error: Supabase credentials missing")
        sys.exit(1)
        
    supabase: Client = create_client(url, key)
    
    # Query all runs where status = 'limit_exceeded'
    try:
        res = supabase.table("pipeline_runs").select("*").eq("status", "limit_exceeded").execute()
        blocked_runs = res.data
    except Exception as e:
        print(f"Error querying Supabase: {e}")
        sys.exit(1)
        
    if not blocked_runs:
        print("No blocked runs found with status 'limit_exceeded'. Everything is up to date!")
        sys.exit(0)
        
    print(f"Found {len(blocked_runs)} blocked run(s) to retry.")
    
    # Check current bucket size
    LIMIT_BYTES = 9 * 1024 * 1024 * 1024
    bucket = os.getenv("R2_BUCKET_NAME")
    
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='s3',
            endpoint_url=os.getenv("R2_ENDPOINT"),
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            region_name=os.getenv("R2_REGION")
        )
        
        current_bucket_size = 0
        paginator = client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket):
            if 'Contents' in page:
                for obj in page['Contents']:
                    current_bucket_size += obj['Size']
        print(f"Current R2 bucket usage: {current_bucket_size / (1024 * 1024):.2f} MB")
    except Exception as e:
        print(f"Error checking bucket size: {e}")
        sys.exit(1)
        
    for run in blocked_runs:
        run_id = run["id"]
        lecture_title = run["lecture_title"]
        lecture_slug = slugify(lecture_title)
        error_message = run.get("error_message", "")
        
        print(f"\nProcessing Run ID {run_id}: {lecture_title}")
        
        if "Archive Paths:" not in error_message:
            print("❌ Skipping: No archive paths found in error message log.")
            continue
            
        # Parse archive paths from error message
        try:
            parts = error_message.split("Archive Paths: ")
            paths_str = parts[1].strip()
            paths_dict = {}
            for item in paths_str.split(";"):
                k, v = item.split("=")
                paths_dict[k] = v
        except Exception as e:
            print(f"❌ Error parsing archive paths from log: {e}")
            continue
            
        # Check files existence and calculate new files size
        new_files_size = 0
        all_exist = True
        for k, path in paths_dict.items():
            if not os.path.exists(path):
                print(f"❌ Missing archived file: {path}")
                all_exist = False
            else:
                new_files_size += os.path.getsize(path)
                
        if not all_exist:
            print("❌ Skipping: Some archived files are missing locally.")
            continue
            
        print(f"Total size of files to upload: {new_files_size / (1024 * 1024):.2f} MB")
        
        # Check if uploading these files would exceed the safety limit
        if current_bucket_size + new_files_size > LIMIT_BYTES:
            print(f"❌ Safety limit would still be exceeded. (Total: {(current_bucket_size + new_files_size)/(1024*1024*1024):.3f} GB / 9.000 GB)")
            print("Skipping for now (remains in queue).")
            continue
            
        # Proceed to upload
        print("Proceeding with upload...")
        
        video_key = f"lectures/{lecture_slug}/video.mp4"
        notes_key = f"lectures/{lecture_slug}/notes.docx"
        transcript_key = f"lectures/{lecture_slug}/transcript.srt"
        slides_key = f"lectures/{lecture_slug}/slides.pdf"
        
        r2_success = True
        
        # 1. Upload notes
        if "notes" in paths_dict:
            print(f"Uploading notes: {paths_dict['notes']} -> {notes_key}")
            if not upload_to_r2(paths_dict['notes'], notes_key):
                r2_success = False
                
        # 2. Upload video
        if "video" in paths_dict:
            print(f"Uploading video: {paths_dict['video']} -> {video_key}")
            if not upload_to_r2(paths_dict['video'], video_key):
                r2_success = False
                
        # 3. Upload transcript
        if "transcript" in paths_dict:
            print(f"Uploading transcript: {paths_dict['transcript']} -> {transcript_key}")
            upload_to_r2(paths_dict['transcript'], transcript_key)
            
        # 4. Upload slides
        if "slides" in paths_dict:
            print(f"Uploading slides: {paths_dict['slides']} -> {slides_key}")
            upload_to_r2(paths_dict['slides'], slides_key)
            
        if r2_success:
            print("✅ All files uploaded successfully. Updating status in Supabase...")
            # Update Supabase database status to completed
            try:
                supabase.table("pipeline_runs").update({
                    "status": "completed",
                    "r2_video_key": video_key,
                    "r2_notes_key": notes_key,
                    "error_message": None
                }).eq("id", run_id).execute()
                print("✅ Supabase run status updated to 'completed'.")
                
                # Delete local archived files
                print("Cleaning up local archived files to free up local space...")
                for k, path in paths_dict.items():
                    if os.path.exists(path):
                        os.remove(path)
                # Remove empty dir
                archive_dir = f"local-archive/{lecture_slug}"
                if os.path.exists(archive_dir) and not os.listdir(archive_dir):
                    os.rmdir(archive_dir)
                print("✅ Local archive cleanup completed.")
                
                # Update current_bucket_size for the next runs in the loop
                current_bucket_size += new_files_size
            except Exception as upd_e:
                print(f"❌ Error updating Supabase status: {upd_e}")
        else:
            print("❌ Upload failed for some files. Remains in queue.")

if __name__ == "__main__":
    main()

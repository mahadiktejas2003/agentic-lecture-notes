#!/usr/bin/env python3
import os
import sys
import json
import re
import boto3
import shutil
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cloud_uploader import upload_to_r2, log_to_supabase

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def normalize_status(status):
    if status in {"completed", "success"}:
        return "completed"
    if status in {"failed", "aborted", "cancelled", "limit_exceeded"}:
        return status
    return "completed" if status == "completed" else "in_progress"

def main():
    # Set CWD to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)
    
    if not os.path.exists("workspace_state.json"):
        print("Error: workspace_state.json not found")
        sys.exit(1)
        
    with open("workspace_state.json", "r", encoding="utf-8") as f:
        state = json.load(f)
        
    lecture_title = state["active_lecture"]["title"]
    lecture_slug = slugify(lecture_title)
    
    audit_score = state.get("audit", {}).get("score", 0)
    status = normalize_status(state.get("pipeline", {}).get("current_stage", "in_progress"))
    
    video_path = state["active_lecture"]["video_path"]
    transcript_path = state["active_lecture"]["transcript_path"]
    notes_path = state["artifacts"]["notes_output"]
    short_note_path = state.get("artifacts", {}).get("short_note_output")
    
    print(f"Uploading files for: {lecture_title} ({lecture_slug})")
    
    video_key = f"lectures/{lecture_slug}/video.mp4"
    notes_key = f"lectures/{lecture_slug}/notes.docx"
    short_note_key = f"lectures/{lecture_slug}/short-note.md"
    transcript_key = f"lectures/{lecture_slug}/transcript.srt"
    slides_key = f"lectures/{lecture_slug}/slides.pdf"
    
    # 9 GB R2 Safety limit check
    LIMIT_BYTES = 9 * 1024 * 1024 * 1024
    
    new_files_size = 0
    files_to_upload = []
    if os.path.exists(notes_path):
        files_to_upload.append(notes_path)
    if os.path.exists(video_path):
        files_to_upload.append(video_path)
    if os.path.exists(transcript_path):
        files_to_upload.append(transcript_path)
    if short_note_path and os.path.exists(short_note_path):
        files_to_upload.append(short_note_path)
    if os.path.exists("lecture-input/SLIDES.pdf"):
        files_to_upload.append("lecture-input/SLIDES.pdf")
        
    for fp in files_to_upload:
        new_files_size += os.path.getsize(fp)
        
    print(f"Size of files to upload: {new_files_size / (1024 * 1024):.2f} MB")
    
    current_bucket_size = 0
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='s3',
            endpoint_url=os.getenv("R2_ENDPOINT"),
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            region_name=os.getenv("R2_REGION")
        )
        bucket = os.getenv("R2_BUCKET_NAME")
        
        paginator = client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket):
            if 'Contents' in page:
                for obj in page['Contents']:
                    # Don't double count files that will be overwritten
                    if obj['Key'] not in [video_key, notes_key, short_note_key, transcript_key, slides_key]:
                        current_bucket_size += obj['Size']
        print(f"Current R2 bucket usage (excluding overwritten files): {current_bucket_size / (1024 * 1024):.2f} MB")
    except Exception as e:
        print(f"Warning: Could not fetch bucket storage usage: {e}")
        
    if current_bucket_size + new_files_size > LIMIT_BYTES:
        print("\n❌ UPLOAD BLOCKED: Cloudflare R2 safety storage limit of 9 GB would be exceeded!")
        print(f"   Current Bucket Size: {current_bucket_size / (1024 * 1024 * 1024):.3f} GB")
        print(f"   New Files Size: {new_files_size / (1024 * 1024 * 1024):.3f} GB")
        print("   Total would be: {:.3f} GB (Limit: 9.000 GB)".format((current_bucket_size + new_files_size) / (1024 * 1024 * 1024)))
        print("   To prevent Cloudflare charges, this upload has been blocked.")
        
        # Archive files locally for later upload
        archive_dir = f"local-archive/{lecture_slug}"
        os.makedirs(archive_dir, exist_ok=True)
        print(f"Archiving files locally in {archive_dir} for retry queue...")
        
        archived_paths = {}
        if os.path.exists(notes_path):
            shutil.copy2(notes_path, f"{archive_dir}/notes.docx")
            archived_paths["notes"] = f"{archive_dir}/notes.docx"
        if os.path.exists(video_path):
            shutil.copy2(video_path, f"{archive_dir}/video.mp4")
            archived_paths["video"] = f"{archive_dir}/video.mp4"
        if os.path.exists(transcript_path):
            shutil.copy2(transcript_path, f"{archive_dir}/transcript.srt")
            archived_paths["transcript"] = f"{archive_dir}/transcript.srt"
        if short_note_path and os.path.exists(short_note_path):
            shutil.copy2(short_note_path, f"{archive_dir}/short-note.md")
            archived_paths["short_note"] = f"{archive_dir}/short-note.md"
        if os.path.exists("lecture-input/SLIDES.pdf"):
            shutil.copy2("lecture-input/SLIDES.pdf", f"{archive_dir}/slides.pdf")
            archived_paths["slides"] = f"{archive_dir}/slides.pdf"
            
        paths_str = ";".join([f"{k}={v}" for k, v in archived_paths.items()])
        error_msg = f"Upload blocked: Cloudflare R2 safety limit of 9 GB exceeded | Archive Paths: {paths_str}"
        
        # Log to Supabase with status limit_exceeded
        run_data = {
            "lecture_title": lecture_title,
            "status": "limit_exceeded",
            "audit_score": audit_score,
            "r2_video_key": None,
            "r2_notes_key": None,
            "error_message": error_msg
        }
        print("Logging status to Supabase...")
        log_to_supabase(run_data)
        sys.exit(0)
        
    r2_success = True
    
    # 1. Upload notes
    if os.path.exists(notes_path):
        print(f"Uploading notes: {notes_path} -> {notes_key}")
        if not upload_to_r2(notes_path, notes_key):
            r2_success = False
    else:
        print(f"Warning: Notes file not found at {notes_path}")
        r2_success = False
        
    # 2. Upload video
    if os.path.exists(video_path):
        print(f"Uploading video: {video_path} -> {video_key}")
        if not upload_to_r2(video_path, video_key):
            r2_success = False
    else:
        print(f"Warning: Video file not found at {video_path}")
        video_key = None
        
    # 3. Upload transcript
    if os.path.exists(transcript_path):
        print(f"Uploading transcript: {transcript_path} -> {transcript_key}")
        if not upload_to_r2(transcript_path, transcript_key):
            r2_success = False

    # 4. Upload short note markdown
    if short_note_path and os.path.exists(short_note_path):
        print(f"Uploading short note: {short_note_path} -> {short_note_key}")
        if not upload_to_r2(short_note_path, short_note_key):
            r2_success = False
        
    # 5. Upload slides (if SLIDES.pdf exists)
    if os.path.exists("lecture-input/SLIDES.pdf"):
        print(f"Uploading slides: lecture-input/SLIDES.pdf -> {slides_key}")
        if not upload_to_r2("lecture-input/SLIDES.pdf", slides_key):
            r2_success = False
        
    # 6. Log to Supabase
    if r2_success:
        run_data = {
            "lecture_title": lecture_title,
            "status": status,
            "audit_score": audit_score,
            "r2_video_key": video_key,
            "r2_notes_key": notes_key,
            "error_message": None
        }
        print("Logging run to Supabase...")
        log_to_supabase(run_data)
        print("✅ Cloud upload and database logging complete.")
    else:
        print("❌ Cloud upload failed. Supabase logging skipped.")
        sys.exit(1)

if __name__ == "__main__":
    main()

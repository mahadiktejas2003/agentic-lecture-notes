#!/usr/bin/env python3
"""
Storage Manager for Agentic Lecture Notes Reconstruction

Handles cloud storage operations with Backblaze B2 (or S3-compatible services).
Features:
- Upload completed lectures to cloud storage
- Download lectures for reprocessing
- Automatic lifecycle policies (cleanup old frames)
- Pre-signed URL generation for secure downloads

Usage:
    from storage_manager import StorageManager
    
    manager = StorageManager()
    manager.archive_completed_lecture("cpu_scheduling_2025")
    manager.cleanup_old_frames(days=7)
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

# Backblaze B2 SDK (install: pip install b2sdk)
try:
    from b2sdk.v2 import InMemoryAccountInfo, B2Api, BucketRetentionRule
    B2_AVAILABLE = True
except ImportError:
    B2_AVAILABLE = False
    print("Warning: b2sdk not installed. Install with: pip install b2sdk")


class StorageManager:
    """Manages cloud storage for lecture videos, notes, and artifacts."""
    
    def __init__(self, bucket_name: str = "lecture-notes"):
        """
        Initialize storage manager.
        
        Args:
            bucket_name: Name of the B2 bucket to use
        """
        self.bucket_name = bucket_name
        self.local_input = Path("lecture-input")
        self.local_output = Path("notes-output")
        self.frames_cache = Path("frames-cache")
        self.agent_memory = Path("agent_memory")
        
        # B2 API (initialized on first use)
        self.b2_api: Optional[B2Api] = None
        self.bucket = None
        
        # Configuration from environment
        self.key_id = os.getenv("R2_ACCESS_KEY_ID")
        self.app_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.endpoint = os.getenv("R2_ENDPOINT", "https://api.backblazeb2.com")
        
    def _init_b2(self):
        """Initialize B2 API connection."""
        if not B2_AVAILABLE:
            raise ImportError("b2sdk not available. Install with: pip install b2sdk")
            
        if not self.key_id or not self.app_key:
            raise ValueError(
                "B2 credentials not set. Set R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY environment variables."
            )
            
        info = InMemoryAccountInfo()
        self.b2_api = B2Api(info)
        self.b2_api.authorize_account("production", self.key_id, self.app_key)
        self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
        print(f"✓ Connected to B2 bucket: {self.bucket_name}")
        
    def ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        if not self.b2_api:
            self._init_b2()
            
        try:
            self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
        except:
            # Bucket doesn't exist, create it
            self.bucket = self.b2_api.create_bucket(
                self.bucket_name, 
                "allPrivate",  # Private bucket
                bucket_default_retention=BucketRetentionRule(mode="none")
            )
            print(f"✓ Created B2 bucket: {self.bucket_name}")
            
    def upload_file(self, local_path: str, remote_path: str) -> str:
        """
        Upload a file to cloud storage.
        
        Args:
            local_path: Local file path
            remote_path: Remote path in bucket (e.g., "videos/lecture1.mp4")
            
        Returns:
            Download URL for the uploaded file
        """
        if not self.b2_api:
            self._init_b2()
            
        self.ensure_bucket_exists()
        
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")
            
        print(f"Uploading {local_path} → {remote_path}")
        
        # Upload file
        file_info = self.bucket.upload_local_file(local_path, remote_path)
        
        # Generate pre-signed URL (valid for 24 hours)
        download_url = self.bucket.get_download_url(remote_path)
        
        print(f"✓ Uploaded successfully: {download_url}")
        return download_url
        
    def download_file(self, remote_path: str, local_path: str):
        """
        Download a file from cloud storage.
        
        Args:
            remote_path: Remote path in bucket
            local_path: Local destination path
        """
        if not self.b2_api:
            self._init_b2()
            
        self.ensure_bucket_exists()
        
        print(f"Downloading {remote_path} → {local_path}")
        
        # Create directory if needed
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Download file
        self.bucket.download_file_by_name(remote_path, local_path)
        
        print(f"✓ Downloaded successfully: {local_path}")
        
    def archive_completed_lecture(self, lecture_id: str, delete_local: bool = True):
        """
        Archive a completed lecture to cloud storage.
        
        Args:
            lecture_id: Unique identifier for the lecture
            delete_local: Whether to delete local files after upload
        """
        archived_files = {}
        
        # Upload video
        video_path = self.local_input / f"{lecture_id}.mp4"
        if video_path.exists():
            remote_path = f"videos/{lecture_id}.mp4"
            url = self.upload_file(str(video_path), remote_path)
            archived_files["video"] = url
            
            if delete_local:
                os.remove(video_path)
                print(f"Deleted local video: {video_path}")
                
        # Upload transcript
        transcript_path = self.local_input / f"{lecture_id}.srt"
        if transcript_path.exists():
            remote_path = f"transcripts/{lecture_id}.srt"
            url = self.upload_file(str(transcript_path), remote_path)
            archived_files["transcript"] = url
            
            if delete_local:
                os.remove(transcript_path)
                
        # Upload generated notes
        notes_path = self.local_output / f"{lecture_id}_NOTES.docx"
        if notes_path.exists():
            remote_path = f"notes/{lecture_id}_NOTES.docx"
            url = self.upload_file(str(notes_path), remote_path)
            archived_files["notes"] = url
            
            # Don't delete notes - keep for immediate access
            
        # Upload frame manifest
        manifest_path = self.local_input / f"{lecture_id}_frame_manifest.json"
        if manifest_path.exists():
            remote_path = f"manifests/{lecture_id}_frame_manifest.json"
            url = self.upload_file(str(manifest_path), remote_path)
            archived_files["manifest"] = url
            
        # Save archive record
        archive_record = {
            "lecture_id": lecture_id,
            "archived_at": datetime.now().isoformat(),
            "files": archived_files
        }
        
        archive_path = self.agent_memory / f"archive_{lecture_id}.json"
        with open(archive_path, "w") as f:
            json.dump(archive_record, f, indent=2)
            
        print(f"✓ Archived lecture {lecture_id}: {len(archived_files)} files")
        return archived_files
        
    def cleanup_old_frames(self, days: int = 7):
        """
        Delete frame caches older than N days.
        
        Args:
            days: Number of days to retain frames
        """
        if not self.frames_cache.exists():
            return
            
        cutoff = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for filename in self.frames_cache.iterdir():
            if filename.is_file():
                mtime = datetime.fromtimestamp(filename.stat().st_mtime)
                if mtime < cutoff:
                    os.remove(filename)
                    deleted_count += 1
                    
        print(f"✓ Cleaned up {deleted_count} old frame files (> {days} days)")
        
    def list_lectures(self, prefix: str = "") -> list:
        """
        List all lectures in cloud storage.
        
        Args:
            prefix: Filter by prefix (e.g., "videos/")
            
        Returns:
            List of file metadata dictionaries
        """
        if not self.b2_api:
            self._init_b2()
            
        self.ensure_bucket_exists()
        
        lectures = []
        for file_version, folder_name in self.bucket.ls(prefix, recursive=True):
            lectures.append({
                "name": file_version.file_name,
                "size": file_version.size,
                "upload_time": datetime.fromtimestamp(file_version.upload_timestamp / 1000),
                "id": file_version.id
            })
            
        return lectures
        
    def get_download_url(self, remote_path: str, expires_hours: int = 24) -> str:
        """
        Generate a pre-signed download URL.
        
        Args:
            remote_path: Remote file path
            expires_hours: URL validity period in hours
            
        Returns:
            Pre-signed download URL
        """
        if not self.b2_api:
            self._init_b2()
            
        self.ensure_bucket_exists()
        
        # Note: B2's public URLs don't expire by default for private buckets
        # For true pre-signed URLs, you'd need to implement signed authentication
        return self.bucket.get_download_url(remote_path)


# Convenience functions for CLI usage
def archive_lecture(lecture_id: str):
    """CLI helper to archive a lecture."""
    manager = StorageManager()
    manager.archive_completed_lecture(lecture_id)
    
def cleanup_frames(days: int = 7):
    """CLI helper to clean up old frames."""
    manager = StorageManager()
    manager.cleanup_old_frames(days)
    
def list_all():
    """CLI helper to list all stored lectures."""
    manager = StorageManager()
    lectures = manager.list_lectures()
    
    print(f"\n{'File':<60} {'Size':>10} {'Uploaded':<25}")
    print("-" * 95)
    for lec in lectures:
        size_mb = lec["size"] / (1024 * 1024)
        upload_time = lec["upload_time"].strftime("%Y-%m-%d %H:%M")
        print(f"{lec['name']:<60} {size_mb:>8.1f}MB {upload_time}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python storage_manager.py <command> [args]")
        print("\nCommands:")
        print("  archive <lecture_id>   - Archive completed lecture to cloud")
        print("  cleanup [days]         - Remove frames older than N days (default: 7)")
        print("  list                   - List all stored lectures")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "archive" and len(sys.argv) > 2:
        archive_lecture(sys.argv[2])
    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        cleanup_frames(days)
    elif command == "list":
        list_all()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

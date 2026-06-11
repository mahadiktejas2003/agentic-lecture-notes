#!/usr/bin/env python3
"""
Minimal Web UI for Agentic Lecture Notes Reconstruction

Phase 1: FastAPI + Background Tasks (No JavaScript framework needed)

Features:
- Upload video and transcript files
- Trigger pipeline processing
- Check processing status
- Download generated notes

Usage:
    cd web_ui
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload
    
Access at: http://localhost:8000
"""

import os
import uuid
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="Lecture Notes Generator",
    description="Upload lecture videos and transcripts to generate exam-ready notes",
    version="1.0.0"
)

# Directories
UPLOAD_DIR = Path("lecture-input")
OUTPUT_DIR = Path("notes-output")
STATUS_DIR = Path("agent_memory/status")

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATUS_DIR.mkdir(exist_ok=True)


# Status tracking
processing_status: Dict[str, dict] = {}


class ProcessingStatus(BaseModel):
    lecture_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    output_file: Optional[str] = None


def run_pipeline(lecture_id: str, video_path: str, transcript_path: str):
    """Background task to run the note generation pipeline."""
    
    status_file = STATUS_DIR / f"{lecture_id}.json"
    
    try:
        # Update status to processing
        status = {
            "lecture_id": lecture_id,
            "status": "processing",
            "progress": "Starting pipeline...",
            "started_at": datetime.now().isoformat()
        }
        with open(status_file, "w") as f:
            json.dump(status, f)
            
        # Run the orchestrator
        result = subprocess.run(
            ["python3", "scripts/langgraph_orchestrator.py"],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode == 0:
            # Success
            output_file = OUTPUT_DIR / "LECTURE_NOTES.docx"
            if output_file.exists():
                # Rename to include lecture_id
                final_output = OUTPUT_DIR / f"{lecture_id}_NOTES.docx"
                shutil.move(str(output_file), str(final_output))
                
                status.update({
                    "status": "completed",
                    "progress": "Notes generated successfully!",
                    "completed_at": datetime.now().isoformat(),
                    "output_file": str(final_output)
                })
            else:
                status.update({
                    "status": "failed",
                    "progress": "Pipeline completed but no output file found",
                    "error_message": "Output file not generated"
                })
        else:
            # Failure
            status.update({
                "status": "failed",
                "progress": "Pipeline failed",
                "error_message": result.stderr[:500] if result.stderr else "Unknown error"
            })
            
    except subprocess.TimeoutExpired:
        status = {
            "lecture_id": lecture_id,
            "status": "failed",
            "progress": "Processing timed out (>30 minutes)",
            "error_message": "Timeout expired"
        }
    except Exception as e:
        status = {
            "lecture_id": lecture_id,
            "status": "failed",
            "progress": "Unexpected error",
            "error_message": str(e)
        }
        
    # Save final status
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lecture Notes Generator</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { 
            color: #333; 
            margin-bottom: 10px;
            font-size: 2.5rem;
        }
        .subtitle { color: #666; margin-bottom: 30px; }
        .form-group { margin-bottom: 25px; }
        label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 600;
            color: #444;
        }
        input[type="file"] {
            width: 100%;
            padding: 15px;
            border: 2px dashed #ddd;
            border-radius: 8px;
            cursor: pointer;
            transition: border-color 0.3s;
        }
        input[type="file"]:hover { border-color: #667eea; }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .status-box {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        .status-box.active { display: block; }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        .status-pending { background: #ffeeba; color: #856404; }
        .status-processing { background: #b8daff; color: #004085; }
        .status-completed { background: #c3e6cb; color: #155724; }
        .status-failed { background: #f5c6cb; color: #721c24; }
        .progress-bar {
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            margin: 15px 0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s;
        }
        .download-btn {
            display: inline-block;
            margin-top: 15px;
            padding: 12px 30px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
        }
        .download-btn:hover { background: #218838; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Lecture Notes Generator</h1>
        <p class="subtitle">Upload your lecture video and transcript to generate exam-ready notes automatically</p>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="form-group">
                <label for="video">🎥 Lecture Video (MP4)</label>
                <input type="file" id="video" name="video" accept=".mp4,.mkv,.avi" required>
            </div>
            
            <div class="form-group">
                <label for="transcript">📝 Transcript File (SRT)</label>
                <input type="file" id="transcript" name="transcript" accept=".srt,.txt" required>
            </div>
            
            <button type="submit" id="submitBtn">Generate Notes</button>
        </form>
        
        <div class="status-box" id="statusBox">
            <h3>Processing Status</h3>
            <span class="status-badge" id="statusBadge">pending</span>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <p id="progressText">Waiting to start...</p>
            <a id="downloadLink" class="download-btn" style="display:none;">Download Notes</a>
        </div>
    </div>
    
    <script>
        let currentLectureId = null;
        let statusInterval = null;
        
        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('video', document.getElementById('video').files[0]);
            formData.append('transcript', document.getElementById('transcript').files[0]);
            
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            
            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                currentLectureId = data.lecture_id;
                
                // Show status box
                document.getElementById('statusBox').classList.add('active');
                
                // Poll for status updates
                statusInterval = setInterval(checkStatus, 2000);
                
            } catch (error) {
                alert('Upload failed: ' + error.message);
                submitBtn.disabled = false;
                submitBtn.textContent = 'Generate Notes';
            }
        });
        
        async function checkStatus() {
            if (!currentLectureId) return;
            
            try {
                const response = await fetch(`/status/${currentLectureId}`);
                const data = await response.json();
                
                const badge = document.getElementById('statusBadge');
                const progressFill = document.getElementById('progressFill');
                const progressText = document.getElementById('progressText');
                const downloadLink = document.getElementById('downloadLink');
                
                badge.textContent = data.status;
                badge.className = 'status-badge status-' + data.status;
                progressText.textContent = data.progress;
                
                if (data.status === 'processing') {
                    progressFill.style.width = '60%';
                } else if (data.status === 'completed') {
                    progressFill.style.width = '100%';
                    downloadLink.href = '/download/' + currentLectureId;
                    downloadLink.style.display = 'inline-block';
                    clearInterval(statusInterval);
                    
                    document.getElementById('submitBtn').disabled = false;
                    document.getElementById('submitBtn').textContent = 'Generate Another';
                } else if (data.status === 'failed') {
                    progressFill.style.width = '0%';
                    progressText.textContent += ': ' + (data.error_message || 'Unknown error');
                    clearInterval(statusInterval);
                    
                    document.getElementById('submitBtn').disabled = false;
                    document.getElementById('submitBtn').textContent = 'Try Again';
                }
                
            } catch (error) {
                console.error('Status check failed:', error);
            }
        }
    </script>
</body>
</html>
    """


@app.post("/process")
async def process_lecture(
    video: UploadFile,
    transcript: UploadFile,
    background_tasks: BackgroundTasks
):
    """
    Process a lecture upload.
    
    Args:
        video: Uploaded video file
        transcript: Uploaded transcript file
        background_tasks: FastAPI background tasks
        
    Returns:
        Lecture ID for status tracking
    """
    # Generate unique lecture ID
    lecture_id = str(uuid.uuid4())[:8]
    
    # Save uploaded files with STANDARD NAMES that orchestrator expects
    video_ext = Path(video.filename).suffix or ".mp4"
    transcript_ext = Path(transcript.filename).suffix or ".srt"
    
    # Use standard names: LECTURE.mp4 and transcript.srt
    video_path = UPLOAD_DIR / f"LECTURE{video_ext}"
    transcript_path = UPLOAD_DIR / f"transcript{transcript_ext}"
    
    # Backup any existing files first
    if video_path.exists():
        backup_video = UPLOAD_DIR / f"LECTURE_backup_{lecture_id}{video_ext}"
        shutil.move(str(video_path), str(backup_video))
        
    if transcript_path.exists():
        backup_transcript = UPLOAD_DIR / f"transcript_backup_{lecture_id}{transcript_ext}"
        shutil.move(str(transcript_path), str(backup_transcript))
    
    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)
        
    with open(transcript_path, "wb") as f:
        shutil.copyfileobj(transcript.file, f)
        
    # Initialize status
    initial_status = {
        "lecture_id": lecture_id,
        "status": "pending",
        "progress": "Files uploaded, queueing for processing",
        "started_at": datetime.now().isoformat()
    }
    
    status_file = STATUS_DIR / f"{lecture_id}.json"
    with open(status_file, "w") as f:
        json.dump(initial_status, f, indent=2)
        
    # Queue background processing
    background_tasks.add_task(run_pipeline, lecture_id, str(video_path), str(transcript_path))
    
    return {
        "lecture_id": lecture_id,
        "status": "pending",
        "message": "Upload successful. Processing started."
    }


@app.get("/status/{lecture_id}")
async def get_status(lecture_id: str):
    """Get processing status for a lecture."""
    status_file = STATUS_DIR / f"{lecture_id}.json"
    
    if not status_file.exists():
        raise HTTPException(status_code=404, detail="Lecture not found")
        
    with open(status_file, "r") as f:
        status = json.load(f)
        
    return status


@app.get("/download/{lecture_id}")
async def download_notes(lecture_id: str):
    """Download generated notes for a lecture."""
    notes_file = OUTPUT_DIR / f"{lecture_id}_NOTES.docx"
    
    if not notes_file.exists():
        raise HTTPException(status_code=404, detail="Notes file not found")
        
    return FileResponse(
        str(notes_file),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{lecture_id}_NOTES.docx"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

#!/usr/bin/env python3
"""
Enhanced Web UI for Agentic Lecture Notes Reconstruction
With local GPU ASR support and real-time execution log visualization.
"""

import os
import uuid
import json
import shutil
import subprocess
import signal
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

app = FastAPI(
    title="Lecture Notes Generator",
    description="Upload lecture videos and transcripts to generate exam-ready notes",
    version="1.1.0"
)

# Directories
PROJECT_ROOT = Path(__file__).parent.parent
UPLOAD_DIR = PROJECT_ROOT / "lecture-input"
OUTPUT_DIR = PROJECT_ROOT / "notes-output"
STATUS_DIR = PROJECT_ROOT / "agent_memory" / "status"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATUS_DIR.mkdir(exist_ok=True)

# Global process tracking for cancel/stop support
active_processes: Dict[str, subprocess.Popen] = {}
DEFAULT_ASR_TIMEOUT_SECONDS = "7200"


def terminate_process_tree(process: subprocess.Popen, grace_seconds: int = 5):
    """Terminate a subprocess and its children when it was started in a new session."""
    if process.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait(timeout=grace_seconds)
    except (subprocess.TimeoutExpired, ProcessLookupError, OSError):
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            try:
                process.kill()
            except OSError:
                pass
def save_status_atomic(filepath: Path, data: dict, indent: Optional[int] = None):
    """Write status data atomically to prevent partial reads."""
    temp_filepath = filepath.with_suffix(".tmp")
    with open(temp_filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)
    os.replace(temp_filepath, filepath)


def parse_asr_progress_from_log(log_path: Path) -> dict:
    """Parse the latest ASR chunk progress percentage and chunk info from a log file."""
    result = {"asr_percent": 0.0, "chunk_info": ""}
    if not log_path.exists():
        return result
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Search from the end for the latest progress line
        for line in reversed(lines):
            if "ASR progress:" in line and "chunk_completed" in line:
                # Parse: "ASR progress:  71.6% | chunk_completed | chunk 140/193"
                pct_match = re.search(r'ASR progress:\s+([\d.]+)%', line)
                chunk_match = re.search(r'chunk (\d+)/(\d+)', line)
                if pct_match:
                    result["asr_percent"] = float(pct_match.group(1))
                if chunk_match:
                    result["chunk_info"] = f"Processing chunk {chunk_match.group(1)}/{chunk_match.group(2)}"
                break
    except Exception:
        pass
    return result
LOGS_DIR.mkdir(exist_ok=True)


async def validate_uploaded_file(file: UploadFile, file_type: str):
    """
    Validates uploaded file suffix, content-type, and magic headers.
    file_type can be 'video', 'transcript', or 'slides'.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    
    suffix = Path(file.filename).suffix.lower()
    content_type = file.content_type.lower() if file.content_type else ""
    
    if file_type == 'video':
        valid_suffixes = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.wav', '.mp3', '.m4a', '.mpeg', '.ogg'}
        if suffix not in valid_suffixes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid video/audio extension '{suffix}'. Supported: {', '.join(valid_suffixes)}"
            )
        if content_type and not (content_type.startswith("video/") or content_type.startswith("audio/") or content_type == "application/octet-stream"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid MIME type '{content_type}' for video/audio."
            )
            
    elif file_type == 'transcript':
        valid_suffixes = {'.srt', '.vtt', '.txt'}
        if suffix not in valid_suffixes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transcript extension '{suffix}'. Supported: {', '.join(valid_suffixes)}"
            )
        if content_type and not (content_type.startswith("text/") or "subrip" in content_type or content_type == "application/octet-stream"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid MIME type '{content_type}' for transcript."
            )
            
    elif file_type == 'slides':
        valid_suffixes = {'.pdf'}
        if suffix not in valid_suffixes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid slides extension '{suffix}'. Supported: PDF only."
            )
        if content_type and content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid MIME type '{content_type}' for slides. Expected PDF."
            )
        # Check PDF header
        try:
            header = await file.read(4)
            await file.seek(0)
            if header != b'%PDF':
                raise HTTPException(
                    status_code=400,
                    detail="File header validation failed. The file is not a valid PDF document."
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Unable to read file headers for PDF validation."
            )


async def save_upload_file_async(file: UploadFile, destination: Path):
    """
    Saves an UploadFile to destination path in chunks asynchronously.
    """
    try:
        with open(destination, "wb") as buffer:
            while True:
                # Read 1MB chunk asynchronously
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)
    finally:
        await file.close()


class ProcessingStatus(BaseModel):
    lecture_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    output_file: Optional[str] = None


def run_pipeline(lecture_id: str, video_path: str, transcript_path: str, language: str = "hi"):
    """Background task to run the note generation pipeline."""
    
    status_file = STATUS_DIR / f"{lecture_id}.json"
    log_file_path = LOGS_DIR / f"pipeline_{lecture_id}.log"
    
    try:
        # Update status to processing
        status = {
            "lecture_id": lecture_id,
            "status": "processing",
            "progress": "Initializing local ASR pipelines...",
            "started_at": datetime.now().isoformat()
        }
        save_status_atomic(status_file, status)
            
        # Run the orchestrator with Popen and redirect stdout/stderr to the specific log file in real-time
        import sys
        env = os.environ.copy()
        env["ASR_LANGUAGE"] = language
        
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                [sys.executable, "scripts/langgraph_orchestrator.py"],
                cwd=str(PROJECT_ROOT),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True
            )
            
            # Track process for cancel support
            active_processes[lecture_id] = process
            
            try:
                # Match the orchestrator's ASR timeout default so long videos are not killed early.
                timeout = int(os.environ.get("ASR_TIMEOUT", DEFAULT_ASR_TIMEOUT_SECONDS))
                retcode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                terminate_process_tree(process)
                retcode = -9
                log_file.write(f"\n[TIMEOUT] Pipeline run exceeded {timeout // 60} minutes and was terminated.\n")
            finally:
                active_processes.pop(lecture_id, None)
        
        if retcode == 0:
            # Success
            output_file = OUTPUT_DIR / "LECTURE_NOTES.docx"
            if output_file.exists():
                # Keep the canonical notes path intact for workspace_state, upload, and audit handoff.
                final_output = OUTPUT_DIR / f"{lecture_id}_NOTES.docx"
                shutil.copy2(str(output_file), str(final_output))
                
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
                    "error_message": "Output file LECTURE_NOTES.docx not generated"
                })
        elif retcode == -9:
            status.update({
                "status": "failed",
                "progress": f"Processing timed out (>{timeout // 60} minutes)",
                "error_message": "Timeout expired"
            })
        else:
            # Read last part of the log file for error description
            err_msg = "Pipeline process failed"
            if log_file_path.exists():
                try:
                    with open(log_file_path, "r", encoding="utf-8") as lf:
                        lines = lf.readlines()
                        err_msg = "".join(lines[-5:]).strip()[:500]
                except Exception:
                    pass
            status.update({
                "status": "failed",
                "progress": "Pipeline execution failed",
                "error_message": err_msg if err_msg else f"Process exited with code {retcode}"
            })
            
    except Exception as e:
        status = {
            "lecture_id": lecture_id,
            "status": "failed",
            "progress": "Unexpected error",
            "error_message": str(e)
        }
        
    # Save final status
    save_status_atomic(status_file, status, indent=2)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Lecture Notes & ASR Studio</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(17, 25, 40, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent-glow: #6366f1;
            --accent-secondary: #a855f7;
            --success-color: #10b981;
            --error-color: #ef4444;
            --primary-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            --asr-gradient: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            --shadow-primary: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 10% 20%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
                radial-gradient(at 90% 80%, rgba(168, 85, 247, 0.12) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px 20px;
        }

        .container {
            width: 100%;
            max-width: 900px;
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 40px;
            box-shadow: var(--shadow-primary);
        }

        header {
            text-align: center;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 2.6rem;
            font-weight: 700;
            background: linear-gradient(90deg, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 1.05rem;
            font-weight: 350;
        }

        /* Tabs styling */
        .tab-container {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 12px;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 10px 20px;
            font-size: 1.05rem;
            font-weight: 500;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s ease;
            font-family: inherit;
        }

        .tab-btn.active {
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }

        .tab-btn:hover:not(.active) {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.03);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }

        .form-group {
            margin-bottom: 24px;
        }

        label {
            display: block;
            margin-bottom: 10px;
            font-weight: 500;
            font-size: 0.95rem;
            color: var(--text-primary);
        }

        /* Drag & Drop File Input styling */
        .file-upload-wrapper {
            position: relative;
            width: 100%;
            height: 100px;
            border: 2px dashed rgba(99, 102, 241, 0.3);
            border-radius: 14px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.02);
        }

        .file-upload-wrapper:hover, .file-upload-wrapper.dragover {
            border-color: var(--accent-glow);
            background: rgba(99, 102, 241, 0.05);
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);
        }

        .file-upload-wrapper input[type="file"] {
            position: absolute;
            left: 0;
            top: 0;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }

        .upload-icon {
            font-size: 24px;
            margin-bottom: 6px;
            transition: transform 0.2s ease;
        }

        .file-upload-wrapper:hover .upload-icon {
            transform: translateY(-2px);
        }

        .upload-text {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .upload-filename {
            font-size: 0.9rem;
            color: #818cf8;
            font-weight: 500;
            margin-top: 6px;
            display: none;
        }

        .optional-tag {
            font-size: 0.75rem;
            background: rgba(255, 255, 255, 0.08);
            padding: 2px 8px;
            border-radius: 12px;
            margin-left: 8px;
            color: var(--text-secondary);
            font-weight: normal;
        }

        /* Collapsible settings panel */
        .collapsible-trigger {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--card-border);
            padding: 12px 20px;
            border-radius: 12px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            font-weight: 500;
            font-size: 0.95rem;
            transition: all 0.2s ease;
        }

        .collapsible-trigger:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .collapsible-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
            padding: 0 10px;
        }

        .collapsible-content.open {
            max-height: 200px;
            margin-bottom: 24px;
        }

        select {
            width: 100%;
            background: #111827;
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 12px 16px;
            border-radius: 10px;
            outline: none;
            cursor: pointer;
            font-family: inherit;
        }

        select:focus {
            border-color: var(--accent-glow);
        }

        button.btn-submit {
            width: 100%;
            background: var(--primary-gradient);
            color: white;
            border: none;
            padding: 16px;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 14px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
            transition: all 0.3s ease;
        }

        button.btn-submit.asr-only-btn {
            background: var(--asr-gradient);
            box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
        }

        button.btn-submit:hover {
            transform: translateY(-2px);
        }

        button.btn-submit:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
        }

        /* Status card */
        .status-box {
            margin-top: 40px;
            padding: 24px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            display: none;
            animation: fadeIn 0.4s ease;
        }

        .status-box.active {
            display: block;
        }

        .status-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }

        .status-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-pending { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
        .status-processing { background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); }
        .status-completed { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .status-failed { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .status-cancelled { background: rgba(251, 146, 60, 0.15); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.3); }

        .btn-stop {
            width: 100%;
            background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
            color: white;
            border: none;
            padding: 14px;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 14px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(239, 68, 68, 0.3);
            transition: all 0.3s ease;
            margin-top: 12px;
            display: none;
        }

        .btn-stop:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(239, 68, 68, 0.4);
        }

        .btn-stop.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }

        .progress-bar {
            height: 6px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            margin: 15px 0;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: var(--primary-gradient);
            width: 0%;
            transition: width 0.5s ease;
        }

        .asr-progress .progress-fill {
            background: var(--asr-gradient);
        }

        /* Pipeline Visual Steps */
        .pipeline-steps {
            display: flex;
            justify-content: space-between;
            margin: 24px 0;
            font-size: 0.8rem;
            color: var(--text-secondary);
            position: relative;
        }

        .pipeline-steps::before {
            content: '';
            position: absolute;
            top: 10px;
            left: 0;
            right: 0;
            height: 2px;
            background: rgba(255, 255, 255, 0.05);
            z-index: 1;
        }

        .step-node {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 2;
            width: 80px;
            text-align: center;
        }

        .step-dot {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #111827;
            border: 2px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 8px;
            transition: all 0.3s ease;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 10px;
            font-weight: bold;
            color: transparent;
        }

        .step-node.active .step-dot {
            border-color: var(--accent-glow);
            box-shadow: 0 0 10px rgba(99, 102, 241, 0.6);
            background: var(--accent-glow);
            color: white;
        }

        .step-node.completed .step-dot {
            border-color: var(--success-color);
            background: var(--success-color);
            color: white;
        }

        .step-node.completed .step-dot::after {
            content: '✓';
            color: white;
            font-size: 11px;
        }

        /* Logs Console styling */
        .console-wrapper {
            margin-top: 24px;
        }

        .console-header {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .console-log {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            background: #06090f;
            border: 1px solid var(--card-border);
            padding: 16px;
            border-radius: 10px;
            height: 180px;
            overflow-y: auto;
            white-space: pre-wrap;
            color: #34d399;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.8);
            line-height: 1.4;
        }

        .download-btn {
            display: none;
            width: 100%;
            text-align: center;
            margin-top: 24px;
            padding: 15px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            transition: all 0.2s ease;
        }

        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
        }

        .asr-download-buttons {
            display: flex;
            gap: 12px;
            margin-top: 24px;
        }

        .asr-download-btn {
            display: none;
            flex: 1;
            text-align: center;
            padding: 14px;
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
            font-size: 0.95rem;
        }

        .asr-download-btn.srt {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }

        .asr-download-btn.txt {
            background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        }

        .asr-download-btn:hover {
            transform: translateY(-2px);
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Scrollbar styling */
        .console-log::-webkit-scrollbar {
            width: 8px;
        }
        .console-log::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.2);
            border-radius: 0 10px 10px 0;
        }
        .console-log::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
        }
        .console-log::-webkit-scrollbar-thumb:hover {
            background: rgba(255,255,255,0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 AI Lecture Notes & ASR Studio</h1>
            <p class="subtitle">Extract audio and automatically transcribe Hinglish speech locally on M4 Metal GPU</p>
        </header>

        <!-- Tabs -->
        <div class="tab-container">
            <button class="tab-btn active" id="tabNotes" onclick="switchTab('notes')">📝 Lecture Notes Reconstruction</button>
            <button class="tab-btn" id="tabASR" onclick="switchTab('asr')">🎙️ ASR-Only Speech-to-Text</button>
            <button class="tab-btn" id="tabWatcher" onclick="switchTab('watcher')">🎧 Watch Folder</button>
        </div>
        
        <!-- Tab 1: Notes Generation Form -->
        <div class="tab-content active" id="notesContentSection">
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="video">🎥 Lecture Video (MP4/MKV/MOV) <span class="optional-tag">Optional if transcript provided</span></label>
                    <div class="file-upload-wrapper" id="videoWrapper">
                        <div class="upload-icon">📹</div>
                        <div class="upload-text">Drag & drop video file or click to browse</div>
                        <div class="upload-filename" id="videoFilename"></div>
                        <input type="file" id="video" name="video" accept=".mp4,.mkv,.mov,.avi">
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="transcript">📝 Transcript File (SRT/TXT) <span class="optional-tag">Optional</span></label>
                    <div class="file-upload-wrapper" id="transcriptWrapper">
                        <div class="upload-icon">📄</div>
                        <div class="upload-text">Leave empty to auto-transcribe Hinglish speech locally</div>
                        <div class="upload-filename" id="transcriptFilename"></div>
                        <input type="file" id="transcript" name="transcript" accept=".srt,.txt">
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="slides">📊 Slide Deck (PDF) <span class="optional-tag">Optional</span></label>
                    <div class="file-upload-wrapper" id="slidesWrapper">
                        <div class="upload-icon">📉</div>
                        <div class="upload-text">Drag & drop slide PDF or click to browse</div>
                        <div class="upload-filename" id="slidesFilename"></div>
                        <input type="file" id="slides" name="slides" accept=".pdf">
                    </div>
                </div>

                <!-- Collapsible Advanced Settings -->
                <div class="collapsible-trigger" id="settingsTrigger">
                    <span>⚙️ Advanced Speech Recognition Settings</span>
                    <span id="triggerChevron">▼</span>
                </div>
                
                <div class="collapsible-content" id="settingsContent">
                    <div class="form-group">
                        <label for="language">🗣️ Transcription Language Model</label>
                        <select id="language" name="language">
                            <option value="hi">Hindi + English (Hinglish Mixed - Recommended)</option>
                            <option value="en">English Only</option>
                            <option value="auto">Auto-Detect Speech</option>
                        </select>
                    </div>
                </div>
                
                <button type="submit" id="submitBtn" class="btn-submit">Generate Lecture Notes</button>
                <button type="button" id="stopPipelineBtn" class="btn-stop" onclick="cancelPipelineJob()">⏹ Stop Pipeline</button>
            </form>
            
            <div class="status-box" id="statusBox">
                <div class="status-header">
                    <h3>Pipeline Status</h3>
                    <span class="status-badge" id="statusBadge">pending</span>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <p id="progressText" style="font-size: 0.9rem; color: var(--text-secondary);">Uploading files...</p>
                
                <!-- Pipeline stage nodes -->
                <div class="pipeline-steps">
                    <div class="step-node" id="stepASR">
                        <div class="step-dot"></div>
                        <div>ASR Transcribe</div>
                    </div>
                    <div class="step-node" id="stepFrames">
                        <div class="step-dot"></div>
                        <div>Frame OCR</div>
                    </div>
                    <div class="step-node" id="stepMapping">
                        <div class="step-dot"></div>
                        <div>Concept Map</div>
                    </div>
                    <div class="step-node" id="stepComposition">
                        <div class="step-dot"></div>
                        <div>Composition</div>
                    </div>
                    <div class="step-node" id="stepAudit">
                        <div class="step-dot"></div>
                        <div>18 Gates</div>
                    </div>
                </div>

                <!-- Console Log viewer -->
                <div class="console-wrapper">
                    <div class="console-header">
                        <span>⚙️ Agent Reconstruction Console Output</span>
                        <span id="consoleStatus" style="color: var(--accent-glow);">Polling...</span>
                    </div>
                    <div class="console-log" id="consoleLog">Logs will appear here once processing starts...</div>
                </div>
                
                <a id="downloadLink" class="download-btn">📥 Download Final Document (.docx)</a>
            </div>
        </div>

        <!-- Tab 2: ASR-Only Form -->
        <div class="tab-content" id="asrContentSection">
            <form id="asrForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="asrFile">🎵 Input Video or Audio File (MP4/MKV/MOV/MP3/WAV/M4A)</label>
                    <div class="file-upload-wrapper" id="asrFileWrapper">
                        <div class="upload-icon">🎙️</div>
                        <div class="upload-text">Drag & drop video/audio file or click to browse</div>
                        <div class="upload-filename" id="asrFilename"></div>
                        <input type="file" id="asrFile" name="file" accept=".mp4,.mkv,.mov,.avi,.mp3,.wav,.m4a,.webm" required>
                    </div>
                </div>

                <div class="form-group">
                    <label for="asrLanguage">🗣️ Speech Language</label>
                    <select id="asrLanguage" name="language">
                        <option value="hi">Hindi + English (Hinglish Mixed - Recommended)</option>
                        <option value="en">English Only</option>
                        <option value="auto">Auto-Detect Speech</option>
                    </select>
                </div>
                
                <button type="submit" id="asrSubmitBtn" class="btn-submit asr-only-btn">Start Local Transcription</button>
                <button type="button" id="stopAsrBtn" class="btn-stop" onclick="cancelAsrJob()">⏹ Stop Transcription</button>
            </form>

            <div class="status-box" id="asrStatusBox">
                <div class="status-header">
                    <h3>ASR Speech Studio Status</h3>
                    <span class="status-badge" id="asrStatusBadge">pending</span>
                </div>
                
                <div class="progress-bar asr-progress">
                    <div class="progress-fill" id="asrProgressFill"></div>
                </div>
                <p id="asrProgressText" style="font-size: 0.9rem; color: var(--text-secondary);">Uploading audio...</p>

                <!-- Console Log viewer -->
                <div class="console-wrapper">
                    <div class="console-header">
                        <span>⚙️ Qwen3-ASR Progress logs</span>
                        <span id="asrConsoleStatus" style="color: var(--accent-glow);">Polling...</span>
                    </div>
                    <div class="console-log" id="asrConsoleLog">Transcription logs will appear here once audio analysis begins...</div>
                </div>
                
                <div class="asr-download-buttons">
                    <a id="asrDownloadSrtLink" class="asr-download-btn srt">🎬 Download Subtitles (.srt)</a>
                    <a id="asrDownloadTxtLink" class="asr-download-btn txt">📄 Download Text (.txt)</a>
                </div>
                
                <div id="asrFilePathContainer" style="display: none; margin-top: 20px; padding: 15px; background: rgba(255, 255, 255, 0.04); border: 1px solid var(--card-border); border-radius: 12px; text-align: left;">
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 5px; font-weight: 500;">💾 Transcribed File Local Path:</div>
                    <code id="asrFilePathText" style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--success-color); word-break: break-all; select: all; display: block; background: #000000; padding: 8px; border-radius: 6px;"></code>
                </div>
            </div>
        </div>

        <!-- Tab 3: Watch Folder Dashboard -->
        <div class="tab-content" id="watcherContentSection">
            <div style="margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                    <h2 style="margin: 0; font-size: 1.4rem;">🎧 Background Transcription Daemon</h2>
                    <span id="watcherAliveIndicator" style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; background: rgba(255,50,50,0.15); color: #ff6b6b;">🔴 Offline</span>
                </div>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">Watches <code>~/Downloads/</code> for new video files and transcribes them automatically using Qwen3-ASR. Transcripts saved to <code>~/Transcripts/</code></p>
            </div>

            <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                <button id="watcherPauseBtn" class="btn-submit" style="padding: 10px 20px; font-size: 0.9rem;" onclick="toggleWatcherPause()">⏸️ Pause</button>
                <button class="btn-submit" style="padding: 10px 20px; font-size: 0.9rem; background: linear-gradient(135deg, #f39c12, #e67e22);" onclick="retryFailedJobs()">🔄 Retry All Failed</button>
                <button class="btn-submit" style="padding: 10px 20px; font-size: 0.9rem; background: linear-gradient(135deg, #3498db, #2980b9);" onclick="refreshWatcherQueue()">🔃 Refresh</button>
            </div>

            <!-- Stats Cards -->
            <div id="watcherStats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px;"></div>

            <!-- Currently Transcribing -->
            <div id="watcherCurrentJob" style="display: none; padding: 15px; background: rgba(52, 152, 219, 0.1); border: 1px solid rgba(52, 152, 219, 0.3); border-radius: 12px; margin-bottom: 20px;">
                <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 5px;">🎙️ Currently Transcribing:</div>
                <div id="watcherCurrentFileName" style="font-weight: 600; font-size: 1rem;"></div>
            </div>

            <!-- Job Queue Table -->
            <div style="border-radius: 12px; overflow: hidden; border: 1px solid var(--card-border);">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
                    <thead>
                        <tr style="background: rgba(255,255,255,0.05);">
                            <th style="padding: 12px 15px; text-align: left; font-weight: 600; color: var(--text-secondary);">File</th>
                            <th style="padding: 12px 15px; text-align: center; font-weight: 600; color: var(--text-secondary); width: 100px;">Status</th>
                            <th style="padding: 12px 15px; text-align: left; font-weight: 600; color: var(--text-secondary);">Transcript Path</th>
                            <th style="padding: 12px 15px; text-align: right; font-weight: 600; color: var(--text-secondary); width: 150px;">Time</th>
                        </tr>
                    </thead>
                    <tbody id="watcherQueueBody">
                        <tr><td colspan="4" style="padding: 30px; text-align: center; color: var(--text-secondary);">Loading queue...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let currentLectureId = null;
        let currentAsrLectureId = null;
        let statusInterval = null;
        let logsInterval = null;
        let asrStatusInterval = null;
        let asrLogsInterval = null;
        
        // Tab switching logic
        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Clear watcher interval when switching away
            if (watcherPollInterval && tab !== 'watcher') {
                clearInterval(watcherPollInterval);
                watcherPollInterval = null;
            }

            if (tab === 'notes') {
                document.getElementById('tabNotes').classList.add('active');
                document.getElementById('notesContentSection').classList.add('active');
            } else if (tab === 'asr') {
                document.getElementById('tabASR').classList.add('active');
                document.getElementById('asrContentSection').classList.add('active');
            } else if (tab === 'watcher') {
                document.getElementById('tabWatcher').classList.add('active');
                document.getElementById('watcherContentSection').classList.add('active');
                refreshWatcherQueue();
                if (!watcherPollInterval) {
                    watcherPollInterval = setInterval(refreshWatcherQueue, 3000);
                }
            }
        }

        // ── Watch Folder Dashboard Functions ──
        let watcherPollInterval = null;

        async function refreshWatcherQueue() {
            try {
                const res = await fetch('/watcher/status');
                const data = await res.json();
                
                // Update alive indicator
                const indicator = document.getElementById('watcherAliveIndicator');
                if (data.alive) {
                    if (data.on_battery) {
                        indicator.innerHTML = '⚠️ Paused (Running on Battery)';
                        indicator.style.background = 'rgba(243,156,18,0.15)';
                        indicator.style.color = '#f39c12';
                    } else if (data.paused) {
                        indicator.innerHTML = '⏸️ Paused';
                        indicator.style.background = 'rgba(155,89,182,0.15)';
                        indicator.style.color = '#9b59b6';
                    } else {
                        indicator.innerHTML = '🟢 Online';
                        indicator.style.background = 'rgba(46,204,113,0.15)';
                        indicator.style.color = '#2ecc71';
                    }
                } else {
                    indicator.innerHTML = '🔴 Offline';
                    indicator.style.background = 'rgba(255,50,50,0.15)';
                    indicator.style.color = '#ff6b6b';
                }

                // Update pause button
                const pauseBtn = document.getElementById('watcherPauseBtn');
                if (data.paused) {
                    pauseBtn.innerHTML = '▶️ Resume';
                    pauseBtn.style.background = 'linear-gradient(135deg, #2ecc71, #27ae60)';
                } else {
                    pauseBtn.innerHTML = '⏸️ Pause';
                    pauseBtn.style.background = '';
                }

                // Update stats cards
                const stats = data.stats || {};
                const statsDiv = document.getElementById('watcherStats');
                const statItems = [
                    { label: 'Queued', value: stats.queued || 0, color: '#3498db', icon: '📋' },
                    { label: 'Transcribing', value: stats.transcribing || 0, color: '#f39c12', icon: '🎙️' },
                    { label: 'Completed', value: stats.completed || 0, color: '#2ecc71', icon: '✅' },
                    { label: 'Failed', value: stats.failed || 0, color: '#e74c3c', icon: '❌' },
                ];
                statsDiv.innerHTML = statItems.map(s => `
                    <div style="padding: 15px; background: rgba(255,255,255,0.03); border: 1px solid var(--card-border); border-radius: 10px; text-align: center;">
                        <div style="font-size: 1.5rem;">${s.icon}</div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: ${s.color};">${s.value}</div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">${s.label}</div>
                    </div>
                `).join('');

                // Update current job
                const currentDiv = document.getElementById('watcherCurrentJob');
                if (data.currently_transcribing) {
                    currentDiv.style.display = 'block';
                    document.getElementById('watcherCurrentFileName').textContent = data.currently_transcribing;
                } else {
                    currentDiv.style.display = 'none';
                }

                // Fetch queue
                const qRes = await fetch('/watcher/queue');
                const jobs = await qRes.json();
                const tbody = document.getElementById('watcherQueueBody');
                
                if (jobs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="padding: 30px; text-align: center; color: var(--text-secondary);">No jobs in queue. Drop a video file into ~/Downloads/ to start.</td></tr>';
                    return;
                }

                tbody.innerHTML = jobs.map(job => {
                    const statusColors = {
                        'queued': '#3498db',
                        'transcribing': '#f39c12',
                        'completed': '#2ecc71',
                        'failed': '#e74c3c',
                    };
                    const statusColor = statusColors[job.status] || '#999';
                    const pathDisplay = job.absolute_srt_path 
                        ? `<code style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--success-color); background: #000; padding: 4px 8px; border-radius: 4px; word-break: break-all; cursor: pointer;" onclick="navigator.clipboard.writeText('${job.absolute_srt_path.replace(/'/g, "\\'")}'). then(() => this.style.color='#f39c12')" title="Click to copy">${job.absolute_srt_path}</code>`
                        : (job.error_message ? `<span style="color: #e74c3c; font-size: 0.8rem;">${job.error_message.substring(0, 80)}...</span>` : '<span style="color: var(--text-secondary);">—</span>');
                    const timeDisplay = job.completed_at 
                        ? new Date(job.completed_at).toLocaleString() 
                        : (job.created_at ? new Date(job.created_at).toLocaleString() : '—');
                    return `<tr style="border-top: 1px solid rgba(255,255,255,0.05);">
                        <td style="padding: 12px 15px; font-weight: 500;">${job.filename}</td>
                        <td style="padding: 12px 15px; text-align: center;"><span style="padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; background: ${statusColor}22; color: ${statusColor};">${job.status}</span></td>
                        <td style="padding: 12px 15px;">${pathDisplay}</td>
                        <td style="padding: 12px 15px; text-align: right; font-size: 0.8rem; color: var(--text-secondary);">${timeDisplay}</td>
                    </tr>`;
                }).join('');

            } catch (err) {
                console.error('Watcher refresh error:', err);
            }
        }

        async function toggleWatcherPause() {
            try {
                const btn = document.getElementById('watcherPauseBtn');
                const isPaused = btn.textContent.includes('Resume');
                await fetch(isPaused ? '/watcher/resume' : '/watcher/pause', { method: 'POST' });
                setTimeout(refreshWatcherQueue, 500);
            } catch (err) { console.error(err); }
        }

        async function retryFailedJobs() {
            try {
                const res = await fetch('/watcher/retry', { method: 'POST' });
                const data = await res.json();
                alert(`Retried ${data.count} failed job(s).`);
                refreshWatcherQueue();
            } catch (err) { console.error(err); }
        }

        // Collapsible Advanced Settings toggler
        const trigger = document.getElementById('settingsTrigger');
        const content = document.getElementById('settingsContent');
        const chevron = document.getElementById('triggerChevron');
        
        if (trigger && content) {
            trigger.addEventListener('click', () => {
                content.classList.toggle('open');
                chevron.textContent = content.classList.contains('open') ? '▲' : '▼';
            });
        }

        // File selection label updates helper
        function setupFileInput(inputId, wrapperId, filenameId) {
            const input = document.getElementById(inputId);
            const wrapper = document.getElementById(wrapperId);
            const filenameDiv = document.getElementById(filenameId);
            
            if (!input || !wrapper || !filenameDiv) return;
            
            input.addEventListener('change', (e) => {
                if (input.files.length > 0) {
                    filenameDiv.textContent = "Selected: " + input.files[0].name;
                    filenameDiv.style.display = 'block';
                    wrapper.style.borderColor = 'var(--success-color)';
                } else {
                    filenameDiv.style.display = 'none';
                    wrapper.style.borderColor = 'rgba(99, 102, 241, 0.3)';
                }
            });
            
            // Drag and drop event listeners
            ['dragenter', 'dragover'].forEach(eventName => {
                wrapper.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    wrapper.classList.add('dragover');
                }, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                wrapper.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    wrapper.classList.remove('dragover');
                }, false);
            });
            
            wrapper.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;
                if (files.length > 0) {
                    input.files = files;
                    filenameDiv.textContent = "Selected: " + files[0].name;
                    filenameDiv.style.display = 'block';
                    wrapper.style.borderColor = 'var(--success-color)';
                }
            });
        }
        
        setupFileInput('video', 'videoWrapper', 'videoFilename');
        setupFileInput('transcript', 'transcriptWrapper', 'transcriptFilename');
        setupFileInput('slides', 'slidesWrapper', 'slidesFilename');
        setupFileInput('asrFile', 'asrFileWrapper', 'asrFilename');
        
        // Tab 1 Form submission (Notes Generation)
        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const videoFile = document.getElementById('video').files[0];
            const transcriptFile = document.getElementById('transcript').files[0];
            
            if (!videoFile && !transcriptFile) {
                alert('Please upload either a lecture video or a transcript file to proceed.');
                return;
            }
            
            const formData = new FormData();
            if (videoFile) {
                formData.append('video', videoFile);
            }
            if (transcriptFile) {
                formData.append('transcript', transcriptFile);
            }
            
            const slidesFile = document.getElementById('slides').files[0];
            if (slidesFile) {
                formData.append('slides', slidesFile);
            }
            
            formData.append('language', document.getElementById('language').value);
            
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Uploading to Local Workspace...';
            
            try {
                // Reset stages UI
                document.querySelectorAll('.step-node').forEach(node => {
                    node.className = 'step-node';
                });
                document.getElementById('consoleLog').textContent = "Uploading assets to workspace...";
                document.getElementById('downloadLink').style.display = 'none';
                
                const response = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Upload failed');
                }
                
                const data = await response.json();
                currentLectureId = data.lecture_id;
                
                // Show status box
                document.getElementById('statusBox').classList.add('active');
                
                // Reset submit button state
                submitBtn.textContent = 'Generating Notes...';
                
                // Poll for status and logs
                clearInterval(statusInterval);
                clearInterval(logsInterval);
                statusInterval = setInterval(checkStatus, 2000);
                logsInterval = setInterval(checkLogs, 2000);
                
                checkStatus();
                checkLogs();
                
            } catch (error) {
                alert('Workspace error: ' + error.message);
                submitBtn.disabled = false;
                submitBtn.textContent = 'Generate Lecture Notes';
            }
        });

        // Tab 2 Form submission (ASR-Only Transcription)
        document.getElementById('asrForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('file', document.getElementById('asrFile').files[0]);
            formData.append('language', document.getElementById('asrLanguage').value);
            
            const asrSubmitBtn = document.getElementById('asrSubmitBtn');
            asrSubmitBtn.disabled = true;
            asrSubmitBtn.textContent = 'Uploading File to GPU Server...';
            
            try {
                document.getElementById('asrConsoleLog').textContent = "Uploading audio/video track...";
                document.getElementById('asrDownloadSrtLink').style.display = 'none';
                document.getElementById('asrDownloadTxtLink').style.display = 'none';
                document.getElementById('asrFilePathContainer').style.display = 'none';
                
                const response = await fetch('/transcribe', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'ASR submission failed');
                }
                
                const data = await response.json();
                currentAsrLectureId = data.lecture_id;
                
                // Show status box
                document.getElementById('asrStatusBox').classList.add('active');
                
                // Reset submit button state
                asrSubmitBtn.textContent = 'Transcribing Speech...';
                
                // Poll for status and logs
                clearInterval(asrStatusInterval);
                clearInterval(asrLogsInterval);
                asrStatusInterval = setInterval(checkAsrStatus, 2000);
                asrLogsInterval = setInterval(checkAsrLogs, 2000);
                
                checkAsrStatus();
                checkAsrLogs();
                
            } catch (error) {
                alert('ASR Error: ' + error.message);
                asrSubmitBtn.disabled = false;
                asrSubmitBtn.textContent = 'Start Local Transcription';
            }
        });
        
        async function checkStatus() {
            if (!currentLectureId) return;
            
            try {
                const response = await fetch(`/status/${currentLectureId}`);
                if (!response.ok) return;
                const data = await response.json();
                
                const badge = document.getElementById('statusBadge');
                const progressFill = document.getElementById('progressFill');
                const progressText = document.getElementById('progressText');
                const downloadLink = document.getElementById('downloadLink');
                
                badge.textContent = data.status;
                badge.className = 'status-badge status-' + data.status;
                progressText.textContent = data.progress;
                
                if (data.status === 'processing') {
                    // Use real progress if available, otherwise estimate based on log content
                    if (data.asr_percent && data.asr_percent > 0) {
                        progressFill.style.width = Math.min(data.asr_percent, 95) + '%';
                    } else {
                        progressFill.style.width = '70%';
                    }
                    document.getElementById('stopPipelineBtn').classList.add('active');
                } else if (data.status === 'completed') {
                    progressFill.style.width = '100%';
                    downloadLink.href = '/download/' + currentLectureId;
                    downloadLink.style.display = 'block';
                    clearInterval(statusInterval);
                    clearInterval(logsInterval);
                    checkLogs(); // One last fetch
                    
                    document.getElementById('consoleStatus').textContent = "Idle";
                    document.getElementById('consoleStatus').style.color = 'var(--success-color)';
                    document.getElementById('submitBtn').disabled = false;
                    document.getElementById('submitBtn').textContent = 'Process Another Lecture';
                    document.getElementById('stopPipelineBtn').classList.remove('active');
                } else if (data.status === 'failed') {
                    progressFill.style.width = '0%';
                    progressText.textContent = 'Failed: ' + (data.error_message || 'Unknown error');
                    clearInterval(statusInterval);
                    clearInterval(logsInterval);
                    checkLogs();
                    
                    document.getElementById('consoleStatus').textContent = "Failed";
                    document.getElementById('consoleStatus').style.color = 'var(--error-color)';
                    document.getElementById('submitBtn').disabled = false;
                    document.getElementById('submitBtn').textContent = 'Retry Generation';
                    document.getElementById('stopPipelineBtn').classList.remove('active');
                } else if (data.status === 'cancelled') {
                    progressFill.style.width = '0%';
                    progressText.textContent = 'Pipeline was stopped by user.';
                    clearInterval(statusInterval);
                    clearInterval(logsInterval);
                    
                    document.getElementById('consoleStatus').textContent = "Stopped";
                    document.getElementById('consoleStatus').style.color = '#fb923c';
                    document.getElementById('submitBtn').disabled = false;
                    document.getElementById('submitBtn').textContent = 'Generate Lecture Notes';
                    document.getElementById('stopPipelineBtn').classList.remove('active');
                }
                
            } catch (error) {
                console.error('Status check failed:', error);
            }
        }
        
        async function checkLogs() {
            if (!currentLectureId) return;
            
            try {
                const response = await fetch(`/logs/${currentLectureId}`);
                if (!response.ok) return;
                const data = await response.json();
                
                const consoleLog = document.getElementById('consoleLog');
                consoleLog.textContent = data.logs || "Loading logs...";
                
                // Auto scroll console to bottom
                consoleLog.scrollTop = consoleLog.scrollHeight;
                
                // Parse log content to highlight visual stage checkpoints dynamically
                const logText = data.logs || "";
                
                const hasASR = logText.includes("mlx-qwen3-asr") || logText.includes("transcribe_lecture.py") || logText.includes("transcription");
                const usingSoundScribeFallback = logText.includes("[FALLBACK]") || logText.includes("SoundScribe Agent CLI");
                const asrFinished = logText.includes("Successfully loaded auto-generated local transcript") || logText.includes("Loaded transcript") || logText.includes("Success via SoundScribe fallback");
                const hasFrames = logText.includes("Node: frame-extraction") || logText.includes("extracting frames");
                const framesFinished = logText.includes("extracted") && logText.includes("manifest");
                const hasMapping = logText.includes("concept-mapper") || logText.includes("concept_block_map");
                const mappingFinished = logText.includes("Mapping completed") || logText.includes("Saving concept_block_map");
                const hasComposition = logText.includes("note-composition") || logText.includes("generate_docx.py") || logText.includes("composition");
                const compositionFinished = logText.includes("Saved notes to") || logText.includes("Composition complete");
                const hasAudit = logText.includes("audit") || logText.includes("Gate");
                const auditFinished =
                    /all\\s+22\\s+gates\\s+passed/i.test(logText) ||
                    /all\\s+gates\\s+passed/i.test(logText) ||
                    logText.includes("completed successfully");

                // Show/update SoundScribe fallback banner
                let fbBanner = document.getElementById('fallbackBanner');
                if (usingSoundScribeFallback) {
                    if (!fbBanner) {
                        fbBanner = document.createElement('div');
                        fbBanner.id = 'fallbackBanner';
                        fbBanner.style.cssText = 'margin:8px 0;padding:8px 14px;border-radius:8px;background:rgba(139,92,246,0.18);border:1px solid rgba(139,92,246,0.5);color:#c4b5fd;font-size:0.85rem;display:flex;align-items:center;gap:8px;';
                        fbBanner.innerHTML = '<span style="font-size:1.1em">⚡</span><span><strong>SoundScribe Fallback Active</strong> — Primary mlx-qwen3-asr failed; transcribing via SoundScribe Agent CLI (same Qwen3-ASR 1.7B model).</span>';
                        const consoleSection = document.getElementById('consoleLog')?.parentElement;
                        if (consoleSection) consoleSection.prepend(fbBanner);
                    }
                } else if (fbBanner) {
                    fbBanner.remove();
                }
                updateStepUI('stepASR', hasASR, asrFinished);
                updateStepUI('stepFrames', hasFrames, framesFinished);
                updateStepUI('stepMapping', hasMapping, mappingFinished);
                updateStepUI('stepComposition', hasComposition, compositionFinished);
                updateStepUI('stepAudit', hasAudit, auditFinished);
                
            } catch (error) {
                console.error('Logs retrieval failed:', error);
            }
        }

        async function checkAsrStatus() {
            if (!currentAsrLectureId) return;
            
            try {
                const response = await fetch(`/status_asr/${currentAsrLectureId}`);
                if (!response.ok) return;
                const data = await response.json();
                
                const badge = document.getElementById('asrStatusBadge');
                const progressFill = document.getElementById('asrProgressFill');
                const progressText = document.getElementById('asrProgressText');
                
                badge.textContent = data.status;
                badge.className = 'status-badge status-' + data.status;
                progressText.textContent = data.progress;
                
                if (data.status === 'processing') {
                    // Use real ASR percentage from backend
                    if (data.asr_percent && data.asr_percent > 0) {
                        progressFill.style.width = Math.min(data.asr_percent, 95) + '%';
                        progressText.textContent = data.progress + ` (${data.asr_percent.toFixed(1)}%)`;
                    } else {
                        progressFill.style.width = '5%';
                        progressText.textContent = data.progress || 'Initializing local GPU ASR...';
                    }
                    document.getElementById('stopAsrBtn').classList.add('active');
                } else if (data.status === 'completed') {
                    progressFill.style.width = '100%';
                    
                    const srtLink = document.getElementById('asrDownloadSrtLink');
                    const txtLink = document.getElementById('asrDownloadTxtLink');
                    
                    srtLink.href = `/download_asr/${currentAsrLectureId}/srt`;
                    txtLink.href = `/download_asr/${currentAsrLectureId}/txt`;
                    
                    srtLink.style.display = 'block';
                    txtLink.style.display = 'block';
                    
                    if (data.absolute_srt_path) {
                        const pathContainer = document.getElementById('asrFilePathContainer');
                        const pathText = document.getElementById('asrFilePathText');
                        pathText.textContent = data.absolute_srt_path;
                        pathContainer.style.display = 'block';
                    }
                    
                    clearInterval(asrStatusInterval);
                    clearInterval(asrLogsInterval);
                    checkAsrLogs(); // One last fetch
                    
                    document.getElementById('asrConsoleStatus').textContent = "Idle";
                    document.getElementById('asrConsoleStatus').style.color = 'var(--success-color)';
                    document.getElementById('asrSubmitBtn').disabled = false;
                    document.getElementById('asrSubmitBtn').textContent = 'Transcribe Another File';
                    document.getElementById('stopAsrBtn').classList.remove('active');
                } else if (data.status === 'failed') {
                    progressFill.style.width = '0%';
                    progressText.textContent = 'Failed: ' + (data.error_message || 'Unknown error');
                    clearInterval(asrStatusInterval);
                    clearInterval(asrLogsInterval);
                    checkAsrLogs();
                    
                    document.getElementById('asrConsoleStatus').textContent = "Failed";
                    document.getElementById('asrConsoleStatus').style.color = 'var(--error-color)';
                    document.getElementById('asrSubmitBtn').disabled = false;
                    document.getElementById('asrSubmitBtn').textContent = 'Retry Transcription';
                    document.getElementById('stopAsrBtn').classList.remove('active');
                } else if (data.status === 'cancelled') {
                    progressFill.style.width = '0%';
                    progressText.textContent = 'Transcription was stopped by user.';
                    clearInterval(asrStatusInterval);
                    clearInterval(asrLogsInterval);
                    
                    document.getElementById('asrConsoleStatus').textContent = "Stopped";
                    document.getElementById('asrConsoleStatus').style.color = '#fb923c';
                    document.getElementById('asrSubmitBtn').disabled = false;
                    document.getElementById('asrSubmitBtn').textContent = 'Start Local Transcription';
                    document.getElementById('stopAsrBtn').classList.remove('active');
                }
                
            } catch (error) {
                console.error('ASR status check failed:', error);
            }
        }
        
        async function checkAsrLogs() {
            if (!currentAsrLectureId) return;
            
            try {
                const response = await fetch(`/logs_asr/${currentAsrLectureId}`);
                if (!response.ok) return;
                const data = await response.json();
                
                const consoleLog = document.getElementById('asrConsoleLog');
                consoleLog.textContent = data.logs || "Loading logs...";
                consoleLog.scrollTop = consoleLog.scrollHeight;
                
            } catch (error) {
                console.error('ASR logs retrieval failed:', error);
            }
        }
        
        function updateStepUI(stepId, isActive, isCompleted) {
            const el = document.getElementById(stepId);
            if (!el) return;
            if (isCompleted) {
                el.className = 'step-node completed';
            } else if (isActive) {
                el.className = 'step-node active';
            } else {
                el.className = 'step-node';
            }
        }

        // Cancel/Stop functions
        async function cancelAsrJob() {
            if (!currentAsrLectureId) return;
            const stopBtn = document.getElementById('stopAsrBtn');
            stopBtn.textContent = 'Stopping...';
            stopBtn.style.opacity = '0.6';
            stopBtn.style.pointerEvents = 'none';
            try {
                const response = await fetch(`/cancel_asr/${currentAsrLectureId}`, { method: 'POST' });
                if (response.ok) {
                    clearInterval(asrStatusInterval);
                    clearInterval(asrLogsInterval);
                    document.getElementById('asrProgressFill').style.width = '0%';
                    document.getElementById('asrProgressText').textContent = 'Transcription was stopped by user.';
                    document.getElementById('asrStatusBadge').textContent = 'cancelled';
                    document.getElementById('asrStatusBadge').className = 'status-badge status-cancelled';
                    document.getElementById('asrConsoleStatus').textContent = 'Stopped';
                    document.getElementById('asrConsoleStatus').style.color = '#fb923c';
                    document.getElementById('asrSubmitBtn').disabled = false;
                    document.getElementById('asrSubmitBtn').textContent = 'Start Local Transcription';
                    stopBtn.classList.remove('active');
                } else {
                    const err = await response.json();
                    stopBtn.textContent = '\u23f9 Stop Transcription';
                    stopBtn.style.opacity = '1';
                    stopBtn.style.pointerEvents = 'auto';
                    console.error('Cancel failed:', err.detail);
                }
            } catch (e) {
                stopBtn.textContent = '\u23f9 Stop Transcription';
                stopBtn.style.opacity = '1';
                stopBtn.style.pointerEvents = 'auto';
                console.error('Cancel request failed:', e);
            }
        }

        async function cancelPipelineJob() {
            if (!currentLectureId) return;
            const stopBtn = document.getElementById('stopPipelineBtn');
            stopBtn.textContent = 'Stopping...';
            stopBtn.style.opacity = '0.6';
            stopBtn.style.pointerEvents = 'none';
            try {
                const response = await fetch(`/cancel/${currentLectureId}`, { method: 'POST' });
                if (response.ok) {
                    clearInterval(statusInterval);
                    clearInterval(logsInterval);
                    document.getElementById('progressFill').style.width = '0%';
                    document.getElementById('progressText').textContent = 'Pipeline was stopped by user.';
                    document.getElementById('statusBadge').textContent = 'cancelled';
                    document.getElementById('statusBadge').className = 'status-badge status-cancelled';
                    document.getElementById('consoleStatus').textContent = 'Stopped';
                    document.getElementById('consoleStatus').style.color = '#fb923c';
                    document.getElementById('submitBtn').disabled = false;
                    document.getElementById('submitBtn').textContent = 'Generate Lecture Notes';
                    stopBtn.classList.remove('active');
                } else {
                    const err = await response.json();
                    stopBtn.textContent = '\u23f9 Stop Pipeline';
                    stopBtn.style.opacity = '1';
                    stopBtn.style.pointerEvents = 'auto';
                    console.error('Cancel failed:', err.detail);
                }
            } catch (e) {
                stopBtn.textContent = '\u23f9 Stop Pipeline';
                stopBtn.style.opacity = '1';
                stopBtn.style.pointerEvents = 'auto';
                console.error('Cancel request failed:', e);
            }
        }
    </script>
</body>
</html>
"""


@app.post("/process")
async def process_lecture(
    background_tasks: BackgroundTasks,
    video: Optional[UploadFile] = File(None),
    transcript: Optional[UploadFile] = File(None),
    slides: Optional[UploadFile] = File(None),
    language: Optional[str] = Form("hi")
):
    """
    Process a lecture upload.
    
    Args:
        video: Uploaded video file (required)
        transcript: Uploaded transcript file (optional)
        slides: Optional uploaded PDF slides file
        language: Selected language code for local transcription ("hi", "en", "auto")
        background_tasks: FastAPI background tasks
        
    Returns:
        Lecture ID for status tracking
    """
    # Check if another pipeline run is active
    lock_file = PROJECT_ROOT / "logs" / "pipeline.lock"
    if lock_file.exists():
        try:
            with open(lock_file, "r") as f:
                old_pid = int(f.read().strip())
            
            def is_pid_running(pid: int) -> bool:
                if pid <= 0:
                    return False
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    return False
                except PermissionError:
                    return True
                except OSError:
                    return False
                
                try:
                    output = subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True, stderr=subprocess.DEVNULL)
                    return "python" in output.lower() and "orchestrator" in output.lower()
                except Exception:
                    return True
                
            if is_pid_running(old_pid):
                raise HTTPException(
                    status_code=503,
                    detail="The local pipeline is currently busy processing another lecture. Please wait until it completes."
                )
        except HTTPException:
            raise
        except Exception:
            pass

    # Generate unique lecture ID
    lecture_id = str(uuid.uuid4())[:8]
    
    # Validate uploaded files first
    if video and video.filename:
        await validate_uploaded_file(video, 'video')
    if transcript and transcript.filename:
        await validate_uploaded_file(transcript, 'transcript')
    if slides and slides.filename:
        await validate_uploaded_file(slides, 'slides')
    
    # Clear old manifests in root to force dynamic mapping for the new run.
    # Keep generated media files intact; resetting manifests prevents stale cross-run references.
    for manifest_name in [
        "concept_block_map.json",
        "frame_manifest.json",
        "slide_manifest.json",
        "reference_manifest.json",
        "embedded_manifest.json",
        "inserted_images.json",
    ]:
        p = PROJECT_ROOT / manifest_name
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    # Save uploaded files with STANDARD NAMES that orchestrator expects
    video_path_str = ""
    if video and video.filename:
        video_ext = Path(video.filename).suffix or ".mp4"
        video_path = UPLOAD_DIR / f"LECTURE{video_ext}"
        
        # Backup any existing files first
        if video_path.exists():
            backup_dir = PROJECT_ROOT / "backups"
            backup_dir.mkdir(exist_ok=True)
            backup_video = backup_dir / f"LECTURE_backup_{lecture_id}{video_ext}"
            try:
                shutil.move(str(video_path), str(backup_video))
            except Exception as e:
                import sys
                print(f"Warning: Failed to backup video file: {e}", file=sys.stderr)
            
        await save_upload_file_async(video, video_path)
        video_path_str = str(video_path)
    else:
        # If no video is uploaded, clean up any existing video file in lecture-input
        # to ensure the orchestrator doesn't pick it up as an active input.
        for v_file in UPLOAD_DIR.glob("LECTURE.*"):
            try:
                v_file.unlink()
            except Exception:
                pass
        for v_file in UPLOAD_DIR.glob("lecture.*"):
            try:
                v_file.unlink()
            except Exception:
                pass

    transcript_path_str = ""
    # Handle transcript
    if transcript and transcript.filename:
        transcript_ext = Path(transcript.filename).suffix or ".srt"
        transcript_path = UPLOAD_DIR / f"transcript{transcript_ext}"
        
        if transcript_path.exists():
            backup_dir = PROJECT_ROOT / "backups"
            backup_dir.mkdir(exist_ok=True)
            backup_transcript = backup_dir / f"transcript_backup_{lecture_id}{transcript_ext}"
            try:
                shutil.move(str(transcript_path), str(backup_transcript))
            except Exception as e:
                import sys
                print(f"Warning: Failed to backup transcript file: {e}", file=sys.stderr)
            
        await save_upload_file_async(transcript, transcript_path)
        transcript_path_str = str(transcript_path)
    else:
        # If no transcript is uploaded, clean up any existing transcript file in lecture-input
        # to ensure the orchestrator triggers auto-transcription
        for t_file in UPLOAD_DIR.glob("transcript.*"):
            try:
                t_file.unlink()
            except Exception:
                pass
        for t_file in UPLOAD_DIR.glob("TRANSCRIPT.*"):
            try:
                t_file.unlink()
            except Exception:
                pass
                
    # Handle slides saving/clearing
    slides_path = UPLOAD_DIR / "SLIDES.pdf"
    if slides_path.exists():
        backup_dir = PROJECT_ROOT / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_slides = backup_dir / f"SLIDES_backup_{lecture_id}.pdf"
        try:
            shutil.move(str(slides_path), str(backup_slides))
        except Exception as e:
            import sys
            print(f"Warning: Failed to backup slides file: {e}", file=sys.stderr)
        
    if slides and slides.filename:
        await save_upload_file_async(slides, slides_path)
    else:
        # Clean up any existing slide file if none uploaded
        if slides_path.exists():
            try:
                slides_path.unlink()
            except Exception:
                pass
            
    # Initialize status
    initial_status = {
        "lecture_id": lecture_id,
        "status": "pending",
        "progress": "Files uploaded, starting background execution",
        "started_at": datetime.now().isoformat()
    }
    
    status_file = STATUS_DIR / f"{lecture_id}.json"
    save_status_atomic(status_file, initial_status, indent=2)
        
    # Queue background processing
    background_tasks.add_task(
        run_pipeline, 
        lecture_id, 
        video_path_str, 
        transcript_path_str, 
        language or "hi"
    )
    
    return {
        "lecture_id": lecture_id,
        "status": "pending",
        "message": "Upload successful. Processing started."
    }


@app.get("/status/{lecture_id}")
async def get_status(lecture_id: str):
    """Get processing status for a lecture, enriched with pipeline progress."""
    if not re.match(r'^[a-f0-9]{8}$', lecture_id):
        raise HTTPException(status_code=400, detail="Invalid lecture ID format")
        
    status_file = STATUS_DIR / f"{lecture_id}.json"
    
    if not status_file.exists():
        raise HTTPException(status_code=404, detail="Lecture not found")
        
    with open(status_file, "r") as f:
        status = json.load(f)
    
    # Enrich with real-time progress from log file during processing
    if status.get("status") == "processing":
        log_file = LOGS_DIR / f"pipeline_{lecture_id}.log"
        progress_data = parse_asr_progress_from_log(log_file)
        if progress_data["asr_percent"] > 0:
            status["asr_percent"] = progress_data["asr_percent"]
            if progress_data["chunk_info"]:
                status["progress"] = f"ASR: {progress_data['chunk_info']}"
        
    return status


@app.get("/logs/{lecture_id}")
async def get_logs(lecture_id: str):
    """Get live logs for a specific lecture reconstruction run."""
    if not re.match(r'^[a-f0-9]{8}$', lecture_id):
        raise HTTPException(status_code=400, detail="Invalid lecture ID format")
        
    log_file = LOGS_DIR / f"pipeline_{lecture_id}.log"
    if not log_file.exists():
        # Fallback to shared general logs if specific log doesn't exist yet
        fallback_log = LOGS_DIR / "pipeline.log"
        if fallback_log.exists():
            try:
                with open(fallback_log, "r", encoding="utf-8") as f:
                    content = f.read()
                # Return last 3000 chars of general log
                return {"logs": "[General Console Logs]:\n" + content[-3000:]}
            except Exception:
                pass
        return {"logs": "Initializing workspace logs..."}
        
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        return {"logs": content}
    except Exception as e:
        return {"logs": f"Error reading logs: {str(e)}"}


@app.get("/download/{lecture_id}")
async def download_notes(lecture_id: str):
    """Download generated notes for a lecture."""
    if not re.match(r'^[a-f0-9]{8}$', lecture_id):
        raise HTTPException(status_code=400, detail="Invalid lecture ID format")
        
    notes_file = OUTPUT_DIR / f"{lecture_id}_NOTES.docx"
    
    if not notes_file.exists():
        raise HTTPException(status_code=404, detail="Notes file not found")
        
    return FileResponse(
        str(notes_file),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{lecture_id}_NOTES.docx"
    )


def run_asr_only(lecture_id: str, input_path: str, language: str = "hi"):
    """Background task to run ASR-only transcription."""
    status_file = STATUS_DIR / f"asr_{lecture_id}.json"
    log_file_path = LOGS_DIR / f"asr_{lecture_id}.log"
    asr_output_dir = UPLOAD_DIR / f"asr_{lecture_id}"
    
    try:
        # Update status to processing
        status = {
            "lecture_id": lecture_id,
            "status": "processing",
            "progress": "Initializing local GPU ASR...",
            "started_at": datetime.now().isoformat()
        }
        save_status_atomic(status_file, status)
            
        import sys
        # ── Primary: mlx-qwen3-asr (Apple Silicon GPU) ──────────────────────
        # If primary fails, transcribe_lecture.py will automatically retry via
        # the SoundScribe Agent CLI fallback.  Both tiers write to asr_output_dir.
        env = os.environ.copy()
        # Ensure the SoundScribe workspace env var is always forwarded
        env.setdefault(
            "SOUNDSCRIBE_AGENT_WORKSPACE",
            "/Users/tejasmahadik/Downloads/Transcription-SoundScribe"
        )
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                [
                    sys.executable, 
                    "scripts/transcribe_lecture.py", 
                    "--input", input_path, 
                    "--language", language,
                    "--output-dir", str(asr_output_dir)
                ],
                cwd=str(PROJECT_ROOT),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True,
            )
            
            # Track process for cancel support
            asr_key = f"asr_{lecture_id}"
            active_processes[asr_key] = process
            
            try:
                # Match the orchestrator's ASR timeout default so long videos are not killed early.
                timeout = int(os.environ.get("ASR_TIMEOUT", DEFAULT_ASR_TIMEOUT_SECONDS))
                retcode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                terminate_process_tree(process)
                retcode = -9
                log_file.write(f"\n[TIMEOUT] ASR run exceeded {timeout // 60} minutes and was terminated.\n")
            finally:
                active_processes.pop(asr_key, None)
        
        # Clean up uploaded raw file
        if os.path.exists(input_path) and "asr_temp_" in input_path:
            try:
                os.remove(input_path)
            except Exception:
                pass
                
        if retcode == 0:
            if (asr_output_dir / "transcript.txt").exists():
                # Detect whether the fallback was used (check log for marker)
                used_fallback = False
                if log_file_path.exists():
                    try:
                        with open(log_file_path, "r", encoding="utf-8") as _lf:
                            _log_content = _lf.read()
                        used_fallback = "[FALLBACK]" in _log_content or "SoundScribe fallback" in _log_content
                    except Exception:
                        pass

                if used_fallback:
                    progress_msg = "Transcription completed via SoundScribe fallback (Qwen3-ASR)!"
                else:
                    progress_msg = "Transcription completed successfully (mlx-qwen3-asr primary)!"

                status.update({
                    "status": "completed",
                    "progress": progress_msg,
                    "used_fallback": used_fallback,
                    "completed_at": datetime.now().isoformat(),
                    "absolute_srt_path": str((asr_output_dir / "transcript.srt").resolve()),
                    "absolute_txt_path": str((asr_output_dir / "transcript.txt").resolve())
                })
            else:
                status.update({
                    "status": "failed",
                    "progress": "ASR finished but output files were not found",
                    "error_message": "Output files not generated"
                })
        elif retcode == -9:
            status.update({
                "status": "failed",
                "progress": f"ASR timed out (>{timeout // 60} minutes)",
                "error_message": "Timeout expired"
            })
        else:
            err_msg = "ASR process failed"
            if log_file_path.exists():
                try:
                    with open(log_file_path, "r", encoding="utf-8") as lf:
                        lines = lf.readlines()
                        err_msg = "".join(lines[-5:]).strip()[:500]
                except Exception:
                    pass
            status.update({
                "status": "failed",
                "progress": "ASR execution failed",
                "error_message": err_msg if err_msg else f"Process exited with code {retcode}"
            })
            
    except Exception as e:
        status = {
            "lecture_id": lecture_id,
            "status": "failed",
            "progress": "Unexpected error",
            "error_message": str(e)
        }
        
    save_status_atomic(status_file, status, indent=2)


@app.post("/transcribe")
async def transcribe_only(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Optional[str] = Form("hi")
):
    """ASR-only transcription endpoint."""
    lecture_id = str(uuid.uuid4())[:8]
    
    # Save file temporarily
    file_ext = Path(file.filename).suffix or ".mp4"
    temp_path = UPLOAD_DIR / f"asr_temp_{lecture_id}{file_ext}"
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    # Initialize status
    initial_status = {
        "lecture_id": lecture_id,
        "status": "pending",
        "progress": "File uploaded, starting local transcription...",
        "started_at": datetime.now().isoformat()
    }
    
    status_file = STATUS_DIR / f"asr_{lecture_id}.json"
    save_status_atomic(status_file, initial_status, indent=2)
        
    background_tasks.add_task(
        run_asr_only,
        lecture_id,
        str(temp_path),
        language or "hi"
    )
    
    return {
        "lecture_id": lecture_id,
        "status": "pending",
        "message": "Upload successful. Transcription started."
    }


@app.get("/status_asr/{lecture_id}")
async def get_status_asr(lecture_id: str):
    """Get status for ASR-only transcription, enriched with real-time progress percentage."""
    if not re.match(r'^[a-f0-9]{8}$', lecture_id):
        raise HTTPException(status_code=400, detail="Invalid lecture ID format")
        
    status_file = STATUS_DIR / f"asr_{lecture_id}.json"
    if not status_file.exists():
        raise HTTPException(status_code=404, detail="Transcription job not found")
        
    with open(status_file, "r") as f:
        status = json.load(f)
    
    # Enrich with real-time progress from log file
    if status.get("status") == "processing":
        log_file = LOGS_DIR / f"asr_{lecture_id}.log"
        progress_data = parse_asr_progress_from_log(log_file)
        status["asr_percent"] = progress_data["asr_percent"]
        if progress_data["chunk_info"]:
            status["progress"] = progress_data["chunk_info"]
    
    return status


@app.get("/logs_asr/{lecture_id}")
async def get_logs_asr(lecture_id: str):
    """Get logs for ASR-only transcription."""
    if not re.match(r'^[a-f0-9]{8}$', lecture_id):
        raise HTTPException(status_code=400, detail="Invalid lecture ID format")
        
    log_file = LOGS_DIR / f"asr_{lecture_id}.log"
    if not log_file.exists():
        return {"logs": "Initializing transcriber logs..."}
        
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        return {"logs": content}
    except Exception as e:
        return {"logs": f"Error reading logs: {str(e)}"}


@app.get("/download_asr/{lecture_id}/{fmt}")
async def download_asr_file(lecture_id: str, fmt: str):
    """Download transcribed SRT or TXT files."""
    if not re.match(r'^[a-f0-9]{8}$', lecture_id):
        raise HTTPException(status_code=400, detail="Invalid lecture ID format")
    if fmt not in ("srt", "txt"):
        raise HTTPException(status_code=400, detail="Invalid format. Supported: srt, txt")
        
    file_path = UPLOAD_DIR / f"asr_{lecture_id}" / f"transcript.{fmt}"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    media_types = {
        "srt": "application/x-subrip",
        "txt": "text/plain"
    }
    
    return FileResponse(
        str(file_path),
        media_type=media_types[fmt],
        filename=f"transcript_{lecture_id}.{fmt}"
    )

@app.post("/cancel_asr/{lecture_id}")
async def cancel_asr(lecture_id: str):
    """Cancel a running ASR-only transcription job."""
    if not re.match(r'^[a-f0-9]{8}$', lecture_id):
        raise HTTPException(status_code=400, detail="Invalid lecture ID format")

    asr_key = f"asr_{lecture_id}"
    process = active_processes.get(asr_key)

    if process is None or process.poll() is not None:
        raise HTTPException(status_code=404, detail="No active ASR job found for this ID")

    terminate_process_tree(process)
    active_processes.pop(asr_key, None)

    # Update status to cancelled
    status_file = STATUS_DIR / f"asr_{lecture_id}.json"
    cancel_status = {
        "lecture_id": lecture_id,
        "status": "cancelled",
        "progress": "Transcription was stopped by user.",
        "completed_at": datetime.now().isoformat()
    }
    save_status_atomic(status_file, cancel_status, indent=2)

    # Clean up temp file
    for temp in UPLOAD_DIR.glob(f"asr_temp_{lecture_id}*"):
        try:
            temp.unlink()
        except Exception:
            pass

    return {"status": "cancelled", "message": "ASR job stopped successfully."}


@app.post("/cancel/{lecture_id}")
async def cancel_pipeline(lecture_id: str):
    """Cancel a running pipeline job."""
    if not re.match(r'^[a-f0-9]{8}$', lecture_id):
        raise HTTPException(status_code=400, detail="Invalid lecture ID format")

    process = active_processes.get(lecture_id)

    if process is None or process.poll() is not None:
        raise HTTPException(status_code=404, detail="No active pipeline job found for this ID")

    terminate_process_tree(process)
    active_processes.pop(lecture_id, None)

    # Clean up lock file
    lock_file = PROJECT_ROOT / "logs" / "pipeline.lock"
    if lock_file.exists():
        try:
            lock_file.unlink()
        except Exception:
            pass

    # Update status to cancelled
    status_file = STATUS_DIR / f"{lecture_id}.json"
    cancel_status = {
        "lecture_id": lecture_id,
        "status": "cancelled",
        "progress": "Pipeline was stopped by user.",
        "completed_at": datetime.now().isoformat()
    }
    save_status_atomic(status_file, cancel_status, indent=2)

    return {"status": "cancelled", "message": "Pipeline job stopped successfully."}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ── Watch Folder Dashboard API Endpoints ──────────────────────────────────────

WATCHER_HEARTBEAT = PROJECT_ROOT / "logs" / "asr_watcher_heartbeat.json"
WATCHER_DB = PROJECT_ROOT / "logs" / "asr_queue.db"
WATCHER_PAUSE_FLAG = PROJECT_ROOT / "logs" / "asr_watcher_paused.flag"


@app.get("/watcher/status")
async def watcher_status():
    """Get watcher daemon status from heartbeat file."""
    alive = False
    paused = False
    on_battery = False
    currently_transcribing = None
    stats = {}

    if WATCHER_HEARTBEAT.exists():
        try:
            with open(WATCHER_HEARTBEAT, "r") as f:
                data = json.load(f)
            from datetime import datetime as dt
            alive_at = dt.fromisoformat(data.get("alive_at", ""))
            age = (dt.now() - alive_at).total_seconds()
            alive = age < 60  # alive if heartbeat < 60 seconds old
            paused = data.get("paused", False)
            on_battery = data.get("on_battery", False)
            currently_transcribing = data.get("currently_transcribing")
            stats = data.get("stats", {})
        except Exception:
            pass

    return {
        "alive": alive,
        "paused": paused or WATCHER_PAUSE_FLAG.exists(),
        "on_battery": on_battery,
        "currently_transcribing": currently_transcribing,
        "stats": stats,
    }


@app.get("/watcher/queue")
async def watcher_queue():
    """Get all jobs from the watcher SQLite queue."""
    if not WATCHER_DB.exists():
        return []
    try:
        import sqlite3
        conn = sqlite3.connect(str(WATCHER_DB))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY id DESC LIMIT 100"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return [{"error": str(e)}]


@app.post("/watcher/retry")
async def watcher_retry():
    """Reset all failed watcher jobs to queued."""
    if not WATCHER_DB.exists():
        return {"count": 0}
    try:
        import sqlite3
        conn = sqlite3.connect(str(WATCHER_DB))
        cursor = conn.execute(
            "UPDATE jobs SET status = 'queued', error_message = NULL, "
            "started_at = NULL, completed_at = NULL WHERE status = 'failed'"
        )
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/watcher/pause")
async def watcher_pause():
    """Pause the watcher daemon by creating a flag file."""
    WATCHER_PAUSE_FLAG.parent.mkdir(exist_ok=True)
    WATCHER_PAUSE_FLAG.touch()
    return {"status": "paused"}


@app.post("/watcher/resume")
async def watcher_resume():
    """Resume the watcher daemon by removing the flag file."""
    if WATCHER_PAUSE_FLAG.exists():
        WATCHER_PAUSE_FLAG.unlink()
    return {"status": "resumed"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

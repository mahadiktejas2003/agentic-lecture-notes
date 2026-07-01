#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import datetime
import subprocess
import logging
import shutil
import signal
from typing import TypedDict, Dict, List, Annotated

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler(sys.stderr)
    ]
)

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

# Graceful shutdown handler for cancel support
def _pipeline_sigterm_handler(signum, frame):
    """Clean up lock file on SIGTERM (sent by the cancel endpoint)."""
    lock_file = os.path.join("logs", "pipeline.lock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except Exception:
            pass
    logging.warning("[CANCELLED] Pipeline stopped by user.")
    sys.exit(130)

signal.signal(signal.SIGTERM, _pipeline_sigterm_handler)

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.audit import run_audit
from scripts.memory_store import store_run

def find_transcript_path() -> str:
    default_path = "lecture-input/transcript.srt"
    if os.path.exists(default_path):
        return default_path
    for name in ["transcript.txt", "transcript.vtt", "TRANSCRIPT.srt", "TRANSCRIPT.txt", "TRANSCRIPT.vtt"]:
        p = os.path.join("lecture-input", name)
        if os.path.exists(p):
            return p
    return default_path

def find_video_path() -> str:
    default_path = "lecture-input/LECTURE.mp4"
    if os.path.exists(default_path):
        return default_path
    for ext in ['.mp4', '.mkv', '.avi', '.webm', '.mov']:
        for name in ['LECTURE', 'video', 'lecture', 'VIDEO']:
            p = os.path.join("lecture-input", f"{name}{ext}")
            if os.path.exists(p):
                return p
    if os.path.exists("lecture-input"):
        for f in os.listdir("lecture-input"):
            if any(f.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.webm', '.mov']):
                return os.path.join("lecture-input", f)
    return default_path

def compute_run_fingerprint() -> str:
    import hashlib
    video_path = find_video_path()
    transcript_path = find_transcript_path()
    slides_path = "lecture-input/SLIDES.pdf"
    
    hasher = hashlib.sha256()
    for p in [video_path, transcript_path, slides_path]:
        if os.path.exists(p):
            try:
                stat = os.stat(p)
                meta = f"{p}:{stat.st_size}:{int(stat.st_mtime)}"
            except Exception:
                meta = f"{p}:error"
            hasher.update(meta.encode("utf-8"))
        else:
            hasher.update(f"{p}:not_exists".encode("utf-8"))
    return hasher.hexdigest()

def build_docx_metadata(docx_path: str) -> Dict[str, object]:
    metadata: Dict[str, object] = {"path": os.path.abspath(docx_path)}
    try:
        stat = os.stat(docx_path)
        metadata["size"] = stat.st_size
        metadata["mtime"] = int(stat.st_mtime)
    except OSError:
        metadata["size"] = None
        metadata["mtime"] = None
    return metadata

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
    
    # Check if the process is actually Python running our orchestrator to prevent false positives from recycled PIDs
    try:
        output = subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True, stderr=subprocess.DEVNULL)
        return "python" in output.lower() and "orchestrator" in output.lower()
    except Exception:
        # Fallback if ps command fails or returns weird output
        return True

class AgentState(TypedDict):
    status: str
    concept_map_path: str
    frame_manifest_path: str
    slide_manifest_path: str
    output_path: str
    failed_gate: int
    gate_results: Dict[str, bool]
    gate_retries: Dict[str, int]
    attempts: int
    short_note_path: str

# GATE MAPPING
GATE_MAPPING = {
    'Gate 1: Structural Integrity': 1,
    'Gate 2: Revision Box Placement': 2,
    'Gate 3: Chronological Flow': 3,
    'Gate 4: Content Completeness': 4,
    'Gate 5: Factual Accuracy': 5,
    'Gate 6: Image Integrity': 6,
    'Gate 7: Minimum Counts': 7,
    'Gate 8: Source Traceability': 8,
    'Gate 9: Slide Handling': 9,
    'Gate 10: Example Coverage': 10,
    'Gate 11: Visual Coverage': 11,
    'Gate 12: Exercise Content': 12,
    'Gate 13: Quote Quality': 13,
    'Gate 14: Meaningful Titles': 14,
    'Gate 15: Explanation Conciseness': 15,
    'Gate 16: Table Presence': 16,
    'Gate 17: Sequence Integrity': 17,
    'Gate 18: Exact Worked Examples': 18,
    'Gate 19: Friction Index Constraint': 19,
    'Gate 20: Transcript Coverage': 20,
    'Gate 21: English Enforcement': 21,
    'Gate 22: Styling and Highlighting Conformity': 22,
}

def log_abort(state: AgentState, reason: str):
    os.makedirs("agent_memory/failures", exist_ok=True)
    run_record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "aborted",
        "failed_gates": [f"Gate {state.get('failed_gate')}"],
        "reason": reason,
        "attempts": state.get("attempts", 0),
        "gate_retries": state.get("gate_retries", {})
    }
    filename = f"fail_abort_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(os.path.join("agent_memory/failures", filename), "w", encoding="utf-8") as f:
        json.dump(run_record, f, indent=2)
    logging.info(f"Abort failure log written to agent_memory/failures/{filename}")

def update_workspace_state(state: AgentState, stage_name: str, status_msg: str):
    import json, os, datetime
    
    lecture_title = "Unknown Lecture"
    if os.path.exists("concept_block_map.json"):
        try:
            with open("concept_block_map.json", "r", encoding="utf-8") as f:
                c_map = json.load(f)
                if isinstance(c_map, dict):
                    lecture_title = c_map.get("lecture_title") or lecture_title
                    blocks = c_map.get("blocks", [])
                    if lecture_title == "Unknown Lecture" and blocks:
                        lecture_title = blocks[0].get("lecture_title", blocks[0].get("title", lecture_title))
                elif c_map and isinstance(c_map, list) and len(c_map) > 0:
                    lecture_title = c_map[0].get("lecture_title", c_map[0].get("title", "Unknown Lecture"))
        except Exception:
            pass

    current_fingerprint = compute_run_fingerprint()
    audit_results = {}
    if os.path.exists("logs/last_run_audit.json"):
        try:
            with open("logs/last_run_audit.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data.get("_run_fingerprint") == current_fingerprint:
                    audit_results = data
        except Exception:
            pass

    failed_gates = []
    passed_count = 0
    for g_num, ok in audit_results.items():
        if g_num.startswith("_"):
            continue
        if not ok:
            failed_gates.append(f"Gate {g_num}")
        else:
            passed_count += 1

    last_archive = None
    if os.path.exists("notes-output"):
        try:
            archives = [
                f for f in os.listdir("notes-output")
                if f.startswith("LECTURE_NOTES_") and f.endswith(".docx")
            ]
            if archives:
                latest = max(
                    archives,
                    key=lambda f: os.path.getmtime(os.path.join("notes-output", f))
                )
                last_archive = os.path.join("notes-output", latest)
        except Exception:
            pass

    workspace_state = {
        "active_lecture": {
            "title": lecture_title,
            "video_path": find_video_path(),
            "transcript_path": find_transcript_path(),
            "run_fingerprint": compute_run_fingerprint(),
            "last_updated": datetime.datetime.now().isoformat()
        },
        "pipeline": {
            "current_stage": stage_name,
            "status_message": status_msg,
            "gate_retries": state.get("gate_retries", {}),
            "failed_gate": state.get("failed_gate", 0),
            "last_updated": datetime.datetime.now().isoformat()
        },
        "artifacts": {
            "concept_map": "concept_block_map.json",
            "frame_manifest": "frame_manifest.json",
            "slide_manifest": "slide_manifest.json",
            "notes_output": "notes-output/LECTURE_NOTES.docx",
            "notes_output_meta": build_docx_metadata("notes-output/LECTURE_NOTES.docx"),
            "short_note_output": state.get("short_note_path", ""),
            "last_archive": last_archive
        },
        "audit": {
            "score": passed_count,
            "failed_gates": failed_gates,
            "last_checked": datetime.datetime.now().isoformat()
        }
    }

    try:
        with open("workspace_state.json", "w", encoding="utf-8") as f:
            json.dump(workspace_state, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to write workspace_state.json: {e}")

# NODES
def content_mapper_node(state: AgentState) -> Dict:
    logging.info("=== [Node: content-mapper] Mapping concepts from transcript and slides ===")
    os.makedirs("notes-output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Helper functions for checking transcript completeness
    def get_transcript_end_time(path: str) -> float:
        if not os.path.exists(path):
            return 0.0
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            import re
            matches = re.findall(r'(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})', content)
            if not matches:
                return 0.0
            last_match = matches[-1]
            hours, minutes, seconds, millis = map(int, last_match)
            return hours * 3600 + minutes * 60 + seconds + millis / 1000.0
        except Exception:
            return 0.0

    def get_video_duration(path: str) -> float:
        if not os.path.exists(path):
            return 0.0
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(res.stdout.strip())
        except Exception as e:
            logging.warning(f"Failed to get video duration: {e}")
            return 0.0

    # 1. Check transcript validity and completeness
    transcript_path = find_transcript_path()
    video_path = find_video_path()
    
    has_valid_transcript = False
    transcript_content = ""
    
    if os.path.exists(transcript_path):
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_content = f.read()
        
        # Check basic length and check for TurboScribe truncation signatures
        is_turboscribe_truncated = any(sig in transcript_content.lower() for sig in ["longer than 30 minutes", "this transcript was truncated"])
        
        if len(transcript_content.strip()) >= 3000 and not is_turboscribe_truncated:
            # Check completeness against video duration
            v_duration = get_video_duration(video_path)
            t_end_time = get_transcript_end_time(transcript_path)
            
            if v_duration > 0 and t_end_time > 0:
                # If transcript ends earlier than 85% of the video duration, it is truncated
                if t_end_time < 0.85 * v_duration:
                    logging.warning(f"Transcript appears truncated: video is {v_duration:.1f}s, transcript ends at {t_end_time:.1f}s (ratio {t_end_time/v_duration:.2%}).")
                else:
                    has_valid_transcript = True
            else:
                # No video to check against, or parsing failed; assume transcript is fine if size is decent
                has_valid_transcript = True
        elif is_turboscribe_truncated:
            logging.warning("Transcript contains TurboScribe truncation signatures. Marking as truncated.")
                
    if not has_valid_transcript:
        if os.path.exists(video_path):
            logging.info(f"Transcript is missing or truncated. Triggering local GPU-accelerated transcription using Qwen3-ASR via mlx-audio on '{video_path}'...")
            try:
                python_exe = sys.executable
                transcribe_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcribe_lecture.py")
                asr_lang = os.getenv("ASR_LANGUAGE", "hi")
                cmd = [python_exe, transcribe_script, "--input", video_path, "--language", asr_lang]
                logging.info(f"Running command: {' '.join(cmd)}")
                
                # Run the transcription with a generous timeout (default 2 hours)
                asr_timeout = int(os.getenv("ASR_TIMEOUT", "7200"))
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=asr_timeout)
                logging.info(f"Local transcription finished successfully: {result.stdout.strip()}")
                
                # Reload transcript
                transcript_path = find_transcript_path()
                if os.path.exists(transcript_path):
                    with open(transcript_path, "r", encoding="utf-8") as f:
                        transcript_content = f.read()
                    if len(transcript_content.strip()) >= 3000:
                        has_valid_transcript = True
                        logging.info("Successfully loaded auto-generated local transcript.")
                    else:
                        logging.error(f"Generated transcript is still too short ({len(transcript_content)} chars).")
            except Exception as e:
                logging.error(f"Auto-transcription failed: {e}")
        else:
            logging.error(f"Lecture video not found at '{video_path}'. Cannot perform auto-transcription.")
            
    if not has_valid_transcript:
        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Error: Transcript file not found at '{transcript_path}' and auto-transcription was not possible.")
        else:
            raise ValueError(f"Error: Transcript at '{transcript_path}' is missing or too short ({len(transcript_content)} chars) and auto-transcription failed.")
        
    # Run process_slides.py first so slide_manifest.json and reference_manifest.json are available
    logging.info("Running process_slides.py...")
    try:
        subprocess.run([sys.executable, "scripts/process_slides.py"], check=True)
        logging.info("Successfully completed process_slides.py execution")
    except Exception as e:
        logging.error(f"process_slides.py failed: {e}")
        raise RuntimeError(f"process_slides.py failed: {e}")
        
    # 2. Check and build concept_block_map.json and frame_manifest.json
    concept_map_path = "concept_block_map.json"
    frame_manifest_path = "frame_manifest.json"
    
    should_generate = True
    if os.path.exists(concept_map_path) and os.path.exists(frame_manifest_path):
        try:
            # Run verify_density.py to check if they are valid
            from scripts.verify_density import verify_density
            passed, report = verify_density(concept_map_path, transcript_path)
            if passed:
                logging.info(f"Manifests '{concept_map_path}' and '{frame_manifest_path}' already exist and pass density checks. Skipping generation.")
                should_generate = False
            else:
                logging.warning(f"Existing manifests failed density checks: {report}. Regenerating...")
        except Exception as e:
            logging.warning(f"Failed to verify density of existing manifests: {e}. Regenerating...")
            
    if should_generate:
        logging.info("Building concept block map and frame manifest...")
        
        # First, try the pre-built fallback files (for known lectures)
        fallback_map = "scripts/fallback_concept_block_map.json"
        fallback_frames = "scripts/fallback_frame_manifest.json"
        
        # Always prefer pre-built fallback if it exists and matches the lecture (faster, deterministic)
        is_cpu_scheduling = "scheduling" in transcript_content.lower()
        if is_cpu_scheduling and os.path.exists(fallback_map) and os.path.exists(fallback_frames):
            logging.info("Using pre-mapped offline fallback manifests...")
            shutil.copy(fallback_map, concept_map_path)
            shutil.copy(fallback_frames, frame_manifest_path)
            logging.info(f"Copied fallback manifests to '{concept_map_path}' and '{frame_manifest_path}'")
        else:
            # Call parse_transcript.py
            logging.info("Running parse_transcript.py dynamically...")
            cmd = [
                sys.executable, "scripts/parse_transcript.py",
                "--input", transcript_path,
                "--output", concept_map_path,
                "--frame-manifest", frame_manifest_path
            ]
            
            # Read lecture title if available
            title_file = "lecture-input/lecture_title.txt"
            if os.path.exists(title_file):
                try:
                    with open(title_file, "r", encoding="utf-8") as f:
                        lecture_title = f.read().strip()
                    if lecture_title:
                        cmd.extend(["--lecture-title", lecture_title])
                        logging.info(f"Using lecture title: {lecture_title}")
                except Exception as e:
                    logging.warning(f"Failed to read lecture title from {title_file}: {e}")

            try:
                subprocess.run(cmd, check=True)
                logging.info(f"Successfully generated manifests '{concept_map_path}' and '{frame_manifest_path}'")
            except Exception as e:
                logging.error(f"Failed to generate manifests: {e}")
                raise RuntimeError(f"parse_transcript.py failed: {e}")
                
        # Run verify_density.py on the newly generated manifests
        try:
            from scripts.verify_density import verify_density
            passed, report = verify_density(concept_map_path, transcript_path)
            if not passed:
                logging.warning(f"⚠️ Newly generated manifests failed density checks: {report}")
            else:
                logging.info("✅ Newly generated manifests passed density verification.")
        except Exception as e:
            logging.warning(f"Failed to verify density of generated manifests: {e}")
            
    res = {
        "status": "concepts_mapped",
        "attempts": state.get("attempts", 0) + 1
    }
    update_workspace_state(state, "content-mapper", "Mapped concepts from transcript")
    return res

def extract_reference_screenshots_node(state: AgentState) -> Dict:
    logging.info("=== [Node: extract-reference] Extracting embedded reference screenshots ===")
    
    logging.info("Running extract_reference_screenshots.py...")
    try:
        subprocess.run([sys.executable, "scripts/extract_reference_screenshots.py"], check=True)
    except Exception as e:
        logging.warning(f"Error during reference screenshot extraction: {e}")
        
    res = {
        "status": "reference_extracted"
    }
    update_workspace_state(state, "extract-reference", "Extracted embedded reference screenshots")
    return res

def example_extractor_node(state: AgentState) -> Dict:
    logging.info("=== [Node: example-extractor] Extracting examples and visual moments ===")
    
    # 1. Load frame_manifest.json to get timestamps
    manifest_path = "frame_manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        if isinstance(manifest_data, dict) and "frames" in manifest_data:
            frames_list = manifest_data["frames"]
        elif isinstance(manifest_data, list):
            frames_list = manifest_data
        elif isinstance(manifest_data, dict):
            frames_list = list(manifest_data.values())
        else:
            frames_list = []
            
        timestamps = [info["timestamp"] for info in frames_list if isinstance(info, dict) and info.get("timestamp")]
        if timestamps:
            video_path = find_video_path()
                
            logging.info(f"Running extract_frames.py with timestamps: {timestamps} using video: {video_path}")
            subprocess.run([
                sys.executable, "scripts/extract_frames.py",
                "--video", video_path,
                "--output-dir", "screenshots",
                "--timestamps"
            ] + timestamps, check=True)
        else:
            logging.info("No timestamps found in frame manifest.")
    else:
        logging.warning("Warning: frame_manifest.json not found. Skipping extraction.")
        
    logging.info("Running crop_frames.py...")
    subprocess.run([sys.executable, "scripts/crop_frames.py"], check=True)
    
    res = {
        "status": "examples_extracted"
    }
    update_workspace_state(state, "example-extractor", "Extracted video frames and visual moments")
    return res

def note_formatter_node(state: AgentState) -> Dict:
    logging.info("=== [Node: note-formatter] Generating Word Document and running Student Tester ===")
    
    # F-4: Semantic Coherence Check - warn if concept map and frame manifest seem mismatched
    try:
        with open(state["concept_map_path"], 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                concept_blocks = data.get("blocks", [])
            else:
                concept_blocks = data
        with open(state["frame_manifest_path"], 'r') as f:
            fdata = json.load(f)
            frames = {}
            if isinstance(fdata, dict) and "frames" in fdata and isinstance(fdata["frames"], list):
                for item in fdata["frames"]:
                    fname = item.get("filename")
                    if fname:
                        frames[fname] = item
            elif isinstance(fdata, list):
                for item in fdata:
                    fname = item.get("filename")
                    if fname:
                        frames[fname] = item
            else:
                frames = fdata
        
        # Extract keywords from concept block titles
        concept_keywords = set()
        for block in concept_blocks:
            title = block.get('title', '').lower()
            concept_keywords.update(title.split())
        
        # Extract keywords from frame OCR text
        frame_keywords = set()
        for fname, frame_data in frames.items():
            ocr_text = frame_data.get('ocr_text', '').lower()
            frame_keywords.update(ocr_text.split())
        
        # Check for overlap - if very low overlap, warn about potential mismatch
        common_keywords = concept_keywords & frame_keywords
        overlap_ratio = len(common_keywords) / max(len(concept_keywords), 1)
        
        if overlap_ratio < 0.1 and len(concept_keywords) > 5 and len(frame_keywords) > 5:
            logging.warning(f"⚠️ SEMANTIC COHERENCE WARNING: Low keyword overlap ({overlap_ratio:.2%}) between concept map and frames.")
            logging.warning(f"   Concept topics may not match frame content. Common keywords: {list(common_keywords)[:10]}")
    except Exception as e:
        logging.error(f"Failed to perform semantic coherence check: {e}")
    
    logging.info("Running generate_docx.py...")
    subprocess.run([
        sys.executable, "scripts/generate_docx.py",
        "--concept-map", state["concept_map_path"],
        "--frame-manifest", state["frame_manifest_path"],
        "--slide-manifest", state["slide_manifest_path"],
        "--output", state["output_path"]
    ], check=True)
    
    logging.info("Running student_tester.py...")
    subprocess.run([sys.executable, "scripts/student_tester.py"], check=True)

    short_note_path = os.path.join("notes-output", "LECTURE_SHORTNOTE.md")
    logging.info("Running generate_short_note.py...")
    subprocess.run([
        sys.executable, "scripts/generate_short_note.py",
        "--concept-map", state["concept_map_path"],
        "--transcript", find_transcript_path(),
        "--slide-manifest", state["slide_manifest_path"],
        "--frame-manifest", state["frame_manifest_path"],
        "--mode", "auto",
        "--output", short_note_path
    ], check=True)
    
    res = {
        "status": "document_formatted",
        "failed_gate": 0,
        "short_note_path": short_note_path
    }
    temp_state = dict(state)
    temp_state.update(res)
    update_workspace_state(temp_state, "note-formatter", "Formatted notes document, generated short note, and ran student tests")
    return res

def run_stages_audit(state: AgentState) -> Dict:
    logging.info("Evaluating gates...")
    all_ok, gates = run_audit(
        state["output_path"],
        state["concept_map_path"],
        state["frame_manifest_path"],
        state["slide_manifest_path"]
    )
    
    results = {}
    for gate_name, ok in gates.items():
        gate_num = GATE_MAPPING.get(gate_name, 0)
        results[str(gate_num)] = ok
        
    return results

def audit_stage_1_node(state: AgentState) -> Dict:
    logging.info("=== [Node: audit-stage-1] Auditing Gates 1 - 4 ===")
    results = run_stages_audit(state)
    failed_gate = 0
    for g in [1, 2, 3, 4]:
        if not results.get(str(g), True):
            failed_gate = g
            break
    
    gate_retries = dict(state.get("gate_retries", {}))
    if failed_gate > 0:
        gate_retries[str(failed_gate)] = gate_retries.get(str(failed_gate), 0) + 1
        
    res = {
        "failed_gate": failed_gate,
        "gate_results": results,
        "gate_retries": gate_retries
    }
    temp_state = dict(state)
    temp_state.update(res)
    update_workspace_state(temp_state, "audit-stage-1", f"Audited stage 1. Failed gate: {failed_gate}")
    return res

def audit_stage_2_node(state: AgentState) -> Dict:
    logging.info("=== [Node: audit-stage-2] Auditing Gates 5 - 8 ===")
    failed_gate = 0
    for g in [5, 6, 7, 8]:
        if not state["gate_results"].get(str(g), True):
            failed_gate = g
            break
            
    gate_retries = dict(state.get("gate_retries", {}))
    if failed_gate > 0:
        gate_retries[str(failed_gate)] = gate_retries.get(str(failed_gate), 0) + 1
        
    res = {
        "failed_gate": failed_gate,
        "gate_retries": gate_retries
    }
    temp_state = dict(state)
    temp_state.update(res)
    update_workspace_state(temp_state, "audit-stage-2", f"Audited stage 2. Failed gate: {failed_gate}")
    return res

def audit_stage_3_node(state: AgentState) -> Dict:
    logging.info("=== [Node: audit-stage-3] Auditing Gates 9 - 12 ===")
    failed_gate = 0
    for g in [9, 10, 11, 12]:
        if not state["gate_results"].get(str(g), True):
            failed_gate = g
            break
            
    gate_retries = dict(state.get("gate_retries", {}))
    if failed_gate > 0:
        gate_retries[str(failed_gate)] = gate_retries.get(str(failed_gate), 0) + 1
        
    res = {
        "failed_gate": failed_gate,
        "gate_retries": gate_retries
    }
    temp_state = dict(state)
    temp_state.update(res)
    update_workspace_state(temp_state, "audit-stage-3", f"Audited stage 3. Failed gate: {failed_gate}")
    return res

def audit_stage_4_node(state: AgentState) -> Dict:
    logging.info("=== [Node: audit-stage-4] Auditing Gates 13 - 22 ===")
    failed_gate = 0
    for g in [13, 14, 15, 16, 17, 18, 19, 20, 21, 22]:
        if not state["gate_results"].get(str(g), True):
            failed_gate = g
            break
            
    gate_retries = dict(state.get("gate_retries", {}))
    if failed_gate > 0:
        gate_retries[str(failed_gate)] = gate_retries.get(str(failed_gate), 0) + 1
        
    res = {
        "failed_gate": failed_gate,
        "gate_retries": gate_retries
    }
    temp_state = dict(state)
    temp_state.update(res)
    update_workspace_state(temp_state, "audit-stage-4", f"Audited stage 4. Failed gate: {failed_gate}")
    return res

def abort_node(state: AgentState) -> Dict:
    logging.info("=== [Node: abort] Pipeline aborted due to retry limit ===")
    res = {
        "status": "aborted"
    }
    update_workspace_state(state, "abort", "Pipeline aborted due to retry limit")
    return res

# CONDITIONAL ROUTING
def route_after_content_mapper(state: AgentState) -> str:
    has_video = os.path.exists(find_video_path())
    has_slides = os.path.exists("lecture-input/SLIDES.pdf") or os.path.exists("lecture-input/SLIDES.pptx")
    has_ref = os.path.exists("lecture-input/REFERENCE_NOTES.pdf")
    
    if has_video or has_slides:
        logging.info("Routing to core_branch (example-extractor)")
        return "example-extractor"
    elif has_ref:
        logging.info("Routing to reference_branch (extract-reference)")
        return "extract-reference"
    else:
        logging.info("Routing to plain_branch (note-formatter)")
        return "note-formatter"

def route_after_stage_1(state: AgentState) -> str:
    failed_gate = state.get("failed_gate", 0)
    if failed_gate == 0:
        return "audit-stage-2"
        
    retries = state.get("gate_retries", {}).get(str(failed_gate), 0)
    if retries >= 3:
        log_abort(state, f"Gate {failed_gate} exceeded 3 retries.")
        return "abort"
        
    if failed_gate == 4:
        logging.info(f"Gate {failed_gate} failed. Attempt {retries}/3. Retrying content-mapper.")
        return "content-mapper"
        
    logging.info(f"Gate {failed_gate} failed. Attempt {retries}/3. Retrying note-formatter.")
    return "note-formatter"
    
def route_after_stage_2(state: AgentState):
    failed = state.get("failed_gate", 0)
    if failed > 0:
        retries = state.get("gate_retries", {}).get(str(failed), 0)
        if retries >= 3:
            log_abort(state, f"Gate {failed} exceeded 3 retries.")
            return "abort"
        if failed > 5:
            logging.info(f"Gate {failed} failed (> 5). Attempt {retries}/3. State preserved. Retrying note-formatter.")
            return "note-formatter"
        else:
            logging.info(f"Gate {failed} failed. Attempt {retries}/3. Retrying note-formatter.")
            return "note-formatter"
    return "audit-stage-3"

def route_after_stage_3(state: AgentState):
    failed = state.get("failed_gate", 0)
    if failed > 0:
        retries = state.get("gate_retries", {}).get(str(failed), 0)
        if retries >= 3:
            log_abort(state, f"Gate {failed} exceeded 3 retries.")
            return "abort"
        logging.info(f"Gate {failed} failed (> 5). Attempt {retries}/3. State preserved. Retrying note-formatter.")
        return "note-formatter"
    return "audit-stage-4"

def route_after_stage_4(state: AgentState):
    failed = state.get("failed_gate", 0)
    if failed > 0:
        retries = state.get("gate_retries", {}).get(str(failed), 0)
        if retries >= 3:
            log_abort(state, f"Gate {failed} exceeded 3 retries.")
            return "abort"
        if failed in [20, 21]:
            logging.info(f"Gate {failed} failed. Attempt {retries}/3. Retrying content-mapper.")
            return "content-mapper"
        logging.info(f"Gate {failed} failed (> 5). Attempt {retries}/3. State preserved. Retrying note-formatter.")
        return "note-formatter"
    return END

# BUILD THE GRAPH
builder = StateGraph(AgentState)

builder.add_node("content-mapper", content_mapper_node)
builder.add_node("example-extractor", example_extractor_node)
builder.add_node("extract-reference", extract_reference_screenshots_node)
builder.add_node("note-formatter", note_formatter_node)
builder.add_node("audit-stage-1", audit_stage_1_node)
builder.add_node("audit-stage-2", audit_stage_2_node)
builder.add_node("audit-stage-3", audit_stage_3_node)
builder.add_node("audit-stage-4", audit_stage_4_node)
builder.add_node("abort", abort_node)

builder.add_edge(START, "content-mapper")

builder.add_conditional_edges(
    "content-mapper",
    route_after_content_mapper,
    {
        "example-extractor": "example-extractor",
        "extract-reference": "extract-reference",
        "note-formatter": "note-formatter"
    }
)

builder.add_edge("example-extractor", "note-formatter")
builder.add_edge("extract-reference", "note-formatter")
builder.add_edge("note-formatter", "audit-stage-1")
builder.add_edge("abort", END)

builder.add_conditional_edges("audit-stage-1", route_after_stage_1)
builder.add_conditional_edges("audit-stage-2", route_after_stage_2)
builder.add_conditional_edges("audit-stage-3", route_after_stage_3)
builder.add_conditional_edges("audit-stage-4", route_after_stage_4)

def build_graph():
    # Create checkpoints directory
    os.makedirs("logs", exist_ok=True)
    db_path = "logs/langgraph_checkpoints.db"
    # Checkpoint DB preserved for recovery
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    return builder.compile(checkpointer=memory), conn

def run_pipeline():
    lock_file = "logs/pipeline.lock"
    conn = None
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r") as f:
                old_pid = int(f.read().strip())
            if is_pid_running(old_pid):
                logging.error(f"❌ LangGraph Orchestrator aborting: another instance (PID {old_pid}) is currently running.")
                return False
        except Exception:
            pass
            
    try:
        os.makedirs(os.path.dirname(lock_file), exist_ok=True)
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))
            
        subprocess.run(["/bin/bash", "scripts/pre-exec-check.sh"], check=True)
        
        # Check run fingerprint to prevent reusing stale manifests from a different lecture
        current_fingerprint = compute_run_fingerprint()
        stale = False
        if os.path.exists("workspace_state.json"):
            try:
                with open("workspace_state.json", "r", encoding="utf-8") as f:
                    old_state = json.load(f)
                    old_fingerprint = old_state.get("active_lecture", {}).get("run_fingerprint")
                    if old_fingerprint != current_fingerprint:
                        logging.info(f"🔄 Run fingerprint changed ({old_fingerprint} -> {current_fingerprint}). Clearing stale manifests.")
                        stale = True
            except Exception as e:
                logging.warning(f"Could not read workspace_state.json to check fingerprint: {e}. Defaulting to clearing manifests.")
                stale = True
        else:
            logging.info("No workspace_state.json found. Initializing new run fingerprint.")
            stale = True

        if stale:
            for manifest_name in [
                "concept_block_map.json",
                "frame_manifest.json",
                "slide_manifest.json",
                "reference_manifest.json",
                "embedded_manifest.json",
                "inserted_images.json",
                "logs/last_run_audit.json",
                "notes-output/LECTURE_NOTES.docx",
                "notes-output/LECTURE_SHORTNOTE.md"
            ]:
                if os.path.exists(manifest_name):
                    try:
                        os.remove(manifest_name)
                        logging.info(f"Cleared stale manifest: {manifest_name}")
                    except Exception as e:
                        logging.error(f"Failed to clear stale manifest {manifest_name}: {e}")
        
        initial_state = {
            "status": "start",
            "concept_map_path": "concept_block_map.json",
            "frame_manifest_path": "frame_manifest.json",
            "slide_manifest_path": "slide_manifest.json",
            "output_path": "notes-output/LECTURE_NOTES.docx",
            "failed_gate": 0,
            "gate_results": {},
            "gate_retries": {},
            "attempts": 0
        }
        
        config = {"configurable": {"thread_id": f"lecture_reconstruction_run_{current_fingerprint[:12]}"}}
        
        graph, conn = build_graph()
        
        logging.info("Starting LangGraph Orchestrator Execution...")
        final_state = graph.invoke(initial_state, config=config)
        
        failed = final_state.get("failed_gate", 0)
        status = final_state.get("status", "failed")
        
        # Save checkpoint JSON file
        checkpoint_file = "logs/last_run_audit.json"
        checkpoint_data = {
            "_run_fingerprint": current_fingerprint,
            "_timestamp": datetime.datetime.now().isoformat(),
            **final_state.get("gate_results", {})
        }
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2)
        logging.info(f"Audit results written to checkpoint file: {checkpoint_file}")
        
        # Run archive cleanup policy
        try:
            logging.info("Running archive and backup cleanup policy...")
            import sys
            subprocess.run([sys.executable, "scripts/cleanup_archives.py"], check=True)
            logging.info("✅ Archive cleanup completed successfully.")
        except Exception as cleanup_err:
            logging.error(f"⚠️ Archive cleanup failed: {cleanup_err}")
        
        if failed == 0 and status != "aborted":
            logging.info("LangGraph Orchestrator finished successfully. All 22 gates passed.")
            
            # Archive the successful notes copy here!
            try:
                import shutil, re
                lecture_title = "Unknown Lecture"
                if os.path.exists("concept_block_map.json"):
                    with open("concept_block_map.json", "r", encoding="utf-8") as f:
                        c_map = json.load(f)
                        if isinstance(c_map, dict):
                            lecture_title = c_map.get("lecture_title") or lecture_title
                
                sanitized_title = re.sub(r'[^a-zA-Z0-9_-]', '_', lecture_title)
                sanitized_title = re.sub(r'_+', '_', sanitized_title).strip('_')
                current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                archive_name = f"LECTURE_NOTES_{sanitized_title}_{current_date}.docx"
                archive_path = os.path.join("notes-output", archive_name)
                shutil.copy2(final_state["output_path"], archive_path)
                logging.info(f"Archived unique copy of successful run saved at: {archive_path}")
                
                # Run cleanup again to immediately clean the previous archive of the same lecture
                try:
                    subprocess.run([sys.executable, "scripts/cleanup_archives.py"], check=True)
                    logging.info("✅ Final post-archive cleanup completed successfully.")
                except Exception as cleanup_err:
                    logging.warning(f"⚠️ Final post-archive cleanup failed: {cleanup_err}")
            except Exception as archive_err:
                logging.error(f"Failed to archive successful notes: {archive_err}")

            update_workspace_state(final_state, "completed", "Pipeline completed successfully with all gates passing")
            store_run("success", 22, [], final_state["output_path"])
            
            # Auto-upload to Cloudflare R2 and log to Supabase
            try:
                logging.info("Starting automatic cloud upload to R2 and Supabase...")
                import sys
                subprocess.run([sys.executable, "scripts/upload_run.py"], check=True)
                logging.info("✅ Automatic cloud upload completed successfully!")
            except Exception as upload_err:
                logging.error(f"❌ Automatic cloud upload failed: {upload_err}")
                
            return True
        else:
            logging.error(f"❌ LangGraph Orchestrator completed with errors. Status: {status}. Failed gate: {failed}.")
            update_workspace_state(final_state, "failed", f"Pipeline failed on Gate {failed}")
            failed_list = [f"Gate {failed}"] if failed > 0 else ["Pipeline Aborted"]
            passed_count = len([v for v in final_state.get("gate_results", {}).values() if v])
            store_run("failed", passed_count, failed_list, final_state["output_path"])
            return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        if os.path.exists(lock_file):
            try:
                with open(lock_file, "r") as f:
                    content_pid = int(f.read().strip())
                if content_pid == os.getpid():
                    os.remove(lock_file)
            except Exception:
                pass

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)

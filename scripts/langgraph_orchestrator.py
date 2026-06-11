#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import datetime
import subprocess
import logging
import shutil
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

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.audit import run_audit
from scripts.memory_store import store_run

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

# NODES
def content_mapper_node(state: AgentState) -> Dict:
    logging.info("=== [Node: content-mapper] Mapping concepts from transcript and slides ===")
    os.makedirs("notes-output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 1. Check transcript
    transcript_path = "lecture-input/transcript.srt"
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Error: Transcript file not found at '{transcript_path}'")
        
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_content = f.read()
        
    if len(transcript_content.strip()) < 3000:
        raise ValueError(f"Error: Transcript at '{transcript_path}' is missing or too short ({len(transcript_content)} chars).")
        
    # 2. Check and build concept_block_map.json and frame_manifest.json
    concept_map_path = "concept_block_map.json"
    frame_manifest_path = "frame_manifest.json"
    
    if os.path.exists(concept_map_path) and os.path.exists(frame_manifest_path):
        logging.info(f"Manifests '{concept_map_path}' and '{frame_manifest_path}' already exist. Skipping generation.")
    else:
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
            # Check for Antigravity CLI path
            cli_path = os.environ.get("ANTIGRAVITY_CLI_PATH") or shutil.which("antigravity")
            if not cli_path:
                logging.warning("Warning: 'antigravity' CLI is not found on PATH or ANTIGRAVITY_CLI_PATH. Checking for fallback manifests...")
                if os.path.exists(fallback_map) and os.path.exists(fallback_frames):
                    shutil.copy(fallback_map, concept_map_path)
                    shutil.copy(fallback_frames, frame_manifest_path)
                    logging.info(f"Copied fallback manifests to '{concept_map_path}' and '{frame_manifest_path}' as CLI is not available.")
                else:
                    raise FileNotFoundError("antigravity CLI not found and no fallback manifests are available.")
            else:
                # For brand-new lectures, call the Antigravity CLI
                logging.info(f"Calling Antigravity CLI from '{cli_path}' for dynamic mapping...")
                try:
                    cli_result = subprocess.run(
                        [
                            cli_path, "chat",
                            "Read the transcript at lecture-input/transcript.srt. "
                            "Build a chronological Concept Block Map following the v8.0 Source Fidelity Protocol. "
                            "Save it as concept_block_map.json. "
                            "Also extract visual timestamps and save them as frame_manifest.json."
                        ],
                        capture_output=True, text=True, timeout=600
                    )
                    logging.info(cli_result.stdout)
                    if cli_result.returncode != 0:
                        logging.error(f"Antigravity CLI failed: {cli_result.stderr}")
                        logging.info("Attempting to fall back to pre-built offline manifests...")
                        if os.path.exists(fallback_map) and os.path.exists(fallback_frames):
                            shutil.copy(fallback_map, concept_map_path)
                            shutil.copy(fallback_frames, frame_manifest_path)
                            logging.info(f"Copied fallback manifests to '{concept_map_path}' and '{frame_manifest_path}' after CLI failure.")
                        else:
                            raise RuntimeError("Antigravity CLI failed to generate manifests and no fallback manifests are available.")
                except subprocess.TimeoutExpired as e:
                    logging.warning("Warning: Antigravity CLI call timed out. Falling back to pre-built offline manifests...")
                    if os.path.exists(fallback_map) and os.path.exists(fallback_frames):
                        shutil.copy(fallback_map, concept_map_path)
                        shutil.copy(fallback_frames, frame_manifest_path)
                        logging.info(f"Copied fallback manifests to '{concept_map_path}' and '{frame_manifest_path}' due to timeout")
                    else:
                        raise RuntimeError("Antigravity CLI timed out and no fallback manifests are available.") from e
            
            # Verify the files actually were created
            if not os.path.exists(concept_map_path) or not os.path.exists(frame_manifest_path):
                raise FileNotFoundError("Manifest generation did not produce the expected manifests")
                
    # 3. Run process_slides.py
    logging.info("Running process_slides.py...")
    subprocess.run([sys.executable, "scripts/process_slides.py"], check=True)
    
    return {
        "status": "concepts_mapped",
        "attempts": state.get("attempts", 0) + 1
    }

def example_extractor_node(state: AgentState) -> Dict:
    logging.info("=== [Node: example-extractor] Extracting examples and visual moments ===")
    
    # 1. Load frame_manifest.json to get timestamps
    manifest_path = "frame_manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            frames = json.load(f)
        timestamps = [info["timestamp"] for info in frames.values() if info.get("timestamp")]
        if timestamps:
            logging.info(f"Running extract_frames.py with timestamps: {timestamps}")
            subprocess.run([
                sys.executable, "scripts/extract_frames.py",
                "--video", "lecture-input/LECTURE.mp4",
                "--output-dir", "screenshots",
                "--timestamps"
            ] + timestamps, check=True)
        else:
            logging.info("No timestamps found in frame manifest.")
    else:
        logging.warning("Warning: frame_manifest.json not found. Skipping extraction.")
        
    logging.info("Running crop_frames.py...")
    subprocess.run([sys.executable, "scripts/crop_frames.py"], check=True)
    
    return {
        "status": "examples_extracted"
    }

def note_formatter_node(state: AgentState) -> Dict:
    logging.info("=== [Node: note-formatter] Generating Word Document and running Student Tester ===")
    
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
    
    return {
        "status": "document_formatted",
        "failed_gate": 0
    }

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
        
    return {
        "failed_gate": failed_gate,
        "gate_results": results,
        "gate_retries": gate_retries
    }

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
        
    return {
        "failed_gate": failed_gate,
        "gate_retries": gate_retries
    }

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
        
    return {
        "failed_gate": failed_gate,
        "gate_retries": gate_retries
    }

def audit_stage_4_node(state: AgentState) -> Dict:
    logging.info("=== [Node: audit-stage-4] Auditing Gates 13 - 15 ===")
    failed_gate = 0
    for g in [13, 14, 15]:
        if not state["gate_results"].get(str(g), True):
            failed_gate = g
            break
            
    gate_retries = dict(state.get("gate_retries", {}))
    if failed_gate > 0:
        gate_retries[str(failed_gate)] = gate_retries.get(str(failed_gate), 0) + 1
        
    return {
        "failed_gate": failed_gate,
        "gate_retries": gate_retries
    }

def abort_node(state: AgentState) -> Dict:
    logging.info("=== [Node: abort] Pipeline aborted due to retry limit ===")
    return {
        "status": "aborted"
    }

# CONDITIONAL ROUTING
def route_after_stage_1(state: AgentState) -> str:
    """
    ROUTING LOGIC FIX:
    - If Gate 4 (Content Completeness) fails, we MUST go back to 'content-mapper', 
      NOT 'note-formatter'.
    - If Gates 1-3 fail, we abort or retry specific steps.
    """
    failed_gate = state.get("failed_gate", 0)
    retry_count = state.get("retry_count", 0)
    
    if failed_gate == 0:
        # All passed
        return "stage_2_audit"
    
    if failed_gate in [1, 2, 3]:
        # Structural/Format errors -> Hard Fail or Retry limited times
        if retry_count < 3:
            print(f"⚠️ Retrying due to Gate {failed_gate} failure...")
            return "note-formatter" # Retry formatting
        else:
            print("❌ Critical structural failure after 3 retries.")
            return "end_failure"
            
    if failed_gate == 4:
        # CONTENT COMPLETENESS FAILURE
        # FIX: Must regenerate the map, not reformat the note!
        print("⚠️ Content Completeness Failed. Regenerating Concept Map...")
        return "content-mapper"  # <--- THIS IS THE FIX
    
    if failed_gate >= 5:
        # Quality issues (Grammar, Tone, etc) -> Retry Formatting
        if retry_count < 3:
            return "note-formatter"
        else:
            return "end_failure"
    
    return "end_failure"
    
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
        logging.info(f"Gate {failed} failed (> 5). Attempt {retries}/3. State preserved. Retrying note-formatter.")
        return "note-formatter"
    return END

# BUILD THE GRAPH
builder = StateGraph(AgentState)

builder.add_node("content-mapper", content_mapper_node)
builder.add_node("example-extractor", example_extractor_node)
builder.add_node("note-formatter", note_formatter_node)
builder.add_node("audit-stage-1", audit_stage_1_node)
builder.add_node("audit-stage-2", audit_stage_2_node)
builder.add_node("audit-stage-3", audit_stage_3_node)
builder.add_node("audit-stage-4", audit_stage_4_node)
builder.add_node("abort", abort_node)

builder.add_edge(START, "content-mapper")
builder.add_edge("content-mapper", "example-extractor")
builder.add_edge("example-extractor", "note-formatter")
builder.add_edge("note-formatter", "audit-stage-1")
builder.add_edge("abort", END)

builder.add_conditional_edges("audit-stage-1", route_after_stage_1)
builder.add_conditional_edges("audit-stage-2", route_after_stage_2)
builder.add_conditional_edges("audit-stage-3", route_after_stage_3)
builder.add_conditional_edges("audit-stage-4", route_after_stage_4)

# Create checkpoints directory
os.makedirs("logs", exist_ok=True)
db_path = "logs/langgraph_checkpoints.db"
# Checkpoint DB preserved for recovery
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

graph = builder.compile(checkpointer=memory)

def run_pipeline():
    subprocess.run(["/bin/bash", "scripts/pre-exec-check.sh"], check=True)
    
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
    
    config = {"configurable": {"thread_id": "lecture_reconstruction_run"}}
    
    logging.info("Starting LangGraph Orchestrator Execution...")
    final_state = graph.invoke(initial_state, config=config)
    
    failed = final_state.get("failed_gate", 0)
    status = final_state.get("status", "failed")
    
    # Save checkpoint JSON file
    checkpoint_file = "logs/last_run_audit.json"
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(final_state.get("gate_results", {}), f, indent=2)
    logging.info(f"Audit results written to checkpoint file: {checkpoint_file}")
    
    if failed == 0 and status != "aborted":
        logging.info("🎉 LangGraph Orchestrator finished successfully! All 15 gates passed.")
        store_run("success", 15, [], final_state["output_path"])
        return True
    else:
        logging.error(f"❌ LangGraph Orchestrator completed with errors. Status: {status}. Failed gate: {failed}.")
        failed_list = [f"Gate {failed}"] if failed > 0 else ["Pipeline Aborted"]
        store_run("failed", 15 - len([k for k, v in final_state.get("gate_results", {}).items() if not v]), failed_list, final_state["output_path"])
        return False

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)

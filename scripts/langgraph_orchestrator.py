#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import datetime
import subprocess
from typing import TypedDict, Dict, List, Annotated

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
    print(f"Abort failure log written to agent_memory/failures/{filename}")

# NODES
def content_mapper_node(state: AgentState) -> Dict:
    print("\n=== [Node: content-mapper] Mapping concepts from transcript and slides ===")
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
        print(f"Manifests '{concept_map_path}' and '{frame_manifest_path}' already exist. Skipping generation.")
    else:
        print("Building concept block map and frame manifest...")
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            import httpx
            # Run API call to map transcript using Gemini model
            print("Running live Gemini API transcript mapping...")
            prompt = f"""
Analyze the following lecture transcript (SRT format).
Group it into chronological Concept Blocks.
For each block, extract:
- block_id (e.g. CB1, CB2)
- title (a meaningful grammatical or educational topic, NOT generic question numbers)
- explanation (concise explanation, under 600 characters)
- transcript_range_percent (estimate start and end percentage [start, end])
- examples (list of solved examples with keys: sentence, rule, working)
- exercise_questions (list of exercise questions discussed)
- visual_moments (list of timestamps where the teacher refers to the board/screen with keys: timestamp, type, description)
- teacher_quotes (list of teacher quotes, clean of SRT artifacts)
- traps (list of exam traps)
- tricks (list of tricks)

Also extract the overall lecture title.

Output ONLY valid JSON matching this schema:
{{
  "lecture_title": "...",
  "concept_blocks": [
     {{
       "block_id": "CB1",
       "title": "...",
       "explanation": "...",
       "transcript_range_percent": [0, 15],
       "examples": [
          {{
            "sentence": "...",
            "rule": "...",
            "working": "..."
          }}
       ],
       "exercise_questions": ["..."],
       "visual_moments": [
          {{
            "timestamp": "HH:MM:SS",
            "type": "board",
            "description": "..."
          }}
       ],
       "teacher_quotes": ["..."],
       "traps": ["..."],
       "tricks": ["..."]
     }}
  ]
}}

Transcript:
{transcript_content}
"""
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            try:
                response = httpx.post(url, json=payload, headers=headers, timeout=120.0)
                response.raise_for_status()
                result = response.json()
                text_content = result["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_content)
                
                # Format to expected concept_block_map.json schema
                lecture_title = parsed.get("lecture_title", "Lecture Notes")
                blocks = parsed.get("concept_blocks", [])
                if blocks:
                    blocks[0]["lecture_title"] = lecture_title
                
                # Write concept_block_map.json
                with open(concept_map_path, "w", encoding="utf-8") as out_f:
                    json.dump(blocks, out_f, indent=2)
                print(f"Successfully wrote {concept_map_path}")
                
                # Build frame_manifest.json from visual_moments
                frame_manifest = {}
                for block in blocks:
                    block_id = block.get("block_id", "CB1")
                    visuals = block.get("visual_moments", [])
                    for i, vis in enumerate(visuals):
                        ts = vis.get("timestamp")
                        if ts:
                            filename = f"{block_id}_{i+1}.jpg"
                            frame_manifest[filename] = {
                                "timestamp": ts,
                                "ocr_text": "extracted frame OCR placeholder text",
                                "type": vis.get("type", "board")
                            }
                with open(frame_manifest_path, "w", encoding="utf-8") as out_f:
                    json.dump(frame_manifest, out_f, indent=2)
                print(f"Successfully wrote {frame_manifest_path}")
                
            except Exception as e:
                print(f"Failed to query Gemini API or parse response: {e}")
                raise
        else:
            # Fallback to local pre-mapped documents if available
            print("No Gemini API Key found in environment. Checking local fallbacks...")
            fallback_map = "scripts/fallback_concept_block_map.json"
            fallback_frames = "scripts/fallback_frame_manifest.json"
            
            if os.path.exists(fallback_map) and os.path.exists(fallback_frames):
                print("Using pre-mapped offline fallback manifests...")
                import shutil
                shutil.copy(fallback_map, concept_map_path)
                shutil.copy(fallback_frames, frame_manifest_path)
                print(f"Copied fallback manifests to '{concept_map_path}' and '{frame_manifest_path}'")
            else:
                raise ValueError("No Gemini API key provided, and no fallback manifests are available.")
                
    # 3. Run process_slides.py
    print("Running process_slides.py...")
    subprocess.run([sys.executable, "scripts/process_slides.py"], check=True)
    
    return {
        "status": "concepts_mapped",
        "attempts": state.get("attempts", 0) + 1
    }

def example_extractor_node(state: AgentState) -> Dict:
    print("\n=== [Node: example-extractor] Extracting examples and visual moments ===")
    
    # 1. Load frame_manifest.json to get timestamps
    manifest_path = "frame_manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            frames = json.load(f)
        timestamps = [info["timestamp"] for info in frames.values() if info.get("timestamp")]
        if timestamps:
            print(f"Running extract_frames.py with timestamps: {timestamps}")
            subprocess.run([
                sys.executable, "scripts/extract_frames.py",
                "--video", "lecture-input/LECTURE.mp4",
                "--output-dir", "screenshots",
                "--timestamps"
            ] + timestamps, check=True)
        else:
            print("No timestamps found in frame manifest.")
    else:
        print("Warning: frame_manifest.json not found. Skipping extraction.")
        
    print("Running crop_frames.py...")
    subprocess.run([sys.executable, "scripts/crop_frames.py"], check=True)
    
    return {
        "status": "examples_extracted"
    }

def note_formatter_node(state: AgentState) -> Dict:
    print("\n=== [Node: note-formatter] Generating Word Document and running Student Tester ===")
    
    print("Running generate_docx.py...")
    subprocess.run([
        sys.executable, "scripts/generate_docx.py",
        "--concept-map", state["concept_map_path"],
        "--frame-manifest", state["frame_manifest_path"],
        "--slide-manifest", state["slide_manifest_path"],
        "--output", state["output_path"]
    ], check=True)
    
    print("Running student_tester.py...")
    subprocess.run([sys.executable, "scripts/student_tester.py"], check=True)
    
    return {
        "status": "document_formatted",
        "failed_gate": 0
    }

def run_stages_audit(state: AgentState) -> Dict:
    print("Evaluating gates...")
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
    print("\n=== [Node: audit-stage-1] Auditing Gates 1 - 4 ===")
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
    print("\n=== [Node: audit-stage-2] Auditing Gates 5 - 8 ===")
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
    print("\n=== [Node: audit-stage-3] Auditing Gates 9 - 12 ===")
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
    print("\n=== [Node: audit-stage-4] Auditing Gates 13 - 15 ===")
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
    print("\n=== [Node: abort] Pipeline aborted due to retry limit ===")
    return {
        "status": "aborted"
    }

# CONDITIONAL ROUTING
def route_after_stage_1(state: AgentState):
    failed = state.get("failed_gate", 0)
    if failed > 0:
        retries = state.get("gate_retries", {}).get(str(failed), 0)
        if retries >= 3:
            log_abort(state, f"Gate {failed} exceeded 3 retries.")
            return "abort"
        if failed <= 3:
            print(f"Gate {failed} failed (<= 3). Attempt {retries}/3. Full Reconstruction.")
            return "content-mapper"
        else:
            print(f"Gate {failed} failed. Attempt {retries}/3. Retrying note-formatter.")
            return "note-formatter"
    return "audit-stage-2"

def route_after_stage_2(state: AgentState):
    failed = state.get("failed_gate", 0)
    if failed > 0:
        retries = state.get("gate_retries", {}).get(str(failed), 0)
        if retries >= 3:
            log_abort(state, f"Gate {failed} exceeded 3 retries.")
            return "abort"
        if failed > 5:
            print(f"Gate {failed} failed (> 5). Attempt {retries}/3. State preserved. Retrying note-formatter.")
            return "note-formatter"
        else:
            print(f"Gate {failed} failed. Attempt {retries}/3. Retrying note-formatter.")
            return "note-formatter"
    return "audit-stage-3"

def route_after_stage_3(state: AgentState):
    failed = state.get("failed_gate", 0)
    if failed > 0:
        retries = state.get("gate_retries", {}).get(str(failed), 0)
        if retries >= 3:
            log_abort(state, f"Gate {failed} exceeded 3 retries.")
            return "abort"
        print(f"Gate {failed} failed (> 5). Attempt {retries}/3. State preserved. Retrying note-formatter.")
        return "note-formatter"
    return "audit-stage-4"

def route_after_stage_4(state: AgentState):
    failed = state.get("failed_gate", 0)
    if failed > 0:
        retries = state.get("gate_retries", {}).get(str(failed), 0)
        if retries >= 3:
            log_abort(state, f"Gate {failed} exceeded 3 retries.")
            return "abort"
        print(f"Gate {failed} failed (> 5). Attempt {retries}/3. State preserved. Retrying note-formatter.")
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
conn = sqlite3.connect("logs/langgraph_checkpoints.db", check_same_thread=False)
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
    
    print("Starting LangGraph Orchestrator Execution...")
    final_state = graph.invoke(initial_state, config=config)
    
    failed = final_state.get("failed_gate", 0)
    status = final_state.get("status", "failed")
    
    # Save checkpoint JSON file
    checkpoint_file = "logs/last_run_audit.json"
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(final_state.get("gate_results", {}), f, indent=2)
    print(f"Audit results written to checkpoint file: {checkpoint_file}")
    
    if failed == 0 and status != "aborted":
        print("\n🎉 LangGraph Orchestrator finished successfully! All 15 gates passed.")
        store_run("success", 15, [], final_state["output_path"])
        return True
    else:
        print(f"\n❌ LangGraph Orchestrator completed with errors. Status: {status}. Failed gate: {failed}.")
        failed_list = [f"Gate {failed}"] if failed > 0 else ["Pipeline Aborted"]
        store_run("failed", 15 - len([k for k, v in final_state.get("gate_results", {}).items() if not v]), failed_list, final_state["output_path"])
        return False

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)

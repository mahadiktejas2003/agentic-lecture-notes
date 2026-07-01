import sys
import os
from typing import Dict, Any

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mcp.server.fastmcp import FastMCP
from scripts.mcp_servers.auth import verify_auth, get_cleaned_args, verify_request_auth, safe_path
from scripts.audit import run_audit as audit_runner

# Verify authentication on start
verify_auth()

mcp = FastMCP("Audit Server")

RULES = {
    1: "Gate 1: Structural Integrity - Heading 2 count > 0, Heading 2 count matches Revision Box count, visual failures is 0, and banned attributions is 0.",
    2: "Gate 2: Revision Box Placement - Revision box count matches Heading 2 count (each H2 section must have a revision box).",
    3: "Gate 3: Chronological Flow - Heading 2 count matches the number of concept blocks in the concept block map.",
    4: "Gate 4: Content Completeness - The concept block map must contain at least one block.",
    5: "Gate 5: Factual Accuracy - The number of worked examples in the docx must be greater than or equal to the total examples in the map (or > 0 if no examples mapped).",
    6: "Gate 6: Image Integrity - Visual anchor errors/failures is 0.",
    7: "Gate 7: Minimum Counts - Heading 2 count is at least 1, and the image count in the docx is at least 80% of the expected images (from frames and discussed slides).",
    8: "Gate 8: Source Traceability - The document title must match the active concept map title.",
    9: "Gate 9: Slide Handling - Banned slides (not discussed) must not have their OCR text present in the document.",
    10: "Gate 10: Example Coverage - The number of worked examples in the docx is at least the total examples in the map.",
    11: "Gate 11: Visual Coverage - The image count in the docx is at least 80% of the expected images.",
    12: "Gate 12: Exercise Content - Exercise questions must contain real text, not just integers/placeholders.",
    13: "Gate 13: Quote Quality - Quotes must not contain raw SRT artifacts (garbled text, timestamps, mid-sentence starts).",
    14: "Gate 14: Meaningful Titles - Concept block titles must be meaningful (not generic question ranges).",
    15: "Gate 15: Explanation Conciseness - Explanations must be concise (no verbose text, <= 600 characters, no repeated 'First,').",
    16: "Gate 16: Table Presence - Concept map table definitions must render as Word tables.",
    17: "Gate 17: Sequence Integrity - Generated Heading 2 sections must follow concept block order.",
    18: "Gate 18: Exact Worked Examples - Worked examples from the concept map must appear in the document.",
    19: "Gate 19: Friction Index Constraint - Cloze and Cornell cue density must remain within the configured friction range.",
    20: "Gate 20: Transcript Coverage - Concept block transcript ranges must cover at least 80% of the lecture duration, and at least 80% of concept block headings must appear in the document.",
    21: "Gate 21: English Enforcement - Devanagari script is forbidden and transliterated Hinglish keywords must remain within the configured threshold.",
    22: "Gate 22: Styling and Highlighting Conformity - Quick Revision boxes, Student Note boxes, run shading, and native Word highlighting must match the approved styling rules.",
}

RECOVERIES = {
    1: "Re-run content-mapper node (full reconstruction) to ensure correct structure, headers, and zero attributions.",
    2: "Re-run content-mapper node (full reconstruction) or note-formatter to align the revision boxes with sections.",
    3: "Re-run content-mapper node (full reconstruction) to sync heading count with the concept map block list.",
    4: "Verify that the concept block map is populated and has valid items.",
    5: "Re-run note-formatter to include missing worked examples or review example mapping.",
    6: "Re-run note-formatter and check crop_frames output to fix visual anchors.",
    7: "Re-run note-formatter and ensure images are successfully embedded from manifests.",
    8: "Re-run note-formatter and verify source traceability parameters (traps or quotes) are met.",
    9: "Ensure undiscussed slides do not have their text leaked in the notes.",
    10: "Re-run note-formatter and verify example details are fully populated.",
    11: "Re-run note-formatter to ensure all expected visual assets are correctly embedded.",
    12: "Edit concept block map to remove empty placeholder exercise questions.",
    13: "Filter out SRT timestamps or bad prefixes from the quotes block.",
    14: "Rename concept block titles to avoid generic ranges like 'Questions X-Y'.",
    15: "Shorten verbose explanation blocks to be under 2000 characters and remove redundant headers.",
    16: "Re-run note-formatter and verify table definitions render as styled Word tables.",
    17: "Re-run content-mapper or note-formatter to restore concept block ordering.",
    18: "Re-run note-formatter and verify every mapped worked example appears exactly enough for audit matching.",
    19: "Adjust cloze/Cornell cue density in the concept map or generator, then re-run note formatting.",
    20: "Preserve transcript range metadata and ensure concept block titles actually render as Heading 2 sections in the final document.",
    21: "Clean Devanagari script and excessive Hinglish from mapped content, then regenerate the document.",
    22: "Fix paragraph shading, run shading, and any native Word highlights so the document matches the approved style contract.",
}

GATE_MAPPING = {
    1: 'Gate 1: Structural Integrity',
    2: 'Gate 2: Revision Box Placement',
    3: 'Gate 3: Chronological Flow',
    4: 'Gate 4: Content Completeness',
    5: 'Gate 5: Factual Accuracy',
    6: 'Gate 6: Image Integrity',
    7: 'Gate 7: Minimum Counts',
    8: 'Gate 8: Source Traceability',
    9: 'Gate 9: Slide Handling',
    10: 'Gate 10: Example Coverage',
    11: 'Gate 11: Visual Coverage',
    12: 'Gate 12: Exercise Content',
    13: 'Gate 13: Quote Quality',
    14: 'Gate 14: Meaningful Titles',
    15: 'Gate 15: Explanation Conciseness',
    16: 'Gate 16: Table Presence',
    17: 'Gate 17: Sequence Integrity',
    18: 'Gate 18: Exact Worked Examples',
    19: 'Gate 19: Friction Index Constraint',
    20: 'Gate 20: Transcript Coverage',
    21: 'Gate 21: English Enforcement',
    22: 'Gate 22: Styling and Highlighting Conformity',
}

@mcp.tool()
def run_audit(gate_number: int, docx_path: str, api_key: str = None) -> Dict[str, Any]:
    """
    Runs the audit for a specific gate number on a docx document.
    
    gate_number: The integer gate number to audit (1-22).
    docx_path: The path to the generated document.
    api_key: Optional API key for request validation.
    """
    gate_name = GATE_MAPPING.get(gate_number)
    if not gate_name:
        return {
            "status": "error",
            "gate": str(gate_number),
            "error_type": "invalid_gate",
            "details": f"Gate number {gate_number} is not a valid gate (1-22).",
            "suggested_recovery": "Use a gate number between 1 and 22."
        }
        
    try:
        verify_request_auth(api_key)
        docx_path = safe_path(docx_path)
        
        # Use default paths relative to execution context
        concept_map_path = safe_path("concept_block_map.json")
        frame_manifest_path = safe_path("frame_manifest.json")
        slide_manifest_path = safe_path("slide_manifest.json")
        
        all_ok, gates = audit_runner(
            docx_path=docx_path,
            concept_map_path=concept_map_path,
            frame_manifest_path=frame_manifest_path,
            slide_manifest_path=slide_manifest_path
        )
        
        gate_passed = gates.get(gate_name, False)
        if gate_passed:
            return {
                "status": "passed",
                "gate": gate_name,
                "error_type": "",
                "details": f"Gate {gate_number} passed successfully.",
                "suggested_recovery": ""
            }
        else:
            return {
                "status": "failed",
                "gate": gate_name,
                "error_type": "quality_gate_failure",
                "details": f"Document failed check for {gate_name}.",
                "suggested_recovery": RECOVERIES.get(gate_number, "Review logic and re-run stage.")
            }
    except Exception as e:
        return {
            "status": "error",
            "gate": gate_name or str(gate_number),
            "error_type": "audit_execution_error",
            "details": str(e),
            "suggested_recovery": "Ensure files exist, path is safe, and API key is correct."
        }

@mcp.resource("audit://rules/{gate}")
def get_rule(gate: str) -> str:
    """
    Returns the rule text for the given gate number (1-22).
    """
    try:
        gate_num = int(gate)
        return RULES.get(gate_num, f"Unknown gate: {gate}")
    except ValueError:
        return f"Invalid gate number format: {gate}"

if __name__ == "__main__":
    sse, cleaned_argv = get_cleaned_args()
    sys.argv = cleaned_argv
    if sse:
        mcp.run(transport="sse", host="127.0.0.1", port=8012)
    else:
        mcp.run()

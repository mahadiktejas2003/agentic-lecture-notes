import sys
import os
from typing import Dict, Any

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mcp.server.fastmcp import FastMCP
from scripts.mcp_servers.auth import verify_auth, get_cleaned_args
from scripts.generate_docx import build_document as docx_builder

# Verify authentication on start
verify_auth()

mcp = FastMCP("Generate DOCX Server")

@mcp.tool()
def build_document(paths: Dict[str, str]) -> Dict[str, Any]:
    """
    Builds a docx document from the provided manifest paths.
    
    paths: A dictionary containing:
      - concept_map_path (default: concept_block_map.json)
      - frame_manifest_path (default: frame_manifest.json)
      - slide_manifest_path (default: slide_manifest.json)
      - output_path (default: notes-output/LECTURE_NOTES.docx)
    """
    concept_map_path = paths.get("concept_map_path", "concept_block_map.json")
    frame_manifest_path = paths.get("frame_manifest_path", "frame_manifest.json")
    slide_manifest_path = paths.get("slide_manifest_path", "slide_manifest.json")
    output_path = paths.get("output_path", "notes-output/LECTURE_NOTES.docx")
    
    errors = []
    try:
        success, archive_path = docx_builder(
            concept_map_path=concept_map_path,
            frame_manifest_path=frame_manifest_path,
            slide_manifest_path=slide_manifest_path,
            output_path=output_path
        )
        return {
            "success": success,
            "output_path": output_path,
            "archive_path": archive_path or "",
            "errors": errors
        }
    except Exception as e:
        errors.append(str(e))
        return {
            "success": False,
            "output_path": output_path,
            "archive_path": "",
            "errors": errors
        }

if __name__ == "__main__":
    sse, cleaned_argv = get_cleaned_args()
    sys.argv = cleaned_argv
    if sse:
        mcp.run(transport="sse", host="127.0.0.1", port=8011)
    else:
        mcp.run()

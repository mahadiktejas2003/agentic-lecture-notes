import sys
import os
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mcp.server.fastmcp import FastMCP
from scripts.mcp_servers.auth import verify_auth, get_cleaned_args
from scripts.extract_frames import extract_frames as run_extraction

# Verify authentication on start
verify_auth()

mcp = FastMCP("Extract Frames Server")

@mcp.tool()
def extract_frames(video_path: str, timestamps: List[str], output_dir: str) -> Dict[str, Any]:
    """
    Extracts frames from the video at specified timestamps and saves them to output_dir.
    
    video_path: Path to the input MP4 video file.
    timestamps: List of timestamps (e.g. ['00:03:30', '00:10:15']).
    output_dir: Directory where the extracted frame JPEG files will be stored.
    """
    try:
        success = run_extraction(
            video_path=video_path,
            timestamps=timestamps,
            output_dir=output_dir
        )
        return {
            "success": success,
            "manifest_path": "frame_manifest.json",
            "frame_count": len(timestamps) if success else 0
        }
    except Exception as e:
        return {
            "success": False,
            "manifest_path": "frame_manifest.json",
            "frame_count": 0,
            "error": str(e)
        }

if __name__ == "__main__":
    sse, cleaned_argv = get_cleaned_args()
    sys.argv = cleaned_argv
    if sse:
        mcp.run(transport="sse", host="127.0.0.1", port=8013)
    else:
        mcp.run()

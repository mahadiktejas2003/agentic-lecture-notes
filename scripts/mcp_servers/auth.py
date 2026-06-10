import os
import sys
import argparse

DEFAULT_KEY = "lecture_notes_secure_mcp_key_2026"

def verify_auth():
    # Parse known args without crashing on other FastMCP args
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--api-key", default=os.environ.get("MCP_API_KEY"))
    args, unknown = parser.parse_known_args()
    
    api_key = args.api_key
    if not api_key:
        print("Security Error: API key is missing. Specify it via the --api-key argument or MCP_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)
        
    if api_key != DEFAULT_KEY:
        print("Security Error: Invalid API key.", file=sys.stderr)
        sys.exit(1)
        
    print("Authentication successful.", file=sys.stderr)

def verify_request_auth(api_key: str = None):
    """
    Verify the api_key provided in a tool request against the expected key.
    Raises PermissionError on failure.
    """
    expected = os.environ.get("MCP_API_KEY") or DEFAULT_KEY
    if not api_key:
        raise PermissionError("Security Error: API key is missing from tool request.")
    if api_key != expected:
        raise PermissionError("Security Error: Invalid API key provided in tool request.")

def safe_path(path: str, base_dir: str = None) -> str:
    """
    Ensure the path is within base_dir (defaults to the project root directory)
    to prevent directory traversal.
    """
    if base_dir is None:
        # Resolve to project root (2 directories up from this file)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    # Resolve the absolute path
    abs_path = os.path.abspath(os.path.join(base_dir, path))
    # Check if the resolved path starts with the base directory
    if not abs_path.startswith(base_dir):
        raise ValueError(f"Security Error: Directory traversal detected for path: {path}")
    return abs_path

def get_cleaned_args():
    cleaned = []
    skip = False
    sse = False
    for arg in sys.argv:
        if skip:
            skip = False
            continue
        if arg == "--api-key":
            skip = True
            continue
        if arg == "--sse":
            sse = True
            continue
        cleaned.append(arg)
    return sse, cleaned

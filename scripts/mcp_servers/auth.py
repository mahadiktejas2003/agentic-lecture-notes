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

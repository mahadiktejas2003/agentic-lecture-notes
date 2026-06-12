#!/bin/bash
# start_mcp_servers.sh — Starts all three FastMCP servers in background using SSE transport.

WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$WORKSPACE_DIR" || exit 1

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found." >&2
    exit 1
fi

# Set default API key if not set
export MCP_API_KEY="${MCP_API_KEY:-lecture_notes_secure_mcp_key_2026}"

echo "Starting MCP servers with API Key..."
mkdir -p logs

# Port 8011: Document Builder
python3 scripts/mcp_servers/generate_docx_server.py --sse > logs/generate_docx_server.log 2>&1 &
DOCX_PID=$!

# Port 8012: Auditor
python3 scripts/mcp_servers/audit_server.py --sse > logs/audit_server.log 2>&1 &
AUDIT_PID=$!

# Port 8013: Frame Extractor
python3 scripts/mcp_servers/extract_frames_server.py --sse > logs/extract_frames_server.log 2>&1 &
FRAMES_PID=$!

echo "PIDs:"
echo "  generate_docx_server (Port 8011): $DOCX_PID"
echo "  audit_server         (Port 8012): $AUDIT_PID"
echo "  extract_frames_server (Port 8013): $FRAMES_PID"

echo "$DOCX_PID" > logs/generate_docx_server.pid
echo "$AUDIT_PID" > logs/audit_server.pid
echo "$FRAMES_PID" > logs/extract_frames_server.pid

echo "MCP Servers started successfully in background."

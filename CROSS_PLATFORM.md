# CROSS_PLATFORM.md

This guide explains how to run the dynamic note reconstruction pipeline across different IDEs and client platforms (Claude Code, Cursor, Claude Desktop, and general MCP clients).

## Prerequisites

Ensure python dependencies and system libraries are installed in the workspace environment:
```bash
source venv/bin/activate
pip install -r requirements-mcp.txt
```

## Running the Pipeline via CLI

To trigger the complete, self-healing LangGraph reconstruction pipeline directly from any terminal or client:
```bash
source venv/bin/activate
python3 scripts/langgraph_orchestrator.py
```

## Integrating Custom MCP Servers

You can expose the core capabilities of the pipeline (document generation, quality audit, and frame extraction) to your AI agent directly as MCP tools.

### Key Security Config
All MCP servers require an API Key handshake. The default expected key is `lecture_notes_secure_mcp_key_2026`. Specify it using the `MCP_API_KEY` environment variable or `--api-key` argument.

> [!CAUTION]
> **Production API Key Warning**: Never commit raw API keys, credentials, or custom tokens to git repositories. Always use environment variables or local configuration files to manage security keys.

### 1. Claude Code
Add the servers to your Claude Code developer setup:
```bash
# Register Document Builder Server
claude mcp add generate-docx python3 scripts/mcp_servers/generate_docx_server.py --env MCP_API_KEY=lecture_notes_secure_mcp_key_2026

# Register Auditor Server
claude mcp add audit-server python3 scripts/mcp_servers/audit_server.py --env MCP_API_KEY=lecture_notes_secure_mcp_key_2026

# Register Frame Extractor Server
claude mcp add extract-frames python3 scripts/mcp_servers/extract_frames_server.py --env MCP_API_KEY=lecture_notes_secure_mcp_key_2026
```

### 2. Cursor
Open Cursor Settings -> Features -> MCP, click **+ Add New MCP Server**, and configure each server:
* **Server 1 (Document Builder)**:
  - Name: `generate_docx`
  - Type: `command`
  - Command: `$HOME/Documents/agentic-lecture-notes/venv/bin/python scripts/mcp_servers/generate_docx_server.py`
  - Environment Variables (optional, or pass in args): `MCP_API_KEY=lecture_notes_secure_mcp_key_2026`
* **Server 2 (Auditor)**:
  - Name: `audit_server`
  - Type: `command`
  - Command: `$HOME/Documents/agentic-lecture-notes/venv/bin/python scripts/mcp_servers/audit_server.py`
  - Environment Variables (optional, or pass in args): `MCP_API_KEY=lecture_notes_secure_mcp_key_2026`
* **Server 3 (Frame Extractor)**:
  - Name: `extract_frames`
  - Type: `command`
  - Command: `$HOME/Documents/agentic-lecture-notes/venv/bin/python scripts/mcp_servers/extract_frames_server.py`
  - Environment Variables (optional, or pass in args): `MCP_API_KEY=lecture_notes_secure_mcp_key_2026`

### 3. Claude Desktop
Add the following configuration to `~/Library/Application Support/Claude/claude_desktop_config.json` (replace `$HOME` with the actual absolute path to your home directory):
```json
{
  "mcpServers": {
    "generate_docx": {
      "command": "$HOME/Documents/agentic-lecture-notes/venv/bin/python",
      "args": [
        "$HOME/Documents/agentic-lecture-notes/scripts/mcp_servers/generate_docx_server.py"
      ],
      "env": {
        "MCP_API_KEY": "lecture_notes_secure_mcp_key_2026"
      }
    },
    "audit_server": {
      "command": "$HOME/Documents/agentic-lecture-notes/venv/bin/python",
      "args": [
        "$HOME/Documents/agentic-lecture-notes/scripts/mcp_servers/audit_server.py"
      ],
      "env": {
        "MCP_API_KEY": "lecture_notes_secure_mcp_key_2026"
      }
    },
    "extract_frames": {
      "command": "$HOME/Documents/agentic-lecture-notes/venv/bin/python",
      "args": [
        "$HOME/Documents/agentic-lecture-notes/scripts/mcp_servers/extract_frames_server.py"
      ],
      "env": {
        "MCP_API_KEY": "lecture_notes_secure_mcp_key_2026"
      }
    }
  }
}
```

### 4. General/Remote MCP Clients (SSE Mode)
To run the servers as HTTP/SSE background daemons (e.g. for access via remote web UI or custom API clients):
```bash
./scripts/start_mcp_servers.sh
```
The endpoints will be available locally at:
* Document Builder: `http://127.0.0.1:8011`
* Auditor: `http://127.0.0.1:8012`
* Frame Extractor: `http://127.0.0.1:8013`

# MCP Server Security Protocol

This document describes the security and authentication mechanism implemented for the three custom Model Context Protocol (MCP) servers in the `agentic-lecture-notes` pipeline.

## Authentication Mechanism

All three servers (`generate_docx_server.py`, `audit_server.py`, and `extract_frames_server.py`) enforce API Key authentication at startup and request handling level.

1. **API Key Setup**:
   - The default fallback API key is `lecture_notes_secure_mcp_key_2026`.
   - To customize the key, set the environment variable `MCP_API_KEY`:
     ```bash
     export MCP_API_KEY="your_secure_api_key"
     ```

2. **Passing the Key**:
   - **Environment Variable**: Configure the host client to launch the servers with `MCP_API_KEY` defined in their environment.
   - **Command-Line Argument**: Pass the key directly during start as an argument:
     ```bash
     python3 scripts/mcp_servers/generate_docx_server.py --api-key your_secure_api_key
     ```

3. **Handshake Enforcement**:
   - The server module imports `scripts/mcp_servers/auth.py` and runs `verify_auth()` before starting `FastMCP`.
   - If the API key is missing or invalid, the process prints a security error to `stderr` and exits immediately with code `1`, causing the client's handshake initialization to fail securely.

## Deployments & Transports

### 1. Stdio Transport (Default)
When configured inside Cursor, Claude Code, or Claude Desktop, the server runs in standard input/output mode:
```json
{
  "mcpServers": {
    "generate_docx": {
      "command": "python3",
      "args": ["scripts/mcp_servers/generate_docx_server.py"],
      "env": {
        "MCP_API_KEY": "lecture_notes_secure_mcp_key_2026"
      }
    }
  }
}
```

### 2. SSE Transport (Background Mode)
When running as background services (e.g. via `scripts/start_mcp_servers.sh`), the servers run as HTTP/SSE endpoints on local loopback ports:
- **Document Builder Server**: `http://127.0.0.1:8011`
- **Auditor Server**: `http://127.0.0.1:8012`
- **Frame Extractor Server**: `http://127.0.0.1:8013`

# Agentic Lecture Notes Reconstruction

An autonomous, self-healing, cross-platform pipeline designed to reconstruct lecture materials (video, transcript, slide decks) into exam-ready notes in Word (.docx) format using the v8.0 Source Fidelity Protocol and LangGraph 1.x orchestration.

## Architecture

```mermaid
graph TD
    A[Antigravity Agent / Cron] -->|Auto-Ingests Downloads| B[lecture-input/]
    B -->|Reads Transcript & Visuals| C[LangGraph Orchestrator]
    
    C -->|Stage 1: Mapping| D[scripts/process_slides.py]
    C -->|Stage 2: Extraction| E[scripts/crop_frames.py]
    C -->|Stage 3: Generation & Tester| F[scripts/generate_docx.py]
    
    C -->|15-Gate Quality Audit| G[scripts/audit.py]
    G -->|Rollback on Fail| C
    
    C -->|Tools & Resources| H[FastMCP Servers]
    H -->|generate_docx| I[Port 8011]
    H -->|audit_server| J[Port 8012]
    H -->|extract_frames| K[Port 8013]
    
    C -->|Memory Layer| L[SQLite & failures/]
    L -->|Analyze Failures| M[scripts/skill_improver.py]
    M -->|Propose Diffs| N[proposed_skill_diffs/]
```

## Quick-Start

### 1. Installation
Ensure system requirements are met, activate the virtual environment, and install dependencies:
```bash
source venv/bin/activate
pip install -r requirements-mcp.txt
```

### 2. Run Note Reconstruction Pipeline
To trigger the complete, self-healing LangGraph note reconstruction:
```bash
python3 scripts/langgraph_orchestrator.py
```

### 3. Launch Custom MCP Servers
To run the background servers locally using the SSE transport:
```bash
./scripts/start_mcp_servers.sh
```

### 4. Continuous Self-Improvement
Analyze pipeline abort files and propose skill improvements:
```bash
python3 scripts/skill_improver.py
```

For more detailed guides, refer to:
- [CLAUDE.md](file:///Users/tejasmahadik/Documents/agentic-lecture-notes/CLAUDE.md): Notes writing rules and Source Fidelity constraints.
- [CROSS_PLATFORM.md](file:///Users/tejasmahadik/Documents/agentic-lecture-notes/CROSS_PLATFORM.md): IDE integration instructions for Cursor, Claude Code, and Claude Desktop.
- [MCP_SECURITY.md](file:///Users/tejasmahadik/Documents/agentic-lecture-notes/MCP_SECURITY.md): Details on the API-key authentication system.

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
    
    C -->|19-Gate Quality Audit| G[scripts/audit.py]
    G -->|Rollback on Fail| C
    
    C -->|Tools & Resources| H[FastMCP Servers]
    H -->|generate_docx| I[Port 8011]
    H -->|audit_server| J[Port 8012]
    H -->|extract_frames| K[Port 8013]
    
    C -->|Memory Layer| L[SQLite & failures/]
    L -->|Analyze Failures| M[scripts/skill_improver.py]
    M -->|Propose Diffs| N[proposed_skill_diffs/]
```

## How It Works

The note reconstruction pipeline operates autonomously through the following steps:

### 1. Dynamic vs. Fallback Manifest Selection (Topic-Specific Matching)
When a lecture transcript is ingested, the system reads its contents to determine if it matches a known lecture (e.g., searching for "scheduling" to identify the CPU Scheduling lecture).
- **Fallback Manifests**: If a matching known lecture is detected, the orchestrator immediately loads pre-built manifests ([fallback_concept_block_map.json](scripts/fallback_concept_block_map.json) and [fallback_frame_manifest.json](scripts/fallback_frame_manifest.json)) to skip unnecessary reasoning steps and accelerate execution.
- **Dynamic Manifests**: If the lecture is unknown, the pipeline falls back to dynamic generation, analyzing the transcript and visual assets dynamically.

### 2. Antigravity CLI Integration for Unknown Lectures
For unknown lectures without offline fallbacks, the orchestrator invokes the local `antigravity` CLI tool to analyze the transcript. The CLI reads the transcript at `lecture-input/transcript.srt`, identifies key concept blocks under the v8.0 Source Fidelity Protocol, and extracts visual anchor points, outputting new `concept_block_map.json` and `frame_manifest.json` files dynamically.

### 3. The 4-Hour Scheduler and Heartbeat Timeout
An autonomous cron scheduler runs every 4 hours. It performs the following duties:
- Wakes up and triggers [auto_ingest.sh](scripts/auto_ingest.sh) to check for new files.
- If files are found, it copies them and attempts to trigger the reconstruction.
- Incorporates a heartbeat mechanism where the main pipeline execution is monitored. If execution stalls beyond the designated heartbeat threshold, it aborts to prevent resource lockup and writes diagnostic fail logs to `agent_memory/failures/`.

### 4. Timestamped Archive Copies
To ensure work is never overwritten by subsequent runs, every successful execution of [generate_docx.py](scripts/generate_docx.py) creates both:
- A primary target notes file at `notes-output/LECTURE_NOTES.docx`.
- A unique, sanitized, and timestamped copy in `notes-output/` (e.g., `LECTURE_NOTES_OSI_Layers_2026-06-06_18-00-00.docx`) based on the lecture title, preserving a complete history of the reconstructed materials.

## Workspace Directory Structure

To maintain a clean and structured repository, the workspace is organized as follows:

### 📁 Workspace Folders
- `lecture-input/`: The active inputs (`LECTURE.mp4`, `REFERENCE_NOTES.pdf`, `SLIDES.pdf`, `transcript.srt`).
- `notes-output/`: Reconstructed Word documents and timestamped archives.
- `scripts/`: Source code Python scripts for extraction, mapping, composition, and quality audits.
- `web_ui/`: FastAPI web server and UI frontend.
- `backups/`: Consolidated lecture-specific backup inputs.
- `scratch/`: One-off scratch files and scripts.
- `sandbox/`: TCS iON testing sandboxes.
- `logs/`: Application execution logs and SQLite checkpoint databases.
- `agent_memory/`: Long-term memory store and fail logs.

### 🖼️ Active Generated Image Folders
The following generated image directories are maintained at the root level to support document image insertion paths:
- `screenshots/`: Extracted video keyframes.
- `reference_screenshots/`: Image assets extracted from the reference notes PDF.
- `slides/`: Rendered slides PDF pages.
- `reference_pages/`: Rendered reference notes PDF pages.

### 📄 Active JSON Manifests
The following active manifest files are maintained at the root level to coordinate data flow between pipeline stages:
- `workspace_state.json`: Central state tracking database.
- `concept_block_map.json`: Chronological segment outline map.
- `frame_manifest.json`: Video keyframe timestamps and OCR texts.
- `slide_manifest.json`: Slides-to-transcript mapping data.
- `reference_manifest.json`: Reference notes OCR text.
- `embedded_manifest.json`: Reference notes embedded image data.
- `inserted_images.json`: Log of images inserted in the active notes document.
- `lecture_profile.json`: Lecture type classification parameters.

## Quick-Start & Local ASR Studio

This project includes a 100% free, private, offline speech-to-text system. It uses Apple Silicon MLX GPU acceleration via `mlx-qwen3-asr` to run the **Qwen3-ASR-1.7B (8-bit quantized)** model natively on your Mac M4.

### 1. Installation
Activate the virtual environment and install the required dependencies (including native MLX ASR modules):
```bash
source venv/bin/activate
pip install -r requirements-mcp.txt
```

### 2. Local ASR CLI Usage
Transcribe any video or audio file locally. The script automatically extracts audio tracks using `ffmpeg` and generates matched `.srt` and `.txt` files:

*   **Fast Phrase-Level Subtitles (No Aligner)**:
    Runs in ~11 seconds for a 60s clip by utilizing native silence energy chunking. Highly recommended for general transcription:
    ```bash
    python scripts/transcribe_lecture.py --input lecture-input/LECTURE.mp4 --language hi
    ```
*   **Exact Word-Level Timestamps (With Aligner)**:
    Requires downloading `Qwen3-ForcedAligner-0.6B` (~1.84 GB) on the first run for precise token alignment:
    ```bash
    python scripts/transcribe_lecture.py --input lecture-input/LECTURE.mp4 --language hi --timestamps
    ```

### 3. Running the OpenAI-Compatible API Server (Optional/Standalone)
You can start a local OpenAI-compatible API server. It exposes standard `/v1/audio/transcriptions` endpoints, allowing external OpenAI SDK clients or other apps to use it. Start it on port `8001` (completely optional and standalone; not required for the Web UI or note pipeline):
```bash
mlx-qwen3-asr serve --model mlx-community/Qwen3-ASR-1.7B-8bit --host 127.0.0.1 --port 8001 --api-key local > logs/asr_server.log 2>&1 &
```
*   **Test health check**: `curl http://127.0.0.1:8001/health`
*   **API authorization header**: `Authorization: Bearer local`

### 4. Running the Tabbed Web UI
The Web UI directly invokes the underlying `scripts/transcribe_lecture.py` script via a background process (it does **not** require the optional port 8001 server to be running).
To start the Web UI (redesigned with a premium glassmorphic dark theme and a live execution log console):
```bash
python web_ui/app.py
```
Open **`http://localhost:8000`** in your browser.
*   **Tab 1: Notes Reconstruction**: Upload your lecture assets. Leaving the transcript input blank auto-triggers local Qwen3-ASR.
*   **Tab 2: ASR-Only Speech-to-Text**: Upload any video/audio track to get downloadable `.srt` and `.txt` transcripts instantly, without affecting note-making pipeline runs.

### 5. System-wide / PC-level Transcription & Launchers
To run transcription or launch the Web UI from anywhere on your Mac without `cd`'ing into this directory, we have created standalone wrapper scripts:
- **CLI Transcription wrapper**: [scripts/qwen-transcribe.sh](scripts/qwen-transcribe.sh)
- **UI Launcher wrapper**: [scripts/qwen-ui.sh](scripts/qwen-ui.sh)
- **Standalone Studio Launcher**: [scripts/qwen-asr-studio.sh](scripts/qwen-asr-studio.sh) (Starts the Web UI and opens your browser automatically)

You can make them accessible globally by creating symlinks in your local `bin` directory:
```bash
mkdir -p ~/.local/bin
ln -sf "/Users/tejasmahadik/Documents/agentic-lecture-notes/scripts/qwen-transcribe.sh" ~/.local/bin/qwen-transcribe
ln -sf "/Users/tejasmahadik/Documents/agentic-lecture-notes/scripts/qwen-asr-studio.sh" ~/.local/bin/qwen-asr-studio
```
Make sure `~/.local/bin` is in your `$PATH`. After reloading your shell, you can run `qwen-transcribe --input /path/to/any_video.mp4 --language hi` or simply run `qwen-asr-studio` from any terminal window.

### 6. Running the Note Reconstruction Pipeline (CLI)
To trigger the complete, self-healing LangGraph note reconstruction manually:
```bash
python3 scripts/langgraph_orchestrator.py
```

### 6. Troubleshooting
*   **CUDA/NVIDIA Error**: Do NOT use CUDA-only backends (like raw vLLM Docker images) on Apple Silicon. This project uses native MLX, which communicates directly with Apple's Metal GPU.
*   **Memory Growth on Long Videos**: Native `mlx-qwen3-asr` recursively slices audio at silence boundaries and clears the Metal GPU cache after every chunk. If you observe memory leak errors, ensure your `mlx-qwen3-asr` package is updated to `>=0.3.5`.
*   **Forced Aligner download hang**: If the 1.84 GB aligner model download halts due to network speed, re-run *without* `--timestamps`. It will complete instantly using acoustic chunk-level boundary files.

For more detailed guides, refer to:
- [CLAUDE.md](CLAUDE.md): Notes writing rules and Source Fidelity constraints.
- [CROSS_PLATFORM.md](CROSS_PLATFORM.md): IDE integration instructions for Cursor, Claude Code, and Claude Desktop.
- [MCP_SECURITY.md](MCP_SECURITY.md): Details on the API-key authentication system.
- [FINAL_ARCHITECTURE.md](docs/architecture/FINAL_ARCHITECTURE.md): Comprehensive system architecture specifications.
- [PROJECT_MEMORY.md](docs/architecture/PROJECT_MEMORY.md): Knowledge base and fail-safe patterns.
- [DEPLOYMENT_STRATEGY.md](docs/architecture/DEPLOYMENT_STRATEGY.md): Cloud storage and multi-agent setup guides.
- [SETUP_FREE_FOREVER.md](docs/architecture/SETUP_FREE_FOREVER.md): Free-tier pricing optimization and Mac M4 setup instructions.

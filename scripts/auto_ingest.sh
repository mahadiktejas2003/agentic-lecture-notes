#!/bin/bash
# auto_ingest.sh — Autonomous Ingestion Daemon Script
# Checks Downloads directory for new lecture files, ingests them, and triggers the process.

DOWNLOADS_DIR="/Users/tejasmahadik/Downloads"
WORKSPACE_DIR="/Users/tejasmahadik/Documents/agentic-lecture-notes"

echo "Checking for new lecture materials in $DOWNLOADS_DIR..."

# Find the latest PDF, MP4, and SRT matching lecture patterns
LATEST_PDF=$(ls -t "$DOWNLOADS_DIR"/*.pdf 2>/dev/null | head -n 1 || true)
LATEST_MP4=$(ls -t "$DOWNLOADS_DIR"/*.mp4 2>/dev/null | head -n 1 || true)
LATEST_SRT=$(ls -t "$DOWNLOADS_DIR"/*.srt 2>/dev/null | head -n 1 || true)

if [ -n "$LATEST_MP4" ] && [ -n "$LATEST_SRT" ]; then
    echo "Found new potential lecture files:"
    echo "  MP4: $LATEST_MP4"
    echo "  SRT: $LATEST_SRT"
    
    # Copying mandatory files
    cp "$LATEST_MP4" "$WORKSPACE_DIR/lecture-input/LECTURE.mp4"
    cp "$LATEST_SRT" "$WORKSPACE_DIR/lecture-input/transcript.srt"
    
    # Copying optional PDF slide deck if available
    if [ -n "$LATEST_PDF" ]; then
        echo "  PDF: $LATEST_PDF (optional)"
        cp "$LATEST_PDF" "$WORKSPACE_DIR/lecture-input/SLIDES.pdf"
    else
        echo "  No optional PDF slide deck found. Skipping PDF copy."
        rm -f "$WORKSPACE_DIR/lecture-input/SLIDES.pdf"
    fi
    
    echo "Successfully ingested files into lecture-input/"
    
    # Execute composition pipeline steps individually if manifests exist
    if [ -f "concept_block_map.json" ] && [ -f "frame_manifest.json" ]; then
        echo "Found existing manifests. Running local composition..."
        source venv/bin/activate
        python3 scripts/generate_docx.py --concept-map concept_block_map.json --frame-manifest frame_manifest.json --slide-manifest slide_manifest.json --output notes-output/LECTURE_NOTES.docx
        python3 scripts/audit.py --docx notes-output/LECTURE_NOTES.docx --concept-map concept_block_map.json --frame-manifest frame_manifest.json --slide-manifest slide_manifest.json
    else
        echo "========================================================================="
        echo "Manifests not found. To dynamically map and reconstruct this new lecture,"
        echo "open the Antigravity chat and run the following command autonomously:"
        echo "  Process the new lecture files currently in Downloads. Run with /goal."
        echo "========================================================================="
    fi
else
    echo "No new lecture files (MP4 and SRT) found in Downloads."
fi

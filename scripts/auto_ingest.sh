#!/bin/bash
# auto_ingest.sh — Autonomous Ingestion Daemon Script
# Checks Downloads directory for new lecture files, ingests them, and triggers the process.

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WORKSPACE_DIR"

# Activate virtualenv if available
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the smart ingestion python script
python3 scripts/smart_ingest.py

if [ $? -eq 0 ]; then
    echo "Ingestion completed successfully."
    
    # Execute composition pipeline steps individually if manifests exist
    if [ -f "concept_block_map.json" ] && [ -f "frame_manifest.json" ]; then
        echo "Found existing manifests. Running local composition..."
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
    echo "No new matching lecture files found in Downloads."
fi


#!/bin/bash
# Global CLI wrapper script to transcribe audio/video using Qwen3-ASR on Apple Silicon GPU

PROJECT_DIR="/Users/tejasmahadik/Documents/agentic-lecture-notes"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
TRANSCRIBE_SCRIPT="$PROJECT_DIR/scripts/transcribe_lecture.py"

if [ "$#" -lt 1 ]; then
    echo "Usage: qwen-transcribe --input <video_or_audio_path> [options]"
    echo "Example: qwen-transcribe --input lecture.mp4 --language hi"
    exit 1
fi

# Run the python script with all passed arguments using the virtual environment's python
exec "$VENV_PYTHON" "$TRANSCRIBE_SCRIPT" "$@"

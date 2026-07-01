#!/bin/bash
# Standalone Launcher for the premium ASR Web UI

PROJECT_DIR="/Users/tejasmahadik/Documents/agentic-lecture-notes"
cd "$PROJECT_DIR" || exit 1

echo "Starting Web UI on port 8000..."
source venv/bin/activate

# Start in background
python web_ui/app.py &
UI_PID=$!

echo "Waiting for server to start..."
sleep 2

echo "Opening browser..."
open http://127.0.0.1:8000

# Wait for process
wait $UI_PID

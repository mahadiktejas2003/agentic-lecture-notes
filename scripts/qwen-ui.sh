#!/bin/bash
# Launcher for the premium ASR Web UI

PROJECT_DIR="/Users/tejasmahadik/Documents/agentic-lecture-notes"
cd "$PROJECT_DIR" || exit 1
source venv/bin/activate
exec python web_ui/app.py

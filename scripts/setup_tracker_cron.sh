#!/bin/bash
# setup_tracker_cron.sh
# Sets up the macOS cron job for tracking the Downloads folder and running the notes pipeline.

PROJECT_DIR="/Users/tejasmahadik/Documents/agentic-lecture-notes"
PYTHON_BIN="$PROJECT_DIR/venv/bin/python"
TRACKER_SCRIPT="$PROJECT_DIR/scripts/downloads_tracker.py"
LOG_FILE="$PROJECT_DIR/logs/tracker.log"

# Define the cron line
CRON_LINE="*/10 7-12 * * * cd $PROJECT_DIR && $PYTHON_BIN $TRACKER_SCRIPT >> $LOG_FILE 2>&1"

# Check if the cron job already exists
if crontab -l 2>/dev/null | grep -F "$TRACKER_SCRIPT" >/dev/null; then
    echo "Downloads folder tracker cron job is already configured."
else
    echo "Configuring cron job to run downloads_tracker.py every 10 minutes between 7 AM and 1 PM..."
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Cron job configured successfully!"
fi

# Print current crontab for verification
echo "Current crontab configuration:"
crontab -l

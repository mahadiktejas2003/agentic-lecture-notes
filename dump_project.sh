#!/bin/bash

# =============================================================================
# PROJECT DUMP COMMAND FOR MAC M4 AIR
# Creates a single text file with ALL source code (excluding binaries)
# Optimized for AI context sharing
# =============================================================================

set -e  # Exit on error

# Configuration
PROJECT_DIR="/Users/tejasmahadik/Documents/agentic-lecture-notes"
OUTPUT_FILE="$HOME/Downloads/agentic-source-context.txt"
EXCLUDE_DIRS=("venv" ".git" "node_modules" "__pycache__" "agent_memory" 
              "lecture-input" "notes-output" "screenshots" "slides" "scratch")
EXCLUDE_EXTS=("mp4" "mov" "avi" "mkv" "srt" "vtt" "jpg" "jpeg" "png" "gif" 
              "webp" "pdf" "pptx" "docx" "xlsx" "mp3" "wav" "m4a" "flac" 
              "pyc" "pyo" "so" "dylib" "DS_Store")

echo "🧠 Agentic Lecture Notes - Full Source Dump"
echo "============================================"
echo ""

# Navigate to project directory
cd "$PROJECT_DIR" || { echo "❌ Project directory not found!"; exit 1; }

# Create output file with header
{
    echo "# 📂 AGENTIC LECTURE NOTES - FULL SOURCE CONTEXT"
    echo "# 📅 Generated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "# 💻 Machine: $(hostname)"
    echo "# ⚠️ EXCLUDED: Videos, Images, PDFs, Notes, Transcripts, Logs, Venv, Git"
    echo ""
    echo "## 📁 PROJECT STRUCTURE"
    echo ""
    
    # Show directory tree (excluding binary folders)
    find . \
        $(for dir in "${EXCLUDE_DIRS[@]}"; do echo "-not -path './$dir/*'"; done) \
        $(for ext in "${EXCLUDE_EXTS[@]}"; do echo "-not -name '*.$ext'"; done) \
        -type f | sort | while read -r file; do
        echo "  $file"
    done
    
    echo ""
    echo "## 📄 FILE CONTENTS"
    echo ""
    
    # Dump each file's content
    find . \
        $(for dir in "${EXCLUDE_DIRS[@]}"; do echo "-not -path './$dir/*'"; done) \
        $(for ext in "${EXCLUDE_EXTS[@]}"; do echo "-not -name '*.$ext'"; done) \
        -type f | sort | while read -r file; do
        
        # Skip if file is empty or doesn't exist
        [ ! -f "$file" ] && continue
        
        echo "================================================================================"
        echo "FILE: $file"
        echo "================================================================================"
        
        # Try to cat the file, skip if binary
        if file "$file" | grep -q "text\|empty\|JSON\|ASCII"; then
            cat "$file" 2>/dev/null || echo "[Error reading file]"
        else
            echo "[Skipped: Binary or non-text file]"
        fi
        
        echo ""
        echo ""
    done
    
} > "$OUTPUT_FILE"

# Display results
echo "✅ SUCCESS!"
echo ""
echo "📂 Output Location: $OUTPUT_FILE"
echo "📏 File Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo "📄 Line Count: $(wc -l < "$OUTPUT_FILE" | tr -d ' ')"
echo "📝 Character Count: $(wc -c < "$OUTPUT_FILE" | tr -d ' ')"
echo ""
echo "🎯 Ready to share with AI agents!"
echo ""
echo "💡 Pro Tip: Upload this file to Claude/Cursor/GitHub Copilot for full project context."
echo ""

# Optional: Compress for easier sharing
if command -v gzip &> /dev/null; then
    COMPRESSED_FILE="${OUTPUT_FILE}.gz"
    gzip -k "$OUTPUT_FILE"
    echo "📦 Compressed version also created: ${COMPRESSED_FILE} ($(du -h "$COMPRESSED_FILE" | cut -f1))"
fi

echo ""
echo "✨ Done!"

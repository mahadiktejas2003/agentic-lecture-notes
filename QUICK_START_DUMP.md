# 🚀 QUICK START - MAC M4 AIR

## One-Line Project Dump Command

Copy and paste this into your Mac terminal to get the complete project source code in one file:

```bash
cd /Users/tejasmahadik/Documents/agentic-lecture-notes && find . -not -path './venv/*' -not -path './.git/*' -not -path './node_modules/*' -not -path './__pycache__/*' -not -path './agent_memory/*' -not -path './lecture-input/*' -not -path './notes-output/*' -not -path './screenshots/*' -not -path './slides/*' -not -path './scratch/*' -type f -not -name '*.mp4' -not -name '*.mov' -not -name '*.avi' -not -name '*.mkv' -not -name '*.srt' -not -name '*.vtt' -not -name '*.jpg' -not -name '*.jpeg' -not -name '*.png' -not -name '*.gif' -not -name '*.webp' -not -name '*.pdf' -not -name '*.pptx' -not -name '*.docx' -not -name '*.xlsx' -not -name '*.mp3' -not -name '*.wav' -not -name '*.m4a' -not -name '*.flac' -not -name '*.pyc' -not -name '*.pyo' -not -name '*.so' -not -name '*.dylib' -not -name '.DS_Store' -print | sort | while read f; do echo "================================================================================"; echo "FILE: $f"; echo "================================================================================"; cat "$f" 2>/dev/null || echo "[Skipped]"; echo ""; done > ~/Downloads/agentic-source-context.txt && echo "✅ Done! File saved to ~/Downloads/agentic-source-context.txt ($(du -h ~/Downloads/agentic-source-context.txt | cut -f1))"
```

---

## Alternative: Using the Script

```bash
# Make executable (first time only)
chmod +x /Users/tejasmahadik/Documents/agentic-lecture-notes/dump_project.sh

# Run the dump script
/Users/tejasmahadik/Documents/agentic-lecture-notes/dump_project.sh
```

---

## What Gets Included?

✅ **INCLUDED:**
- All Python scripts (`.py`)
- All Markdown docs (`.md`)
- All JSON configs (`.json`)
- All YAML files (`.yml`, `.yaml`)
- All shell scripts (`.sh`)
- All Dockerfiles
- All requirements files

❌ **EXCLUDED:**
- Videos (`.mp4`, `.mov`, `.avi`, `.mkv`)
- Transcripts (`.srt`, `.vtt`)
- Images (`.jpg`, `.png`, `.gif`, `.webp`)
- PDFs, PPTX, DOCX
- Audio files (`.mp3`, `.wav`, `.m4a`)
- Compiled files (`.pyc`, `.so`, `.dylib`)
- Virtual environments (`venv/`)
- Git history (`.git/`)
- Generated outputs (`notes-output/`, `screenshots/`)

---

## Output File Location

```
~/Downloads/agentic-source-context.txt
```

This single file contains your entire project's source code, ready to share with AI agents for analysis, debugging, or enhancement!

---

## Next Steps After Dump

1. **Upload to AI**: Share `agentic-source-context.txt` with Claude/Cursor/GitHub Copilot
2. **Ask for Analysis**: "Analyze this agentic lecture notes pipeline and suggest improvements"
3. **Request Features**: "Add flashcard generation to this system"
4. **Debug Issues**: "Why is Gate 7 failing in the audit phase?"

---

## Full Setup Commands

To set up the entire "Free Forever" stack on your Mac M4 Air:

```bash
# 1. Navigate to project
cd /Users/tejasmahadik/Documents/agentic-lecture-notes

# 2. Create .env file with your credentials
nano .env
# (Paste credentials from Cloudflare R2 + Supabase)

# 3. Build Docker containers
docker-compose build

# 4. Launch all services
docker-compose up -d

# 5. Access Web UI
open http://localhost:3000
```

See `SETUP_FREE_FOREVER.md` for detailed instructions!

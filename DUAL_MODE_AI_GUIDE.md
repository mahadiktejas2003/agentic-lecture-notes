# 🤖 DUAL-MODE AI INTEGRATION GUIDE

**Version:** 1.0  
**Last Updated:** June 10, 2026  
**Purpose:** Enable flexible AI processing using BOTH direct API calls AND external IDE tools

---

## 🎯 OVERVIEW

This project supports **TWO complementary modes** of AI integration:

| Mode | Description | Best For | Tools Used |
|------|-------------|----------|------------|
| **Mode A: Direct API** | Automated pipeline calls to cloud AI services | Batch processing, overnight runs, CI/CD | Gemini 2.0 Flash, Groq, Claude API, Ollama |
| **Mode B: External Tools** | Manual invocation via IDE extensions & CLI tools | Interactive debugging, custom prompts, human-in-the-loop | Codex 5.5, Claude Code, Cursor, Antigravity 2.0 |

**You can use BOTH modes simultaneously!** The pipeline is designed to accept input from either source.

---

## 🔧 MODE A: DIRECT API CALLS (Automated)

### Setup
1. Install dependencies:
```bash
pip install google-genai groq anthropic python-dotenv
```

2. Create `.env` file with your API keys:
```bash
GEMINI_API_KEY="your_key_here"
GROQ_API_KEY="your_key_here"
ANTHROPIC_API_KEY="your_key_here"
```

3. Run the AI services module:
```bash
python scripts/ai_services.py
```

### What It Handles
- **Batch OCR**: Extract text from 50+ frames using Gemini 2.0 Flash Vision
- **Concept Mapping**: Generate structured JSON from transcript + OCR + slides
- **Note Composition**: Format content into exam-ready DOCX with Source Fidelity checks
- **Fallback Chain**: Gemini → Groq → Claude → Ollama (automatic failover)

### Code Example
```python
from scripts.ai_services import AIServices

ai = AIServices()

# Batch OCR
frames = ["frame_001.jpg", "frame_002.jpg", ...]
ocr_results = ai.perform_batch_ocr(frames)

# Generate concept map
concept_map = ai.generate_concept_map(
    transcript="Welcome to lecture on...",
    ocr_results=ocr_results,
    slides_text="Slide 1: Introduction..."
)
```

---

## 🛠️ MODE B: EXTERNAL AI TOOLS (Manual/Interactive)

### Supported Tools

#### 1. **Codex 5.5** (VS Code Extension)
- **Use Case**: Real-time code assistance, debugging pipeline errors
- **Invocation**: `Cmd+Shift+P` → "Codex: Explain This Code"
- **Context**: Automatically reads `.agents/skills/*.md` for style guidance

#### 2. **Claude Code** (CLI Tool)
- **Use Case**: Complex reasoning tasks, skill improvement proposals
- **Invocation**:
```bash
claude-code --prompt "Analyze this failed audit log and propose a fix for the transcript-mapping skill"
```
- **Context**: Provide `agent_memory/run_*.json` as input

#### 3. **Cursor** (AI-Powered IDE)
- **Use Case**: Refactoring Python scripts, generating test cases
- **Features**: 
  - `Cmd+K`: Inline code generation
  - `Cmd+L`: Chat with entire codebase context
  - Auto-reads `CLAUDE.md` for Source Fidelity rules

#### 4. **Antigravity 2.0** (Custom Extension)
- **Use Case**: Legacy transcript mapping, fallback concept generation
- **Invocation**: 
```bash
antigravity map --transcript lecture.srt --output concept_map.json
```
- **Note**: Being phased out in favor of `ai_services.py`, but still supported for backward compatibility

### Workflow Integration

When using external tools, follow this pattern:

1. **Dump Context**: Use the project dump command to create a single file for AI analysis:
```bash
cd /Users/tejasmahadik/Documents/agentic-lecture-notes
find . -not -path './venv/*' -not -path './.git/*' -not -path './lecture-input/*' -not -path './notes-output/*' -type f | sort | while read f; do echo "=== $f ==="; cat "$f"; done > ~/Downloads/project-context.txt
```

2. **Upload to AI**: Paste `project-context.txt` into Claude/Codex/Cursor chat

3. **Execute Suggestions**: Manually apply generated fixes or run suggested commands

4. **Log Results**: Save outcomes to `agent_memory/manual_intervention_YYYYMMDD.json`

---

## 🔄 HYBRID WORKFLOW EXAMPLE

Here's how to combine both modes for maximum efficiency:

### Scenario: Processing a New Lecture

1. **Step 1 (Automated)**: Run local pipeline up to frame extraction
```bash
python scripts/extract_frames.py --video lecture-input/new_lecture.mp4
```

2. **Step 2 (Manual)**: Use Claude Code to verify frame quality
```bash
claude-code --prompt "Review these 25 extracted frames in screenshots/. Are any blurry or missing text? Suggest cropping parameters."
```

3. **Step 3 (Automated)**: Run batch OCR via API
```bash
python scripts/ai_services.py --task ocr --input screenshots/
```

4. **Step 4 (Manual)**: Use Cursor to refine concept map
```bash
# Open concept_block_map.json in Cursor
# Cmd+L: "Improve this concept map structure based on Source Fidelity Protocol"
```

5. **Step 5 (Automated)**: Complete pipeline with audit
```bash
python scripts/langgraph_orchestrator.py --watch
```

---

## 📋 BEST PRACTICES

### When to Use Mode A (Direct API)
- ✅ Processing multiple lectures in batch
- ✅ Overnight/unsupervised runs
- ✅ CI/CD pipelines and automated testing
- ✅ Standard OCR and mapping tasks

### When to Use Mode B (External Tools)
- ✅ Debugging failed audits or pipeline crashes
- ✅ Handling edge cases (poor audio, handwritten slides)
- ✅ Improving agent skills based on failure patterns
- ✅ Custom prompt engineering for specific subjects

### Security Notes
- 🔒 Never commit `.env` file to GitHub
- 🔒 Rotate API keys every 90 days
- 🔒 Use Docker secrets for production deployments
- 🔒 Validate all AI-generated code before execution

---

## 🚀 QUICK START COMMANDS

### Test Direct API (Mode A)
```bash
cd /Users/tejasmahadik/Documents/agentic-lecture-notes
cp .env.example .env
# Edit .env with your keys
python scripts/ai_services.py
```

### Invoke Claude Code (Mode B)
```bash
claude-code --prompt "Review the last failed run in agent_memory/ and suggest fixes"
```

### Dump Project for AI Analysis
```bash
find . -not -path './venv/*' -not -path './.git/*' -not -path './lecture-input/*' -not -path './notes-output/*' -type f | sort | while read f; do echo "=== $f ==="; cat "$f"; done > ~/Downloads/project-dump.txt
```

---

## 📚 ADDITIONAL RESOURCES

- `scripts/ai_services.py` - Direct API implementation
- `.agents/skills/*.md` - Skill definitions for external AI reference
- `CLAUDE.md` - Source Fidelity Protocol (share with external AIs)
- `agent_memory/` - Run logs for debugging
- `CRITICAL_FIXES_APPLIED.md` - Recent security and routing fixes

---

**Remember**: The goal is **flexibility**. Use Mode A for automation, Mode B for creativity and problem-solving. Both modes respect the same Source Fidelity Protocol v8.0 to ensure consistent, hallucination-free output.

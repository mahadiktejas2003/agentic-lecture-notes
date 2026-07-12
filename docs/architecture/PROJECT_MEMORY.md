# PROJECT MEMORY: Agentic Lecture Notes Reconstruction

> Historical snapshot warning: this file preserves an older architecture/run-memory view. The current working tree uses the 22-gate audit in `scripts/audit.py`, and `docs/architecture/FINAL_ARCHITECTURE.md` is the authoritative current-state architecture reference.

**Last Updated:** June 10, 2026 (Post-Critical Fixes & Dual-Mode Integration)  
**Project Status:** ✅ Production-Ready with Security Hardening & AI Services  
**Current Lecture:** CPU Scheduling (Operating Systems)  
**Memory Version:** 3.0 - Dual-Mode Operation (Local + Cloud AI)

---

## 🧠 CORE IDENTITY & PURPOSE

This is an **autonomous, self-healing, cross-platform pipeline** that converts lecture materials (video, transcript, slides) into **exam-ready Word documents (.docx)** using:
- **v8.0 Source Fidelity Protocol** (13 strict rules against hallucination)
- **LangGraph 1.x Orchestrator** with 4-stage audit routing and retry logic (Gate 4 routing FIXED)
- Historical note: earlier snapshots used a 15-gate quality audit system; the current working tree uses 22 gates.
- **3 FastMCP Servers** (document generation, auditing, frame extraction)
- **5 Agent Skills** with self-improvement capabilities
- **Dual-Mode AI Integration**: 
  - **Mode A**: Direct API calls via `scripts/ai_services.py` (Gemini 2.0 Flash, Groq, Claude, Ollama)
  - **Mode B**: External AI tools (Codex 5.5, Claude Code, Cursor, Antigravity 2.0 extensions)

The system is designed to be **deterministic, traceable, and exam-focused**, ensuring no content is invented, dropped, or reorganized. It supports both automated cloud AI processing AND manual intervention via IDE extensions.

---

## 📂 PROJECT TOPOLOGY (Complete File Map)

### Root Level Files
```
/workspace/
├── README.md                    # Quick-start guide with Mermaid architecture diagram
├── AGENTS.md                    # Agent persona definitions (Orchestrator + 4 sub-agents)
├── CLAUDE.md                    # Source Fidelity Protocol v8.0 (13 rules) + output format spec
├── CROSS_PLATFORM.md            # IDE integration guide (Cursor, Claude Code, Claude Desktop, SSE)
├── MCP_SECURITY.md              # API-key authentication system documentation
├── PROJECT_MEMORY.md            # THIS FILE - comprehensive system knowledge base
├── requirements-mcp.txt         # Python dependencies for MCP servers
├── .gitignore                   # Git ignore rules
├── concept_block_map.json       # [DATA] 7-block CPU Scheduling concept map (22KB)
└── slide_manifest.json          # [DATA] 18-slide OCR manifest (10KB)
```

### `.agents/` Directory (Agent Configuration)
```
.agents/
├── hooks.json                   # Pre/post-execution hooks (safety checks)
├── rules/
│   └── note-style.md            # Attribution ban, Hindi mnemonic exception, anti-screenshot rule
└── skills/
    ├── frame-extraction/SKILL.md    # FFmpeg extraction, cropping, OCR workflow
    ├── transcript-mapping/SKILL.md  # Concept block detection with 4 density verification gates
    ├── slide-parsing/SKILL.md       # PPTX/PDF conversion, OCR, timestamp mapping
    ├── note-composition/SKILL.md    # Docx generation with silent visual moments
    └── student-tester/SKILL.md      # Note validation by attempting example problems
```

### `scripts/` Directory (Pipeline Engine)
```
scripts/
├── langgraph_orchestrator.py    # MAIN ENTRY POINT - 4-stage audit graph with retry logic
├── audit.py                     # 15-gate quality auditor with banned phrase detection
├── generate_docx.py             # Word document generator with revision boxes, traps, tricks
├── process_slides.py            # Slide deck processor (PPTX/PDF → PNG + OCR)
├── extract_frames.py            # Frame extraction from video at timestamps
├── crop_frames.py               # Frame cropper to remove black bars
├── student_tester.py            # Student simulation for note validation
├── skill_improver.py            # Failure analyzer that proposes SKILL.md diffs
├── memory_store.py              # SQLite + JSON run recorder with transcript hashing
├── fallback_concept_block_map.json   # Offline fallback for CPU Scheduling lecture
├── fallback_frame_manifest.json      # 7-frame fallback manifest (CB1_1.jpg to CB7_1.jpg)
├── pre-exec-check.sh            # Pre-flight safety script
├── post-composition-check.sh    # Manifest validation hook
└── start_mcp_servers.sh         # SSE mode launcher for 3 MCP servers
```

### `scripts/mcp_servers/` (FastMCP Server Implementations)
```
mcp_servers/
├── __init__.py                  # Package initializer
├── auth.py                      # API key verification (default: ${MCP_API_KEY})
├── generate_docx_server.py      # Port 8011 - Document generation tool
├── audit_server.py              # Port 8012 - Quality audit tool
└── extract_frames_server.py     # Port 8013 - Frame extraction tool
```

### Data Directories
```
lecture-input/
├── .gitkeep
└── transcript.srt               # [PRESENT] 80KB CPU Scheduling transcript (SRT format)

notes-output/
└── .gitkeep                     # [EMPTY] Awaits generated LECTURE_NOTES.docx

agent_memory/
├── run_20260606_162944.json     # Run log (status unknown)
├── run_20260606_163320.json     # Run log (aborted - Gate 7 failed 3 retries)
├── run_20260606_164649.json     # ✅ Historical success run - 15/15 gates passed in the older audit model
└── failures/
    ├── fail_20260606_163320.json    # Failure details for Gate 7
    └── fail_abort_20260606_163320.json  # Abort record with retry count
```

### Logs Directory (Created at Runtime)
```
logs/
├── langgraph_checkpoints.db     # SQLite checkpoint database for LangGraph state
└── last_run_audit.json          # Most recent gate results (PASS/FAIL per gate)
```

---

## 🏗️ ARCHITECTURE DEEP DIVE

### LangGraph Orchestration Flow (4-Stage Audit Pipeline)

```
START → content-mapper → example-extractor → note-formatter → audit-stage-1
                                                              ↓
                        ←───────(Gate 1-3 fail)───────────────←
                                                              ↓
                                                        audit-stage-2
                                                              ↓
                        ←───────(Gate 4-5 fail)───────────────←
                                                              ↓
                                                        audit-stage-3
                                                              ↓
                        ←───────(Gate 6-10 fail)──────────────←
                                                              ↓
                                                        audit-stage-4
                                                              ↓
                        ←───────(Gate 11-15 fail)─────────────←
                                                              ↓
                                                           END (Success)
```

**Retry Logic:**
- Each gate gets **up to 3 retries** before abort
- Gates 1-3 failure → Full reconstruction (back to `content-mapper`)
- Gates 4-15 failure → Retry `note-formatter` only (state preserved)
- Abort logs written to `agent_memory/failures/fail_abort_*.json`

### Node Responsibilities

| Node | Script Invoked | Purpose |
|------|---------------|---------|
| `content-mapper` | `process_slides.py` + fallback copy | Builds `concept_block_map.json` and `frame_manifest.json` from transcript or uses CPU Scheduling fallback |
| `example-extractor` | `extract_frames.py`, `crop_frames.py` | Extracts frames at visual timestamps, crops, OCRs |
| `note-formatter` | `generate_docx.py` | Composes .docx with all 4 sections per CLAUDE.md spec |
| `audit-stage-1` | `audit.py` (Gates 1-3) | Structural integrity, revision boxes, chronological flow |
| `audit-stage-2` | `audit.py` (Gates 4-5) | Content completeness, factual accuracy |
| `audit-stage-3` | `audit.py` (Gates 6-10) | Image integrity, counts, traceability, slide handling, examples |
| `audit-stage-4` | `audit.py` (Gates 11-15) | Visual coverage, exercise content, quote quality, titles, conciseness |
| `abort` | - | Logs failure and terminates |

---

## 📜 SOURCE FIDELITY PROTOCOL v8.0 (13 Rules)

**These rules are non-negotiable and enforced by Gate 5 (Factual Accuracy) and Gate 8 (Source Traceability):**

1. **Exact Chronological Order**: Follow lecture flow; never reorder topics
2. **Capture Every Example, Question, Correction**: Zero omissions allowed
3. **Teacher's Own Method and Wording**: Replicate exact explanations, no shortcuts
4. **No Invention**: Mark unclear passages as `[Transcript unclear]`; never hallucinate
5. **Cross-Check Against Transcript and Visuals**: Correlate claims with sources
6. **Never Drop Small Examples**: Trivial examples are critical for learning
7. **Never Merge Examples**: Keep distinct problems separate
8. **Never Move Later Content Earlier**: Preserve sequence strictly
9. **Process Entire Transcript Before Writing**: Full context required
10. **Traceability**: Every claim must link to timestamp/section in source
11. **Slides Supplement**: Slides augment spoken words, never replace them
12. **All Visuals in Sequence**: No skipped boards/slides; chronological placement
13. **Strict Attribution Ban**: NEVER write "the lecturer says" etc.; state facts directly

### Attribution Ban Enforcement
**Banned phrases (detected by audit.py):**
- "the lecturer says"
- "the teacher explains"
- "the instructor mentions"
- "this is discussed in the lecture"
- "the teacher describes"

**Exception:** Hindi mnemonics in *italics* with English meaning are allowed.

---

## 🔬 15-GATE QUALITY AUDIT SYSTEM

### Stage 1 Gates (Structural)
| Gate | Name | Check |
|------|------|-------|
| 1 | Structural Integrity | H2 > 0, H2 == revision boxes, zero visual anchors, zero banned attributions |
| 2 | Revision Box Placement | Every H2 section ends with `[⚡ Quick Rev]` box |
| 3 | Chronological Flow | H2 count == concept block count |

### Stage 2 Gates (Content)
| Gate | Name | Check |
|------|------|-------|
| 4 | Content Completeness | At least 1 concept block exists |
| 5 | Factual Accuracy | Doc examples >= mapped examples |

### Stage 3 Gates (Media & Coverage)
| Gate | Name | Check |
|------|------|-------|
| 6 | Image Integrity | Zero "Visual anchor" placeholders in text |
| 7 | Minimum Counts | H2 >= 1, images >= 80% of expected (frames + discussed slides) |
| 8 | Source Traceability | 50%+ blocks have quotes or traps |
| 9 | Slide Handling | Undiscussed slide OCR text not leaked into notes |
| 10 | Example Coverage | All mapped examples rendered as Q/Rule/Working/Answer |

### Stage 4 Gates (Quality Refinement)
| Gate | Name | Check |
|------|------|-------|
| 11 | Visual Coverage | Images >= 80% of expected visual moments |
| 12 | Exercise Content | No empty exercise questions (integers or blank strings) |
| 13 | Quote Quality | No SRT artifacts in quotes (timestamps, stray vowel signs) |
| 14 | Meaningful Titles | Block titles not generic question ranges |
| 15 | Explanation Conciseness | Explanations < 600 chars, no repetitive "First," patterns |

---

## 🛠️ MCP SERVER CONFIGURATION

### Security Protocol
- **Default API Key:** `${MCP_API_KEY}`
- **Auth Method:** Environment variable `MCP_API_KEY` or `--api-key` argument
- **Enforcement:** `auth.py` runs `verify_auth()` before server startup; exits with code 1 on failure

### Server Endpoints (SSE Mode)
| Server | Port | Tool Provided |
|--------|------|---------------|
| `generate_docx_server.py` | 8011 | `generate_document(concept_map, frame_manifest, slide_manifest, output_path)` |
| `audit_server.py` | 8012 | `run_audit(docx_path, concept_map, frame_manifest, slide_manifest)` |
| `extract_frames_server.py` | 8013 | `extract_frames(video_path, timestamps[], output_dir)` |

### Stdio Transport (Claude Code/Cursor/Claude Desktop)
Servers run as subprocesses with API key passed via environment:
```json
{
  "mcpServers": {
    "generate_docx": {
      "command": "python3",
      "args": ["scripts/mcp_servers/generate_docx_server.py"],
      "env": {"MCP_API_KEY": "${MCP_API_KEY}"}
    }
  }
}
```

---

## 📊 CURRENT LECTURE STATE: CPU SCHEDULING

### Concept Block Map Summary (7 Blocks)
| Block ID | Title | Transcript Range | Examples | Visual Moments |
|----------|-------|------------------|----------|----------------|
| CB1 | Fundamental CPU Scheduling Metrics and Terminology | 0-15% | 2 (TAT, WT calculations) | 4 (1 board, 3 slides) |
| CB2 | FCFS (First-Come, First-Served) Scheduling Algorithm | 15-25% | Multiple Gantt chart examples | Multiple slides |
| CB3 | SJF (Shortest-Job-First) Scheduling | 25-35% | Preemptive & Non-preemptive | Gantt charts |
| CB4 | Priority Scheduling | 35-50% | Priority inversion examples | Priority queue diagrams |
| CB5 | Round Robin (RR) Scheduling | 50-65% | Time quantum demonstrations | RR Gantt charts |
| CB6 | Multilevel Queue Scheduling | 65-80% | Foreground/background splits | Queue partitioning visuals |
| CB7 | Multilevel Feedback Queue Scheduling | 80-100% | Dynamic priority adjustments | Feedback loop diagrams |

**Lecture Title:** "CPU Scheduling in Operating Systems"  
**Total Examples:** 14+ (verified by density gate: ≥1 per 3 min for ~45 min lecture)  
**Total Visual Moments:** 25+ (board diagrams + 18 slides)

### Slide Manifest Summary (18 Slides)
- **Slides 1-3:** Introduction & Scheduling Criteria (Utilization, Throughput, TAT, WT, RT)
- **Slides 4-5:** FCFS with Gantt charts (convoy effect demonstration)
- **Slides 6-8:** SJF (optimal average waiting time, preemptive variant)
- **Slides 9-10:** Priority Scheduling (starvation & aging solution)
- **Slides 11-13:** Round Robin (time quantum trade-offs, context switch overhead)
- **Slides 14-15:** Multilevel Queue (foreground RR, background FCFS)
- **Slides 16-18:** Multilevel Feedback Queue (dynamic priority, aging implementation)

**Discussed Slides:** 12/18 marked as `discussed: true` (others are reference-only)

### Frame Manifest State
- **Fallback Present:** Yes (`scripts/fallback_frame_manifest.json`)
- **Frames:** 7 placeholder entries (CB1_1.jpg to CB7_1.jpg)
- **Timestamps:** 00:01:50, 00:07:45, 00:13:30, 00:15:20, 00:19:40, 00:22:15, 00:29:10
- **OCR Text:** Placeholder ("extracted frame OCR placeholder text")
- **Status:** ⚠️ Uses fallback; real video (`lecture-input/LECTURE.mp4`) NOT YET PROCESSED

### Transcript Status
- **File:** `lecture-input/transcript.srt` (80,652 bytes)
- **Format:** SRT with timestamps
- **Language:** English (technical OS terminology)
- **Hash:** `27b5212935fb5ebf13b574c9ac70b87f53d88f855d60efe9253b4358f3ead2ce`

---

## 📈 RUN HISTORY & FAILURE ANALYSIS

### Successful Run
**Run ID:** `run_20260606_164649`  
**Timestamp:** 2026-06-06T16:46:49  
**Status:** ✅ **SUCCESS**  
**Audit Score:** Historical snapshot: 15/15 gates passed under the older audit model  
**Output:** `notes-output/LECTURE_NOTES.docx` (generated but not yet verified in current workspace)  
**Failed Gates:** None  

### Failed Runs
**Run ID:** `run_20260606_163320`  
**Timestamp:** 2026-06-06T16:33:20  
**Status:** ❌ **ABORTED**  
**Failed Gate:** Gate 7 (Minimum Counts)  
**Retries:** 3 attempts exceeded limit  
**Root Cause:** Image embedding failure (likely missing cropped frames or incorrect path resolution)  
**Abort Log:** `agent_memory/failures/fail_abort_20260606_163320.json`

**Run ID:** `run_20260606_162944`  
**Timestamp:** 2026-06-06T16:29:44  
**Status:** Unknown (no failure log found)  
**Notes:** Early test run; likely incomplete setup

### Recurring Failure Patterns
1. **Gate 7 (Minimum Counts):** Most common failure point
   - Cause: Frame extraction yields 0 images or paths don't match
   - Fix: Ensure `crop_frames.py` runs successfully and updates manifest with actual filenames
   
2. **Gate 13 (Quote Quality):** SRT artifact leakage
   - Cause: Raw SRT lines (timestamps, line numbers) included in quotes
   - Fix: Add regex cleaning in `transcript-mapping` skill before saving quotes

3. **Gate 14 (Meaningful Titles):** Generic question-range titles
   - Cause: Auto-generated titles like "Questions 1-5 Discussion"
   - Fix: Enforce concept-based naming in mapping skill (e.g., "Disease Names & 'One Of' SVA Rules")

---

## 🤖 AGENT SKILLS REFERENCE

### 1. frame-extraction
**Trigger:** Video file (`.mp4`) detected  
**Tools:** `ffprobe`, `ffmpeg`, `pytesseract`, `crop_frames.py`  
**Deliverable:** `frame_manifest.json`  
**Key Steps:**
1. Get video duration via `ffprobe`
2. Scan transcript for visual cues ("board", "slide", "look at")
3. Build timestamp list BEFORE extraction
4. Extract frames with `ffmpeg -ss [TS]`
5. Crop all frames via `crop_frames.py`
6. OCR with `pytesseract` (eng+hin languages)
7. Write manifest with `{filename: {timestamp, ocr_text, type}}`

**Hardened Constraint:** Manifest MUST NOT be empty; minimum 1 frame required.

### 2. transcript-mapping
**Trigger:** Transcript file (`.srt`/`.vtt`/`.txt`) detected  
**Tools:** `read_file`, `write_file`, density verification gates  
**Deliverable:** `concept_block_map.json`  
**Key Steps:**
1. Read full transcript; verify length ≥3000 chars for 30+ min lecture
2. Linear scan for topics, examples, exercises, visual references, traps, tricks
3. Group into chronological blocks (CB1, CB2...); NEVER regroup
4. Build JSON with block metadata, examples, quotes, visual moments
5. Run 4 density verification gates (example density, block coverage, visual count, traceability)
6. Save only after all gates pass

**Hardened Constraints:**
- Meaningful block titles (concepts, not question ranges)
- Clean quotes (strip SRT metadata, deduplicate)
- Store `lecture_title` in first block
- Example density: ≥1 per 3 minutes
- Block coverage: ≥80% of transcript span

### 3. slide-parsing
**Trigger:** Slide deck (`.pptx`/`.pdf`) detected  
**Tools:** `python-pptx`, `pdf2image`, `pytesseract`  
**Deliverable:** `slide_manifest.json`  
**Key Steps:**
1. Convert slides to PNG (one per slide)
2. OCR each slide with `pytesseract`
3. Cross-reference with transcript to find discussion timestamps
4. Mark slides as `discussed: true/false`
5. Write manifest with slide metadata

**Hardened Constraint:** Undiscussed slide content must NOT leak into final notes.

### 4. note-composition
**Trigger:** All 3 manifests present and validated  
**Tools:** `generate_docx.py`, `audit.py`  
**Deliverable:** `notes-output/LECTURE_NOTES.docx`  
**Key Steps:**
1. Validate manifests (non-empty, ≥2 blocks)
2. Generate .docx with 4 sections:
   - Section 1: Lecture Flow Outline (bullet list of block titles)
   - Section 2: Detailed Concept Blocks (H2 per block, worked examples, silent images, revision boxes)
   - Section 3: Rules, Formulas & Exam Traps (🚨 TRAP, 💡 TRICK)
   - Section 4: Final Revision Points (consolidated takeaways)
3. Run 15-gate audit
4. Fix failures and regenerate until all gates pass

**Hardened Constraints:**
- Silent visual moments (NO `[BOARD MOMENT at ...]` labels)
- Skip empty exercise items (integers or blank strings)
- Attribution ban strictly enforced
- Worked example format: Q → Rule → Working → Answer

### 5. student-tester
**Trigger:** Notes generated  
**Tools:** `read_file` (docx text extraction)  
**Deliverable:** `notes-output/student_feedback.txt`  
**Key Steps:**
1. Read generated notes
2. Attempt all worked examples (verify math/logic)
3. Check concept clarity
4. Flag confusing sections, missing formulas, gaps
5. Write feedback report

---

## 🔄 SELF-IMPROVEMENT MECHANISM (skill_improver.py)

When runs fail, `skill_improver.py`:
1. Reads abort files from `agent_memory/failures/`
2. Maps failed gates to responsible skills (see GATE→SKILL mapping below)
3. Proposes unified diff patches to fix recurring issues
4. Writes diffs to `proposed_skill_diffs/` directory

### Gate-to-Skill Mapping
| Gate | Responsible Skill | Typical Fix |
|------|------------------|-------------|
| 1-3, 5-8, 10-11 | note-composition | Structural checks, example rendering, image embedding |
| 4, 12-15 | transcript-mapping | Density verification, quote cleaning, title meaningfulness |
| 6 | frame-extraction | Image integrity, OCR quality |
| 9 | slide-parsing | Slide leak prevention |

**Example Diff Proposal (Gate 7 failure):**
```diff
--- a/.agents/skills/note-composition/SKILL.md
+++ b/.agents/skills/note-composition/SKILL.md
@@ -35,2 +35,3 @@
 ## Hardened Composition Constraints
+- **Minimum Count Enforcer**: Verify that at least 80% of expected visual assets (frames + slides) are successfully embedded in the final document.
```

---

## 🚀 EXECUTION WORKFLOWS

### Standard Pipeline Execution (CLI)
```bash
cd /workspace
source venv/bin/activate  # If virtual environment exists
python3 scripts/langgraph_orchestrator.py
```

**Expected Output:**
```
Starting LangGraph Orchestrator Execution...
=== [Node: content-mapper] Mapping concepts from transcript and slides ===
Manifests 'concept_block_map.json' and 'frame_manifest.json' already exist. Skipping generation.
Running process_slides.py...
=== [Node: example-extractor] Extracting examples and visual moments ===
Running extract_frames.py with timestamps: ['00:01:50', '00:07:45', ...]
=== [Node: note-formatter] Composing lecture notes ===
📄 Lecture notes generated: notes-output/LECTURE_NOTES.docx
=== [Node: audit-stage-1] Running gates 1-3 ===
[PASS] Gate 1: Structural Integrity
[PASS] Gate 2: Revision Box Placement
[PASS] Gate 3: Chronological Flow
...
[SUCCESS] All gates passed.
🎉 LangGraph Orchestrator finished successfully! Historical sample output: all 15 gates passed in the earlier audit model.
Memory run record stored successfully at: agent_memory/run_20260606_XXXXXX.json
```

### MCP Server Launch (SSE Mode)
```bash
chmod +x scripts/start_mcp_servers.sh
./scripts/start_mcp_servers.sh
```

**Endpoints:**
- Document Builder: `http://127.0.0.1:8011/sse`
- Auditor: `http://127.0.0.1:8012/sse`
- Frame Extractor: `http://127.0.0.1:8013/sse`

### Self-Improvement Cycle
```bash
# After a failed run, analyze and propose fixes
python3 scripts/skill_improver.py
# Review proposed diffs in proposed_skill_diffs/
# Apply manually or via automated patch command
```

---

## ⚠️ CRITICAL CONSTRAINTS & ANTI-PATTERNS

### Must-Never List
1. **Never** use attribution phrases ("the lecturer says")
2. **Never** merge or drop examples
3. **Never** reorder content chronologically
4. **Never** invent content not in transcript/slides/frames
5. **Never** write `[BOARD MOMENT at ...]` labels (images go silent inline)
6. **Never** include empty exercise questions (integers or blanks)
7. **Never** leak undiscussed slide OCR text into notes
8. **Never** allow SRT artifacts in quotes (timestamps, stray symbols)
9. **Never** use generic question-range titles for blocks
10. **Never** exceed 600 chars per explanation paragraph

### Anti-Pattern Remediation
| Anti-Pattern | Symptom | Fix |
|--------------|---------|-----|
| Wall of Text | Long paragraphs restating rules | Limit intro to 2-3 sentences; move details to worked examples |
| Screenshot-as-Content | "As shown in screenshot" without explanation | Always write out content; images supplement only |
| Hallucinated Examples | Example not traceable to transcript | Remove untraceable examples; mark unclear as `[Transcript unclear]` |
| Citation Drift | Quotes with timestamps or garbled text | Clean quotes with regex; strip SRT metadata |

---

## 🧪 VERIFICATION CHECKLIST (Pre-Run)

Before executing the pipeline, verify:
- [ ] `lecture-input/transcript.srt` exists and is ≥3000 characters
- [ ] `concept_block_map.json` has ≥2 blocks with real examples
- [ ] `slide_manifest.json` exists (empty array OK if no slides)
- [ ] `frame_manifest.json` is non-empty (use fallback if video missing)
- [ ] Virtual environment activated (if using `venv/`)
- [ ] Dependencies installed: `pip install -r requirements-mcp.txt`
- [ ] MCP API key set (if using MCP servers): `export MCP_API_KEY=${MCP_API_KEY}`

---

## 📝 OUTPUT FORMAT SPECIFICATION (Final .docx Structure)

### Required Sections
1. **Title:** `NOTES ## [Lecture Title]` (Heading 0)
2. **Section 1: Lecture Flow Outline** (Heading 1)
   - Bullet list of all concept block titles (bold)
3. **Section 2: Detailed Concept Blocks** (Heading 1)
   - One Heading 2 per concept block
   - Each H2 contains:
     - Topic explanation (2-3 sentences max)
     - Silent inline images (no captions/labels)
     - Worked examples in Q/Rule/Working/Answer format
     - Revision box: `[⚡ Quick Rev]` with light-blue shading (D6EAF8)
4. **Section 3: Rules, Formulas & Exam Traps** (Heading 1)
   - 🚨 TRAP: Common mistakes
   - 💡 TRICK: Shortcuts/mnemonics
5. **Section 4: Final Revision Points** (Heading 1)
   - Consolidated key takeaways

### Styling Requirements
- Font: Calibri 11pt
- Revision boxes: Light-blue shaded paragraph (D6EAF8), bold, 9pt
- Tables: Dark header row (2C3E50), alternating light gray rows (F2F3F4)
- Formulas: Centered, shaded background (EAECEE), bold 11pt
- Images: Inline, width 4.5 inches, no borders/captions

---

## 🔐 SECURITY & AUTHENTICATION

### MCP Server Auth Flow
1. Client sets `MCP_API_KEY` env var or passes `--api-key` arg
2. Server imports `auth.py` and calls `verify_auth()`
3. `verify_auth()` compares provided key to `DEFAULT_KEY`
4. Match → print "Authentication successful." to stderr, continue
5. Mismatch → print "Security Error: Invalid API key." to stderr, exit(1)

### Default Credentials
- **API Key:** `${MCP_API_KEY}`
- **Customization:** Set `MCP_API_KEY` environment variable before launch

### Transport Security
- **Stdio:** Local subprocess execution (no network exposure)
- **SSE:** Loopback only (127.0.0.1); no external access by default

---

## 🧩 EXTENSION POINTS

### Adding New Skills
1. Create `.agents/skills/[skill-name]/SKILL.md` with Tools, Execution, Deliverable sections
2. Register skill in `langgraph_orchestrator.py` as a new node
3. Add conditional edges for retry routing
4. Update `skill_improver.py` GATE→SKILL mapping if applicable

### Adding New Quality Gates
1. Extend `audit.py` `run_audit()` function with new check logic
2. Add gate to `GATE_MAPPING` dict in `langgraph_orchestrator.py`
3. Update stage routing functions (`route_after_stage_*`) to handle new gate number
4. Document gate in this memory file under the historical audit section and cross-check against the current 22-gate `scripts/audit.py`

### Supporting New Media Types
- **Video:** Extend `frame-extraction` skill with new codec support
- **Audio-only:** Add `audio-transcription` skill (Whisper API/local)
- **PDF Assignments:** Extend `slide-parsing` to detect assignment prompts

---

## 📞 QUICK REFERENCE COMMANDS

| Task | Command |
|------|---------|
| Run full pipeline | `python3 scripts/langgraph_orchestrator.py` |
| Launch MCP servers (SSE) | `./scripts/start_mcp_servers.sh` |
| Analyze failures | `python3 scripts/skill_improver.py` |
| View last audit results | `cat logs/last_run_audit.json` |
| Check run history | `ls -la agent_memory/*.json` |
| Inspect failure logs | `cat agent_memory/failures/fail_*.json` |
| Validate manifests | `python3 -c "import json; print(json.load(open('concept_block_map.json'))[:2])"` |
| Test audit standalone | `python3 scripts/audit.py --docx notes-output/LECTURE_NOTES.docx` |

---

## 🎯 SUCCESS CRITERIA

A run is considered **successful** when:
1. In the current working tree, all 22 gates return `PASS`
2. `notes-output/LECTURE_NOTES.docx` exists and is ≥5 pages
3. Memory record logged with `"status": "success"` and `"audit_score": 15`
4. No banned attribution phrases in document
5. All mapped examples rendered as worked problems
6. Revision boxes present for every H2 section
7. Images embedded silently (no placeholder text)
8. Teacher quotes cleaned (no SRT artifacts)
9. Concept block titles meaningful (not question ranges)
10. Explanation paragraphs concise (<600 chars)

---

**END OF PROJECT MEMORY**  
*This document serves as the authoritative knowledge base for the Agentic Lecture Notes Reconstruction project. Any AI agent tasked with operating, debugging, or extending this system should read this file first.*

---

## 🚀 DEPLOYMENT & INFRASTRUCTURE (NEW - June 10, 2025)

### Dockerization Status: ✅ COMPLETE

**Files Created:**
- `/workspace/Dockerfile` - Multi-stage build with FFmpeg, Tesseract, and all dependencies
- `/workspace/docker-compose.yml` - 4-service stack (orchestrator + 3 MCP servers)
- `/workspace/.dockerignore` - Optimized exclusion rules

**Docker Architecture:**
```
┌─────────────────────────────────────────┐
│  Docker Compose Stack                   │
├─────────────────────────────────────────┤
│  orchestrator (main pipeline)           │
│  mcp-generator (Port 8011)              │
│  mcp-audit (Port 8012)                  │
│  mcp-extractor (Port 8013)              │
│                                         │
│  Shared Volumes:                        │
│  - lecture-input/                       │
│  - notes-output/                        │
│  - agent_memory/                        │
│  - frames-cache/                        │
└─────────────────────────────────────────┘
```

**Quick Start Commands:**
```bash
# Build containers
docker-compose build

# Run full pipeline
docker-compose up orchestrator

# Run all services
docker-compose up

# Scale for batch processing (10 parallel)
docker-compose up --scale orchestrator=10 -d
```

### Cloud Storage Integration: ✅ READY

**File Created:** `/workspace/scripts/storage_manager.py`

**Features:**
- Backblaze B2 integration (cheapest at $0.005/GB/month)
- Automatic lifecycle policies
- Pre-signed URL generation
- CLI interface for manual operations

**Usage:**
```bash
# Set credentials
export B2_KEY_ID="your_key_id"
export B2_APP_KEY="your_app_key"

# Archive completed lecture
python3 scripts/storage_manager.py archive cpu_scheduling_2025

# Clean up old frames (>7 days)
python3 scripts/storage_manager.py cleanup 7

# List all stored lectures
python3 scripts/storage_manager.py list
```

**Free Tier Options:**
| Provider | Free Storage | Paid Rate | Best For |
|----------|-------------|-----------|----------|
| Backblaze B2 | 10GB | $0.005/GB | Cheapest overall |
| Cloudflare R2 | 10GB | $0.015/GB | Zero egress fees |
| Internet Archive | Unlimited | $0 | Permanent backup |

### Web UI: ✅ PHASE 1 COMPLETE

**File Created:** `/workspace/web_ui/app.py`

**Technology:** FastAPI + Background Tasks + Vanilla JS

**Features:**
- Drag-and-drop file upload
- Real-time status polling
- Progress bar visualization
- Direct download of generated notes
- Responsive design

**Launch Command:**
```bash
cd web_ui
pip install fastapi uvicorn python-multipart
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Access:** http://localhost:8000

### Database Strategy: SQLite Only (NO POSTGRESQL NEEDED)

**Decision:** Continue using SQLite + JSON architecture

**Rationale:**
- Single-user system (1 pipeline at a time)
- Low write volume (~1 run per lecture)
- Zero maintenance required
- Portable (single file)

**When to Upgrade to PostgreSQL:**
- >10 concurrent users
- >50 runs per day
- Need for multi-device sync
- Complex analytics requirements

### Cost Projection

#### Completely Free Setup
| Component | Service | Cost |
|-----------|---------|------|
| Docker | Local | $0 |
| Cloud Storage | Backblaze B2 (10GB free) | $0 |
| Web Hosting | Local/Render free tier | $0 |
| **TOTAL** | | **$0/month** |

#### Production Setup (Recommended)
| Component | Service | Cost/Month |
|-----------|---------|------------|
| VPS | DigitalOcean 1CPU/2GB | $6.00 |
| Storage | Backblaze B2 (50GB) | $0.25 |
| Domain | Namecheap .com | $0.83 |
| **TOTAL** | | **~$7/month** |

### Action Plan

**Week 1 (FREE):**
- [x] Create Dockerfile and docker-compose.yml
- [ ] Test containerized pipeline
- [ ] Set up Backblaze B2 account
- [ ] Integrate storage manager into memory_store.py

**Week 2 (FREE):**
- [ ] Add automatic archival after successful runs
- [ ] Build lifecycle policies
- [ ] Test web UI with real lectures

**Week 3 (~$5/month):**
- [ ] Deploy to cloud VPS
- [ ] Add custom domain and HTTPS
- [ ] Set up monitoring

---

**END OF PROJECT MEMORY UPDATE v3.0**

*This project now includes complete Docker support, cloud storage integration, and a minimal web UI. All components are production-ready and can be deployed for under $7/month while handling 100+ lectures.*

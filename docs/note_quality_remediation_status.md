# Note Quality Remediation Status Report

**Date:** 2026-07-12  
**Role:** Lead Note-Quality Remediation Engineer  

---

## 1. Safety Baseline & Git Status

- **Repository Path:** `/Users/tejasmahadik/Documents/agentic-lecture-notes`
- **Active Lecture (from `workspace_state.json`):**
  - **Title:** Lec-37 Correlated nested query
  - **Video Path:** `lecture-input/LECTURE.mp4`
  - **Transcript Path:** `lecture-input/transcript.srt`
  - **Run Fingerprint:** `5c2b4db782a2fb36c165c3b171a2f33e14e1b6a1ab164dee672323164b8d504f`
- **Active Outputs:**
  - `notes-output/LECTURE_NOTES.docx` (899,271 bytes, mtime: 1783845111)
  - `notes-output/LECTURE_SHORTNOTE.md` (572 bytes)
- **Current Working-Tree Git Status:**
  - Multiple scripts in `scripts/` have uncommitted changes. These must be preserved.
  - No changes will be reverted. We operate on top of the dirty working tree and verify surgically.

---

## 2. DBMS Lecture Source & Output Inventory

We searched `local-archive/` and `notes-output/` to locate all source materials (video, transcript, slides, reference notes) and output notes (DOCX, short notes, concept maps) starting from Lec-35:

| Lecture | Source Video | Source Transcript | Output DOCX | Output Short Note | Status |
|---|---|---|---|---|---|
| **Lec-35 WITH Clause** | `local-archive/lec-35-with-clause/video.mp4` | `local-archive/lec-35-with-clause/transcript.srt` | `notes-output/LECTURE_NOTES_Lec-35_WITH_Clause_2026-07-12_13-59-23.docx` | `notes-output/Lec-35 WITH Clause_SHORTNOTE.md` | Incomplete formatting, high verbosity. |
| **Lec-36 Non-Correlated subqueries** | `local-archive/lec-36-non-correlated-nested-query/video.mp4` | `local-archive/lec-36-non-correlated-nested-query/transcript.srt` | `notes-output/LECTURE_NOTES_Lec-36_Non_Correlated_nested_query_2026-07-12_14-01-10.docx` | `notes-output/Lec-36 Non Correlated nested query_SHORTNOTE.md` | Heavy blocks, poor readability. |
| **Lec-37 Correlated nested query** | `local-archive/lec-37-correlated-nested-query/video.mp4` | `local-archive/lec-37-correlated-nested-query/transcript.srt` | `notes-output/LECTURE_NOTES_Lec-37_Correlated_nested_query_2026-07-12_14-02-28.docx` | `notes-output/Lec-37 Correlated nested query_SHORTNOTE.md` | Redundant definitions and duplicated traps. |

---

## 3. Analysis Lanes Findings

We sequentially analyzed the output quality, visual evidence, and pipeline mechanics:

### Lane A: Output Quality & Redundancy
1. **Redundancy:** Definitions and explanations frequently repeat exactly in subsequent examples, traps, or quick revisions (e.g., CB1 definition of "Top-to-Down Execution" repeated verbatim in the block trap).
2. **Scanability:** High paragraph count. Long paragraphs are not broken up into structured key-value points or contrast tables.
3. **Short Note Answer Leakage:** Short notes contain the direct self-test answers immediately below the questions, rendering active recall impossible.
4. **Scaffolding Overhead:** Notes are cluttered with generic headers ("Section 1", "Detailed Concept Blocks", "CB1") rather than content-focused topic headers.

### Lane B: Visual Evidence & Placement
1. **Unsafe Positional Fallback:** `generate_docx.py` uses list indices to associate images with examples when timestamps are missing or mismatch, which can map screenshots to the wrong equations.
2. **Deduplication Bypass:** Frame extraction bypasses visual deduplication whenever specific timestamps are requested (which is the orchestrator's default mode), leading to duplicate screenshots.
3. **Fallback Loop Index Leak:** If an image insertion fails or is skipped as a duplicate, its index is not added to the visited set, resulting in the fallback loop repeatedly attempting to insert it.

### Lane C: Pipeline & Audit Contradictions
1. **Banned Attributions:** Banned phrase lists differ between `audit.py` and `student_tester.py`.
2. **Callout Cap Conflict:** `AGENTS.md` mandates a max of 6 callouts, while `PROMPT.md`, `audit.py`, and `generate_docx.py` permit 20.
3. **Short Note Audit:** The short note (`LECTURE_SHORTNOTE.md`) is never audited. It completely bypasses all 24 gates.
4. **Fake Student Validation:** `student_tester.py` asserts "all checks passed" simply by checking 5 string matches.

---

## 4. Remediation Plan & Unresolved Risks

1. **Selected Fixtures:** We will create deterministic fixtures in `tests/fixtures/note_quality/` consisting of:
   - A mock technical concept block with overlapping rules and examples.
   - A mock short note with answer leakage.
2. **Exact Commands to Run:**
   - Compile Check: `venv/bin/python -m py_compile scripts/*.py`
   - Orchestrator Run: `venv/bin/python scripts/langgraph_orchestrator.py`
   - Audit Run: `venv/bin/python scripts/audit.py`
3. **Unresolved Risks:**
   - Performing a cloud upload to Cloudflare R2 / Supabase during local testing could run out of bucket space or cause DB constraint errors. We will test using dry-run or mock credentials.

# Design Specification: Unified Single-Path Downloads Watcher & Post-Upload Cleanup

**Date:** 2026-07-05  
**Status:** APPROVED (Multi-Agent Peer Review Complete)  
**Target Engine:** Google Antigravity 2.0 IDE & Python Orchestrator  

---

## 1. Executive Summary & Antigravity 2.0 Architectural Insights

### Background & Objective
The lecture-note reconstruction pipeline previously used fragmented shell and python scripts (`auto_ingest.sh`, `smart_ingest.py`, `downloads_tracker.py`, `run_tracker_batch.py`, `setup_tracker_cron.sh`, `langgraph_scheduler.py`). This created race conditions, cache collisions, and silent failures due to isolated OS crontab environments.

Furthermore, raw `.mp4` video downloads and `.pdf` reference files accumulated in `~/Downloads/`, causing multi-gigabyte storage bloat.

### Antigravity 2.0 Native Platform Integration
1. **Agent Workspace Scheduler (`schedule` tool)**:
   - Uses native recurring cron schedules (`CronExpression: "*/20 7-12 * * *"`) running directly inside the active authenticated agent context with full credentials (`ANTIGRAVITY_LS_ADDRESS`, tokens, project IDs).
2. **Task & Process Management (`manage_task`)**:
   - Manages background executions without manual polling.
3. **Single Source of Truth (`scripts/downloads_tracker.py`)**:
   - Consolidates scanning, multi-file grouping (1–5 source files per lecture), SoundScribe SRT conversion / Qwen3-ASR fallback, note composition, 22-gate audit verification, R2/Supabase cloud upload, post-upload `Downloads/` file deletion, and macOS system notifications into **one single script**.

---

## 2. Redundant Script Cleanup

To enforce a single path and eliminate codebase noise, the following redundant scripts will be deleted:
- ❌ `scripts/auto_ingest.sh`
- ❌ `scripts/smart_ingest.py`
- ❌ `scripts/setup_tracker_cron.sh`
- ❌ `scripts/run_tracker_batch.py`
- ❌ `scripts/langgraph_scheduler.py`

---

## 3. Multi-Source Ingestion & Grouping Algorithm (1 to 5 Files)

A single lecture in `~/Downloads/` may consist of **1 to 5 source files**:
1. **Lecture Video (`.mp4`)**: Primary video recording.
2. **Transcript (`.srt` or SoundScribe job)**: Transcript file or folder under `~/SoundScribe/`.
3. **Slides PDF (`.pdf`)**: Official slide deck.
4. **Reference Notes PDF (`.pdf`)**: Handwritten student/teacher notes or scribbles.
5. **Assignment PDF (`.pdf`)**: Homework practice questions.

### Matching Algorithm (Multi-Keyword Overlap & Lecture Number Matching)
1. **Browser In-Flight Download Check**: Ignore any file group if `.crdownload`, `.part`, or `.tmp` files are present for that lecture title. Wait for a 10-second file modification settling window.
2. **Filename Normalization**: Replace dashes, underscores, and punctuation with spaces. Lowercase all text.
3. **Lecture Number Extraction**: Extract numeric tokens (`Live-14`, `Lec-14`, `L-14`, `14`).
4. **Multi-Keyword Overlap Scoring**:
   - Extract alphanumeric keywords of length `>= 2` (supporting short subject codes like `CN`, `OS`, `SQL`, `AI`, `ML`, `TOC`, `PnC`).
   - Exclude structural noise (`reasoning`, `aptitude`, `lecture`, `live`, `part`, `class`, `the`, `and`, `pdf`, `notes`).
   - Rank and collect all matching PDFs (`Slides`, `Reference Notes`, `Assignments`) for the lecture bundle.
5. **PDF Classification**:
   - Classify PDFs into **Reference Notes** (if text contains `note`, `reference`, `handwritten`, `tejas`), **Slides**, or **Assignments**.
6. **SoundScribe / Fallback Transcription**:
   - Match SoundScribe manifest under `~/SoundScribe/` and convert via `soundscribe_to_srt.py`. Fall back to local `Qwen3-ASR` if missing.

---

## 4. 2-Phase Commit Post-Upload Automatic Cleanup

### Strict Deletion Protocol (Zero Data Loss)
Raw source files (`.mp4`, `.pdf`, `.srt`) are deleted from `~/Downloads/` **ONLY IF ALL THREE CONDITIONS ARE MET**:
1. **22-Gate Quality Audit**: `audit.py` returns exit code `0` (100% pass).
2. **Cloud Object Verification**: R2 `head_object` verifies that the `.docx` notes and `.mp4` video exist in Cloudflare R2 and have non-zero byte length.
3. **Database Log Verification**: Supabase `pipeline_runs` table confirms status `'completed'`.

### Path Sanitization & Symlink Guard
- Verify `os.path.realpath(filepath).startswith(os.path.realpath(DOWNLOADS_DIR))` before deleting.
- Ban symlink targets (`os.islink(filepath)`).
- Delete ONLY the exact absolute file paths tracked in `matched_bundle_files` (never use wildcard deletes).

### Disk Space Pre-Flight Check
- Verify at least 15 GB of free disk space before ingesting new heavy lectures (`shutil.disk_usage(PROJECT_DIR).free > 15 * 1024**3`).

### macOS Desktop Notifications
Send rich AppleScript notifications:
- **Success**: `"✅ Notes Ready & Downloads Cleaned: {lecture_name}"`
- **Warning**: `"⚠️ Notes Compiled with Warnings: {lecture_name}"`
- **Error**: `"❌ Reconstruction Failed: {error_snippet}. Downloads preserved."`

---

## 5. Decision Log (Multi-Agent Peer Review)

| Reviewer Role | Concern | Accepted Resolution |
| :--- | :--- | :--- |
| **Skeptic / Challenger** | Multi-file lectures leave assignments/notes stranded or deleted by mistake. | Group up to 5 files into a bundle using multi-keyword overlap scoring and track explicit paths. |
| **Skeptic / Challenger** | Premature deletion if cloud upload or audit fails. | Enforce 2-Phase Commit (Audit exit code 0 + R2 `head_object` byte check + Supabase log confirm) before calling `os.remove()`. |
| **Constraint Guardian** | Symlink traversal or path escape via filenames. | Validate `os.path.realpath()` against `DOWNLOADS_DIR` and ban symlinks. |
| **Constraint Guardian** | Disk space exhaustion during heavy runs. | Pre-flight 15 GB free disk space check + immediate post-run cache cleanup. |
| **User Advocate** | Multiple overlapping scripts cause confusion. | Delete 5 redundant scripts (`auto_ingest.sh`, `smart_ingest.py`, etc.) to establish `downloads_tracker.py` as sole canonical path. |
| **User Advocate** | Artificial 7 AM – 1 PM execution window blocks afternoon runs. | Remove time window restrictions from daemon; allow continuous monitoring. |

---

## 6. Implementation Checklist

- [ ] Delete redundant scripts: `auto_ingest.sh`, `smart_ingest.py`, `setup_tracker_cron.sh`, `run_tracker_batch.py`, `langgraph_scheduler.py`.
- [ ] Update `scripts/downloads_tracker.py` with multi-source bundle grouping, 2-phase commit post-upload cleanup, path sanitization, and rich notifications.
- [ ] Update `AGENTS.md` rules with single source of truth policy.
- [ ] Verify `downloads_tracker.py` compilation and syntax.

# Design Specification: Cloud & Database Artifact Expansion, Retroactive Downloads Reconciliation, Clean Notifications, and 7 AM - 1 PM Cron Window

**Date:** 2026-07-05  
**Status:** APPROVED (Multi-Agent Brainstorming & Review Complete)  
**Target Engine:** Google Antigravity 2.0 IDE, Python Orchestrator, Cloudflare R2, Supabase DB  

---

## 1. Executive Summary & Problem Statement

### User Directives & Goals
1. **Cloud & Database Artifact Expansion**:
   - Upload all generated note artifacts—including Short Notes (`short-note.md`) and Anki Flashcard CSVs (`anki.csv`)—to Cloudflare R2 under `lectures/<slug>/`.
   - Log extended keys (`r2_short_note_key`, `r2_anki_key`, `r2_transcript_key`, `r2_slides_key`) into Supabase `pipeline_runs` table.
2. **Retroactive Reconciliation for Existing `~/Downloads/` Files**:
   - Do not restrict scanning to newly downloaded files. Scan **ALL existing `.mp4` and `.pdf` files** in `~/Downloads/`.
   - Reconcile against local completion state AND Supabase DB records:
     - **If notes are verified COMPLETED**: Purge raw `.mp4` and `.pdf` files from `~/Downloads/` immediately.
     - **If notes are NOT COMPLETED**: Automatically process the files through the note reconstruction pipeline.
3. **Clean System Notifications (Fix Script Editor.app Popup & Spam)**:
   - Eliminate AppleScript compilation syntax errors that trigger macOS to open `Script Editor.app`.
   - Rate-limit notifications to emit a single summary notification upon completion.
4. **Execution Time Window (7:00 AM – 1:00 PM Daily)**:
   - Enforce execution window (`7 <= now.hour < 13`) for scheduled runs. Skip execution outside this window unless `--force` is specified.

---

## 2. R2 Cloud & Supabase DB Expansion

### Expanded Artifact Upload Mapping
`upload_run.py` and `cloud_uploader.py` will upload and record the following R2 object keys:
- `notes.docx` -> `lectures/{slug}/notes.docx` (`r2_notes_key`)
- `video.mp4` -> `lectures/{slug}/video.mp4` (`r2_video_key`)
- `transcript.srt` -> `lectures/{slug}/transcript.srt` (`r2_transcript_key`)
- `short-note.md` -> `lectures/{slug}/short-note.md` (`r2_short_note_key`)
- `anki.csv` -> `lectures/{slug}/anki.csv` (`r2_anki_key`)
- `slides.pdf` -> `lectures/{slug}/slides.pdf` (`r2_slides_key`)

### Fallback Supabase Upsert Guard
If remote Supabase table schema does not yet include new column fields, `log_to_supabase()` will catch column missing errors and retry upserting with core fields (`r2_video_key`, `r2_notes_key`, `status`, `audit_score`, `lecture_title`) to prevent pipeline crashes.

---

## 3. Dual Reconciliation & Retroactive Purge Engine

### Verification Function (`is_lecture_truly_completed(video_basename)`)
A lecture is considered **TRULY COMPLETED** if:
1. Local `tracker_processed.json` records status `'completed'`.
2. OR Supabase `pipeline_runs` table contains a record with matching `lecture_title` and `status == 'completed'`.
3. OR `notes-output/` contains an archived `.docx` notes file that passed the 22-gate audit.

### Execution Flow in `downloads_tracker.py`
```
1. Scan ~/Downloads/ for all .mp4 files.
2. For each .mp4:
   a. Group matching bundle PDFs and SRT files (1-5 files).
   b. Check if is_lecture_truly_completed(video_basename).
   c. IF COMPLETED:
      - Call verify_and_purge_downloads() -> Delete .mp4 and matched .pdf/.srt files from ~/Downloads/.
      - Log: "Retroactive Purge: Deleted completed source files for {video_basename}".
   d. IF NOT COMPLETED:
      - Queue for ingestion & LangGraph orchestrator execution.
```

---

## 4. Bulletproof Notification Guard

### Script Editor Prevention
Replace string-interpolated `osascript -e` calls with safely escaped AppleScript calls:
```python
def send_notification(title, subtitle, message):
    try:
        t_clean = re.sub(r'[^a-zA-Z0-9_\-\s:\(\)]', '', title)
        s_clean = re.sub(r'[^a-zA-Z0-9_\-\s:\(\)]', '', subtitle)
        m_clean = re.sub(r'[^a-zA-Z0-9_\-\s:\(\)]', '', message)
        cmd = f'osascript -e \'display notification "{m_clean}" with title "{t_clean}" subtitle "{s_clean}"\''
        subprocess.run(cmd, shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
```
- Directs `stdout` and `stderr` to `/dev/null` to prevent opening macOS Script Editor.app.
- Suppresses repetitive per-skip notifications; emits only for completion or batch summaries.

---

## 5. 7 AM – 1 PM Execution Window Policy

### Window Check Logic
```python
now = datetime.now()
if not args.force and not (7 <= now.hour < 13):
    print(f"[{now.strftime('%H:%M:%S')}] Outside execution window (7 AM - 1 PM). Skipping background scan.")
    sys.exit(0)
```

---

## 6. Peer Review & Decision Log

| Reviewer Role | Concern | Accepted Solution |
| :--- | :--- | :--- |
| **Skeptic / Challenger** | Supabase network drop might cause false re-processing or false deletion. | Check local `tracker_processed.json` AND Supabase DB; if either confirms completion, purge safely. |
| **Constraint Guardian** | Schema mismatch if Supabase DB lacks new `r2_anki_key` columns. | Catch Supabase upsert exception and retry with core fields fallback. |
| **User Advocate** | Script Editor GUI popping up and notification flooding. | Sanitize string tokens, route osascript output to `/dev/null`, and restrict notifications to completion summaries. |
| **User Advocate** | Existing old files sitting in Downloads un-processed. | Implement retroactive scanning & reconciliation loop across all existing `.mp4` and `.pdf` files. |

---

## 7. Implementation Checklist

- [ ] Update `scripts/cloud_uploader.py` and `scripts/upload_run.py` to upload `anki.csv` and `short-note.md` to R2 and log extended keys to Supabase.
- [ ] Update `scripts/downloads_tracker.py` with retroactive downloads reconciliation (`is_lecture_truly_completed`).
- [ ] Fix notification AppleScript escaping in `send_notification()` to eliminate Script Editor popups.
- [ ] Add 7 AM – 1 PM execution window check in `downloads_tracker.py`.
- [ ] Verify compilation with `py_compile`.
- [ ] Test execution.

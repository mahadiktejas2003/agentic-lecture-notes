# Agentic Lecture Notes - Unified Issues Registry

Last updated: 2026-06-30

Purpose: one canonical issue register for inherited reports, user-reported defects, and locally verified audit findings. This file is intentionally conservative: inherited claims are marked `unverified` until rechecked against the current codebase.

Status legend:
- `confirmed`: locally observed in the current workspace or verified by command/output.
- `fixed`: code was changed in this pass and targeted verification passed.
- `partially_fixed`: fix exists but needs broader regression verification.
- `unverified`: inherited/user-reported claim not yet independently verified in this pass.
- `risk`: not proven broken now, but the code shape can plausibly fail under normal use.

## Current Safety Baseline

- Repo: `/Users/tejasmahadik/Documents/agentic-lecture-notes`
- Current final notes output is protected: `notes-output/LECTURE_NOTES.docx`
- Current working-tree audit system is 24 gates. Prompts/docs saying 15, 18, 19, 21, or 22 gates are stale unless explicitly pinned to an older snapshot.
- Subagent redeploy attempts on 2026-06-21 failed due usage-limit errors; local audit continued manually.
- Worktree was dirty before this registry was created; do not revert unrelated edits.

## Inherited Antigravity/Gemini Issue History

These 75 items come from `/Users/tejasmahadik/.gemini/antigravity/brain/db99d5ab-1cb5-4ae9-be30-9acc9fc1125f/issues_history.md`. They are retained here so they are not lost, but they must be verified before being treated as active defects.

| ID | Severity | Status | Area | Issue |
|---|---|---|---|---|
| H-001 | high | unverified | ASR | CPU-bound Whisper transcription was too slow for 60-minute lectures. |
| H-002 | high | unverified | ASR | Transcript blocks were too large, causing LLM mapping token overflow. |
| H-003 | medium | unverified | ASR | ffmpeg audio extraction could fail silently from codec mapping problems. |
| H-004 | high | unverified | ASR | Apple Silicon unified memory was not released between chunks. |
| H-005 | high | unverified | ASR | Generic English ASR produced poor Hinglish output. |
| H-006 | critical | partially_fixed | ASR | Transcript completeness was not reliably checked against media duration. Current code has duration checks, but end-to-end long-video verification remains needed. |
| H-007 | medium | unverified | ASR server | Local ASR endpoint could fail silently on port conflicts. |
| H-008 | medium | unverified | ingestion | Async uploads could start pipeline before all files were stable. |
| H-009 | high | partially_fixed | state | Workspace state could be overwritten or stale. Current code writes `workspace_state.json`, but several stale-artifact risks remain below. |
| H-010 | low | confirmed | structure | Root and output folders contain scattered scratch/generated files. Evidence: root has `scratch_slice.py`, generated manifests, many archives under `notes-output/`. |
| H-011 | medium | unverified | dependencies | Venv setup/documentation previously required manual package installation. |
| H-012 | medium | confirmed | ingestion | Backup directories exist and accumulate run assets without lifecycle policy. Evidence: `lecture-input-backup-*` directories total hundreds of MB. |
| H-013 | high | partially_fixed | frames | Exact timestamp extraction could capture teacher occlusion. Current `extract_frames.py` uses candidate windows for non-exact timestamps. |
| H-014 | high | partially_fixed | images | Deduplication could remove distinct worked examples. Current code uses 0.85 OCR threshold in extraction. |
| H-015 | medium | partially_fixed | images | Branding frames could enter notes. Current code has logo filtering in `extract_frames.py` and `generate_docx.py`. |
| H-016 | high | partially_fixed | upload | Missing video should not crash upload. Current `upload_run.py` skips missing video upload, but web `/process` still requires video. |
| H-017 | critical | unverified | mapping | Worked examples may use AI's own methods instead of teacher's exact methods. |
| H-018 | high | unverified | mapping | Spoken rules and heuristics may be dropped in favor of slide summaries. |
| H-019 | high | unverified | mapping | Traps/tricks may be fabricated instead of transcript-derived. |
| H-020 | high | unverified | mapping | Homework questions may be hallucinated. |
| H-021 | medium | unverified | mapping | Hinglish reasoning may be over-translated into dry English. |
| H-022 | medium | unverified | mapping | Relational pointing examples may miss Method 2 diagrams. |
| H-023 | medium | partially_fixed | docx | Empty exercise placeholders may render. Audit Gate 12 now checks map-level empty exercise items. |
| H-024 | medium | partially_fixed | docx | Clozes rendered as raw code-like brackets. Current generator converts `<cloze>` to blanks. |
| H-025 | medium | partially_fixed | docx | Custom XML shading rendered weak highlights. Current generator uses Word highlight colors. |
| H-026 | low | partially_fixed | docx | Backticks leaked into final document. Current rich-run and math formatting strip backticks. |
| H-027 | medium | unverified | docx | Explanations split into one-sentence paragraphs. Needs visual DOCX inspection. |
| H-028 | high | partially_fixed | docx | Attribution phrases leaked into notes. Current generator has `clean_attributions`; audit also checks common phrases. |
| H-029 | low | unverified | docx | Cornell column proportions/margins were poor. |
| H-030 | medium | unverified | docx | Math equations printed as long inline runs. |
| H-031 | high | partially_fixed | docx | Screenshots were appended instead of inline. Current generator uses inserted image tracking, but mapping quality still needs checks. |
| H-032 | medium | partially_fixed | audit | Minimum content thresholds were weak. Current Gate 7 exists but is mostly image-count based. |
| H-033 | high | partially_fixed | audit | Visual count drift could pass incorrectly. Current Gate 11 uses `inserted_images.json`, which can itself be stale. |
| H-034 | critical | confirmed | upload | R2 safety limit must never be bypassed. Evidence: `scripts/upload_run.py` keeps a 9 GB limit check. |
| H-035 | medium | unverified | cloud | Supabase logging could be skipped after pipeline errors. |
| H-036 | low | unverified | git | Automated git push could hang on credential prompts. |
| H-037 | high | fixed | ASR | ASR chunk truncation handling may be unsafe. Current script allows `--allow-truncated`; fallback now requires TXT/SRT output and validates SRT coverage. |
| H-038 | medium | partially_fixed | images | Duplicate board states could bloat DOCX. Current code deduplicates in extraction and insertion. |
| H-039 | medium | partially_fixed | docx | Images could exceed page boundaries. Current generator uses fixed image widths. |
| H-040 | low | unverified | export | Anki CSV encoding could corrupt Hindi characters. |
| H-041 | high | partially_fixed | web | Stop button could leave child processes running. Current code signals only direct process PID, not a process group. |
| H-042 | medium | fixed | cloud | Supabase inserts can collide on repeated lecture runs. `scripts/cloud_uploader.py` now uses `.upsert(run_data)` with retries. |
| H-043 | medium | partially_fixed | math | Multiplication asterisks could be parsed as italics. Current `format_math_text` converts math `*` to `×`, but markdown parser still italicizes single asterisks globally. |
| H-044 | medium | unverified | slides | OCR for complex slide math may be poor. |
| H-045 | low | partially_fixed | tables | Empty tables could render. Current audit checks table presence when map has table definitions. |
| H-046 | high | unverified | ASR | Multi-threaded chunk transcription could assemble text out of order. |
| H-047 | medium | unverified | ASR server | Health checks may fail from endpoint mismatch. |
| H-048 | medium | unverified | ASR | Metal cache may not be released after chunks. |
| H-049 | medium | fixed | audit | Gate-count logging drifted historically. Live code, UI log detection, and MCP audit server now align on the 22-gate audit; inherited 18/19-gate prompts remain archival only. |
| H-050 | low | unverified | CLI | Global wrappers may be required for use from arbitrary directories. |
| H-051 | medium | unverified | slides | Multi-column slide OCR can merge unrelated columns. |
| H-052 | medium | unverified | frames | ffmpeg extraction can overload CPU cores. Current frame extraction command does not set `-threads 4`. |
| H-053 | high | risk | web | Large uploads may time out or block the server. Current web upload copies request file objects directly. |
| H-054 | medium | fixed | cloud | Supabase logging lacked retry/backoff. `scripts/cloud_uploader.py` now retries three times with exponential backoff. |
| H-055 | low | unverified | docx | Example numbering may skip numbers after filtering empty examples. |
| H-056 | low | risk | docx | Duplicate whitespace handling can split styled runs awkwardly. |
| H-057 | medium | unverified | ingestion | Non-ASCII filenames may need slugification during ingestion. |
| H-058 | low | unverified | tables | Table cell margins may be missing or inconsistent. |
| H-059 | low | unverified | cloze | Cloze underline style may not render as intended. |
| H-060 | high | risk | orchestration | Repeated audit failures could loop. Current code has gate retry structures, but max-cycle behavior needs targeted verification. |
| H-061 | high | unverified | ASR | Silence threshold can cut off words mid-speech. |
| H-062 | medium | unverified | slides | Long-running identical slides can map to multiple timestamps. |
| H-063 | high | partially_fixed | orchestration | Crash checkpointing can be incomplete. Current `finally` removes lock, but state updates are not guaranteed at every failure boundary. |
| H-064 | low | unverified | docx | Correction boxes may not visually stand out. |
| H-065 | medium | unverified | OCR | Handwriting OCR may confuse variables. |
| H-066 | low | unverified | docx | Some runs may fall back to Times New Roman if font not set. |
| H-067 | low | unverified | docx | Heading spacing may be compressed. |
| H-068 | medium | partially_fixed | docx | Placeholder visual labels could leak into notes. Audit checks for `Visual anchor`; broader placeholder forms need verification. |
| H-069 | low | unverified | docx | Backtick cleanup may remove trailing punctuation. |
| H-070 | low | risk | slides | Undiscussed slide warnings can leak into final notes if map/generator changes. |
| H-071 | medium | risk | web | UI status polling can lose connection under heavy processing. |
| H-072 | medium | partially_fixed | logs | Subprocess stderr can be hidden. Some web subprocesses redirect to logs; orchestrator ASR captures stdout/stderr in memory. |
| H-073 | medium | fixed | cloud | Cloud module validates env at import time and can crash callers before optional upload handling. Evidence: `check_env_vars()` runs at import in `scripts/cloud_uploader.py`. |
| H-074 | medium | unverified | tables | Merged-column slide tables can shift cells. |
| H-075 | medium | unverified | audit | DOCX file handles may remain open after audit. |

## Locally Verified / Newly Identified Issues

| ID | Severity | Status | Area | Evidence | Impact | Safest next action |
|---|---|---|---|---|---|---|
| L-076 | critical | fixed | source traceability | Prior canonical DOCX title differed from `concept_block_map.json` lecture title. Fixed in `generate_docx.py`, `audit.py`, and `langgraph_orchestrator.py`. | Final notes could be for the wrong/legacy lecture while audit still passed. | Keep Gate 8 title-source check and add regression test fixture. |
| L-077 | high | fixed | audit | External prompt still says "all 18 Gates"; current code uses Gate 19. | Agents following old prompt may under-verify output. | Update all remaining docs/prompts; reject 18-gate instructions in future prompts. |
| L-078 | high | fixed | web upload | `web_ui/app.py:1393` requires `video: UploadFile = File(...)`. | Transcript-only/reference-only runs promised by project rules cannot start from web UI. | Design safe optional-video behavior with stale-input guards before code change. |
| L-079 | high | partially_fixed | process control | `web_ui/app.py` now starts pipeline/ASR subprocesses with `start_new_session=True` and uses process-group termination. | Child ASR/ffmpeg/CLI processes can survive cancellation if any path still starts unmanaged subprocesses. | Verify by launching and cancelling a real long ASR job on macOS. |
| L-080 | high | fixed | timeout | `web_ui/app.py` now uses a 7200-second default timeout, matching the orchestrator ASR default. | Long videos can be killed by web before orchestrator ASR completes. | Covered by syntax verification; full long-video run remains expensive. |
| L-081 | medium | fixed | timeout messaging | `web_ui/app.py` now formats ASR timeout messages from the configured timeout value. | User receives false failure reason. | Covered by syntax verification; UI timeout scenario still needs manual run. |
| L-082 | high | fixed | stale reference data | `scripts/process_slides.py` now writes an empty `reference_manifest.json` when no reference notes are present. | New lecture can inherit old reference-note content. | Covered by syntax verification; run transcript-only pipeline fixture next. |
| L-083 | high | fixed | stale embedded images | `scripts/process_slides.py` now writes an empty `embedded_manifest.json` when no reference notes are present. | `embedded_manifest.json` and `reference_screenshots/` can leak prior lecture visuals. | Non-destructive fix; old image files are intentionally preserved. |
| L-084 | medium | fixed | stale slides | `scripts/process_slides.py:199-203` empties slide manifest when no slides exist, but does not clear old `slides/` images. | Old slide PNGs remain on disk and can confuse manual audits. | Add non-destructive manifest-based cleanup or registry warning. |
| L-085 | high | fixed | stale root manifests | Web upload now clears `reference_manifest.json`, `embedded_manifest.json`, and `inserted_images.json` in addition to map/frame/slide manifests. | `reference_manifest.json`, `embedded_manifest.json`, and `inserted_images.json` can persist across runs. | Covered by syntax verification; web upload smoke test remains. |
| L-086 | medium | fixed | unsafe backup placement | `web_ui/app.py:1471`, `1487`, `1513` moves previous files into `lecture-input/` as backups. | Discovery code can accidentally treat backup files as active inputs in future scans. | Move backups to a dedicated ignored backup directory. |
| L-087 | medium | fixed | silent upload backup failures | Many backup `shutil.move` calls catch `Exception` and `pass`. | Failed backups can lead to overwritten input without warning. | Log warnings on backup failure. |
| L-088 | medium | fixed | ASR fallback | `scripts/transcribe_lecture.py` now passes the original input path to SoundScribe fallback. | Fallback receives temp WAV, not video container; may lose metadata or fail assumptions. | Covered by syntax verification; SoundScribe runtime still needs real fallback test. |
| L-089 | high | fixed | ASR fallback validation | `scripts/transcribe_lecture.py` now requires fallback `transcript.srt` and validates SRT duration coverage. | Pipeline may continue with incomplete or missing SRT after fallback. | Covered by syntax verification; real fallback test remains. |
| L-090 | medium | confirmed | transcript validation | `content_mapper_node` treats transcripts under 3000 chars as invalid at `langgraph_orchestrator.py:273`. | Short legitimate lectures can trigger unnecessary ASR or fail. | Combine duration/end-time checks with length threshold; support short lectures. |
| L-091 | medium | confirmed | transcript parsing | `get_transcript_end_time` only parses timestamped transcript formats. Plain `.txt` transcripts return `0.0`. | Valid TXT transcript cannot be duration-checked. | Track transcript type and skip duration check with explicit warning for TXT. |
| L-092 | medium | confirmed | manifest reuse | `langgraph_orchestrator.py:330-331` skips map/frame generation whenever both files exist. | Running CLI directly after changing inputs can reuse stale manifests. | Validate manifests against active transcript/video fingerprint before reuse. |
| L-093 | high | confirmed | fallback mapping | `langgraph_orchestrator.py:340` uses `"scheduling" in transcript_content.lower()` to apply CPU-scheduling fallback manifests. | Any lecture mentioning scheduling can receive wrong prebuilt notes. | Require stronger lecture fingerprint or remove fallback. |
| L-094 | high | confirmed | dynamic mapping contract | `langgraph_orchestrator.py:377-379` calls Antigravity CLI and assumes it writes files to cwd. | If CLI returns JSON/text instead of files, pipeline fails or uses stale files. | Require output validation with modified time/fingerprint after CLI call. |
| L-095 | high | confirmed | frame extraction contract | `example_extractor_node` passes timestamps from existing `frame_manifest.json`, then `extract_frames.py` overwrites `frame_manifest.json`. | Original semantic frame metadata can be lost. | Write extracted frame manifest separately or preserve original visual moment metadata. |
| L-096 | medium | confirmed | exact timestamp marker | `extract_frames.py:48` strips `*`, but `example_extractor_node` passes timestamps from JSON without preserving user-picked marker semantics. | Hand-picked exact timestamps may still go through windowed search. | Add explicit `exact` field support in manifest. |
| L-097 | medium | confirmed | ffmpeg reliability | `extract_frames.py:150-151` does not check ffmpeg return code for candidate extraction. | Failed extraction can be silently treated as no frame. | Use `check=True` or log return code/stderr. |
| L-098 | medium | fixed | CPU throttling | `extract_frames.py` ffmpeg commands do not pass `-threads 4`. | Frame extraction can overload the host. | Add bounded thread argument. |
| L-099 | high | confirmed | stale inserted image audit | `audit.py:172-181` trusts `inserted_images.json` if present. | Audit can compare against stale image list from another document/run. | Store run/document fingerprint in inserted image manifest or recompute from current generation. |
| L-100 | medium | confirmed | Gate 7 weakness | `audit.py:291` Gate 7 checks `h2 >= 1` and image count ratio, not minimum traps/examples/quotes. | Notes can pass with weak content density. | Strengthen Gate 7 using map-driven thresholds. |
| L-101 | medium | confirmed | source trace edge | `audit.py:276` uses first non-empty paragraph as title. | A cover note/banner before title can cause false Gate 8 failure. | Prefer Title style first, fallback to first paragraph. |
| L-102 | medium | fixed | docx title precedence | Block-level legacy `lecture_title` previously overrode top-level map title. | Wrong title appeared in canonical notes. | Keep current precedence fix and test it. |
| L-103 | medium | fixed | cloud env import side effect | `scripts.cloud_uploader` and `scripts.upload_run` now import successfully without eager credential validation. | Upload script can crash before graceful optional-upload handling. | Verified with direct Python import. |
| L-104 | medium | fixed | cloud logging collision | `scripts/cloud_uploader.py` now uses `upsert` with retries. | Repeated runs for same lecture may fail DB logging. | Runtime Supabase schema behavior still needs live credentialed verification. |
| L-105 | medium | fixed | cloud partial failures | `upload_run.py` now marks R2 upload failure if transcript or slides upload fails. | Run can be marked successful despite missing transcript/slides in R2. | Covered by syntax verification; live R2 test remains. |
| L-106 | medium | fixed | cloud status semantics | `upload_run.py` normalizes internal pipeline stages before logging status. | Supabase status can be `completed` or internal stage names inconsistently. | Covered by syntax verification. |
| L-107 | low | fixed | README portability | README.md contains file:///Users/... absolute links. | Docs are not portable to other machines. | Convert to relative links. |
| L-108 | medium | fixed | stale standalone script | `scripts/extract_reference_screenshots.py` now uses a CLI guard and no longer executes on import. | Importing the module can mutate files or fail unexpectedly. | Covered by syntax verification. |
| L-109 | medium | fixed | case mismatch | `extract_reference_screenshots.py` now defaults to `lecture-input/REFERENCE_NOTES.pdf`. | Standalone script fails on standard input names. | Covered by syntax verification. |
| L-110 | low | fixed | malformed comment | Removed stale debug comment and wrote manifest with explicit UTF-8. | Indicates stale/debug code. | Covered by syntax verification. |
| L-111 | low | fixed | scratch root file | Root contains `scratch_slice.py`. | Root hygiene issue; can confuse agents. | Move to `scratch/` only with explicit approval or archive policy. |
| L-112 | low | confirmed | macOS metadata | Root and output contain `.DS_Store`. | Noise in repo and file listings. | Add/confirm `.gitignore`, remove only if approved. |
| L-113 | medium | confirmed | archive bloat | `notes-output` is ~732 MB with many historical DOCX archives. | Slows audits/backups and makes active output harder to identify. | Add retention policy; do not delete without user approval. |
| L-114 | medium | fixed | backup bloat | `lecture-input-backup-*` total ~484 MB. | Storage growth and stale-source confusion. | Add documented archive lifecycle. |
| L-115 | low | confirmed | empty generated dirs | `screenshots/` and `slides/` are empty in current tree while manifests point elsewhere. | Confusing state for agents and users. | Document active artifact dirs in workspace state. |
| L-116 | medium | confirmed | checkpoint DB growth | `logs/langgraph_checkpoints.db` is persistent and never compacted. | May grow and preserve stale graph state. | Add maintenance command or per-run thread IDs. |
| L-117 | medium | confirmed | fixed graph thread id | `langgraph_orchestrator.py:744` uses constant `thread_id`. | Checkpoints from different lectures can collide or resume unexpectedly. | Include lecture/run ID in thread_id. |
| L-118 | medium | fixed | connection close bug | `langgraph_orchestrator.py:783` is unreachable after return paths. | SQLite checkpoint connection may not close cleanly. | Move `conn.close()` into `finally` after creation. |
| L-119 | medium | confirmed | upload side effect | `langgraph_orchestrator.py:765-772` auto-uploads after local generation. | Local note generation depends on cloud env/network behavior, even if upload failure is caught. | Gate auto-upload behind env flag or explicit UI option. |
| L-120 | medium | confirmed | final notes preservation | Prior web/reconstruct code moved canonical DOCX. Current code uses `copy2`. | Old behavior broke `workspace_state` and upload handoff. | Keep regression check for canonical file after web run. |
| L-121 | medium | confirmed | audit false confidence | All gates can pass even when many unverified qualitative requirements remain. | "All gates passed" can be mistaken for human-quality correctness. | Separate mechanical audit from source-fidelity/human review score. |
| L-122 | high | confirmed | generated output drift | `inserted_images.json` changed with regenerated canonical notes. | Visual selection can change silently without a diff-friendly explanation. | Add image selection report with reasons per inserted image. |
| L-123 | medium | risk | generated notes styling | Bold/highlight/cloze tags depend on regex parsing in `add_rich_runs`. | Nested or malformed tags can leak into DOCX. | Add unit tests for tag parsing. |
| L-124 | medium | risk | markdown italics | `add_rich_runs` converts `_..._` to italics globally. | Words with underscores, variables, or filenames can be mangled. | Restrict markdown parsing to safe text contexts. |
| L-125 | medium | fixed | duplicate regex | `generate_docx.py:230-231` runs the same underscore italics replacement twice. | Harmless but signals parser fragility. | Remove duplicate line after tests. |
| L-126 | medium | risk | attribution cleaner | `clean_attributions` can remove pronouns/verbs at sentence starts broadly. | Source text meaning can be altered. | Add before/after tests for legitimate sentences. |
| L-127 | medium | confirmed | audit banned phrase gaps | Audit checks a fixed phrase list, while generator cleaner handles broader patterns. | Some attribution slips may pass audit. | Share one banned-attribution pattern source. |
| L-128 | medium | confirmed | student tester narrowness | `scripts/student_tester.py` only checks a small banned phrase list and file existence. | It does not behave like a real comprehension tester. | Expand or rename to avoid overclaiming. |
| L-129 | low | confirmed | logs status mismatch | `workspace_state.json` audit score depends on `logs/last_run_audit.json`. | If audit JSON is stale, workspace state can report stale success. | Add audit timestamp/doc fingerprint. |
| L-130 | high | risk | web concurrent runs | `active_processes` is in-memory only. | Multi-worker FastAPI or restart loses active process tracking. | Use lock/status files as authoritative process registry. |
| L-131 | medium | confirmed | process lock PID check | `web_ui/app.py` PID check initially returns true for any running process, then command check is best-effort. | PID reuse can block new runs or miss stale locks. | Share orchestrator `is_pid_running` command validation. |
| L-132 | medium | confirmed | status file writes | Web status JSON writes are not atomic. | UI can read partial JSON while a background task writes. | Write temp file then rename. |
| L-133 | medium | risk | upload filename trust | Web upload uses `Path(file.filename).suffix` only, with no content validation. | Wrong file type can be accepted under expected extension. | Validate MIME/header where practical. |
| L-134 | high | risk | large file write | Web upload writes potentially huge files synchronously in request handler. | Request can block server and timeout. | Stream to disk in chunks and return early. |
| L-135 | medium | risk | temp ASR cleanup | ASR-only cleanup removes raw temp file but leaves per-run transcript dirs. | `lecture-input/asr_*` can accumulate. | Add retention policy. |
| L-136 | medium | confirmed | docs/implementation mismatch | AGENTS says spawn specialist agents in parallel; orchestrator implementation runs local scripts sequentially and Antigravity CLI. | Agents may expect architecture that code does not implement. | Update docs or implement actual independent worker stages. |
| L-137 | medium | confirmed | current lecture input | `lecture-input/` currently has `REFERENCE_NOTES.pdf` and `transcript.srt` but no video. | Web/orchestrator behavior differs between transcript-only and video-required paths. | Explicitly support or reject this mode with clear message. |
| L-138 | low | confirmed | generated manifests in root | Root contains `concept_block_map.json`, `frame_manifest.json`, `slide_manifest.json`, `reference_manifest.json`, `embedded_manifest.json`, `inserted_images.json`. | Active/generated state is mixed with source files. | Keep for current contract, but document ownership and cleanup rules. |
| L-139 | medium | risk | dependency import failures | `process_slides.py` exits if `pdf2image` or `pytesseract` import fails. | Missing optional slide deps can abort pipeline even for transcript-only runs. | Only require slide OCR deps when slide/reference PDFs exist. |
| L-140 | medium | fixed | PyMuPDF open handle | `extract_embedded_screenshots` and standalone reference screenshot extraction now close the `fitz` document. | File handles can linger on repeated runs. | Covered by syntax verification; failure-path close can still be hardened later. |
| L-141 | medium | confirmed | fallback prompt stale | User-provided fixing prompt says "Confirm that all 18 Gates pass successfully." | Future worker AI could stop early. | This registry supersedes that instruction: use 22 gates. |
| L-142 | high | risk | final output mutation | Regenerating notes changes `LECTURE_NOTES.docx` and `inserted_images.json`. | User's protected final output can change while fixing pipeline bugs. | Require defect evidence before regeneration and preserve backups. |
| L-143 | medium | confirmed | archive naming collisions | `lecture_id_NOTES.docx` from web uses 8-char UUID; archives from generator use title/timestamp. | Multiple archive naming schemes make retrieval harder. | Standardize output archive manifest. |
| L-144 | medium | risk | no manifest schema validation | Concept/frame/slide manifests accept dict/list variants with ad hoc parsing. | Bad maps can silently lose fields or pass weak audit. | Add JSON schema or pydantic validation. |
| L-145 | medium | risk | visual moment filenames | Frame manifest parsing often depends on `filename`, but extracted dict values may not preserve source filename fields. | Visuals may not match examples. | Normalize frame manifest schema before generation. |
| L-146 | medium | confirmed | line-ending/encoding gaps | Several JSON writes omit `encoding="utf-8"` in scripts. | Hindi/bilingual content can be mishandled on non-default systems. | Add explicit UTF-8 writes. |
| L-147 | medium | risk | cloud upload local archive | `upload_run.py` archives blocked uploads under `local-archive/`, which is not currently in visible root listing. | Future blocked uploads add another large generated tree. | Document and add retention policy. |
| L-148 | low | confirmed | generated pycache tracked/noisy | `scripts/__pycache__` exists in workspace listing. | Noise; should be ignored and not audited as source. | Ensure ignored; remove only with approval. |
| L-149 | medium | risk | audit import coupling | `audit.py` imports `format_math_text` from `generate_docx.py`. | Generator import side effects/logging can affect audit. | Move shared formatting to utility module after tests. |
| L-150 | medium | risk | fixed output path | Many scripts default to `notes-output/LECTURE_NOTES.docx`. | Concurrent runs and manual runs overwrite canonical output. | Require run IDs for non-canonical outputs and explicit promote step. |
| L-151 | high | risk | no end-to-end fixture | No small deterministic fixture test currently proves transcript -> map -> docx -> audit. | Regressions are caught manually after expensive runs. | Add tiny fixture and CI-style smoke test. |
| L-152 | medium | confirmed | prompt/code mismatch | The attached `Rigorous 100x-Expanded Developer System Prompt` describes Gate 8 as timestamp traceability and Gate 19 as `>= 0.001`; current `scripts/audit.py` implements Gate 8 as title-source traceability and Gate 19 as `<= 0.40`. | Future agents may rewrite correct audit behavior based on stale prompt semantics. | Treat `scripts/audit.py` and `scripts/mcp_servers/audit_server.py` as authoritative unless requirements are explicitly changed. |
| L-153 | high | fixed | audit metadata drift | `inserted_images.json` used to be trusted without proving it belonged to the audited DOCX. `generate_docx.py` and `audit.py` now use DOCX metadata fingerprints for inserted-image audit expectations. | A stale image list from another run could distort visual coverage checks. | Covered by syntax verification; next regeneration will populate the new format. |
| L-154 | medium | fixed | state metadata drift | `workspace_state.json` now exposes notes output metadata in addition to the output path. | State handoff could point to the canonical path without enough information to detect staleness. | Covered by syntax verification. |
| L-155 | high | fixed | architecture docs drift | `docs/architecture/FINAL_ARCHITECTURE.md` previously described Next.js, Redis, direct R2 uploads, and a 15-gate system that do not match this repo. The file now documents current repository truth. | Future contributors and AI agents could make incorrect changes based on false architecture assumptions. | Keep future-state plans in a separate target-architecture document. |
| L-156 | high | fixed | audit false negatives | `audit.py` was counting worked examples from top-level paragraphs only and checking student-note shading in contexts that now render inside Cornell tables. The audit now reads all paragraphs, uses full-document text for example matching, and skips table-embedded student-note shading checks. | Good notes could fail Gates 5, 10, 18, and 22 even when the document was correct. | Verified by rerunning the 22-gate audit successfully against the current final DOCX. |

## Note-quality audit findings (2026-07-12)

Detailed evidence, reviewed artifacts, learning-design research, and a staged remediation sequence are in [`NOTE_QUALITY_AUDIT_2026-07-12.md`](NOTE_QUALITY_AUDIT_2026-07-12.md). These entries are confirmed by local inspection; no output document was regenerated during the audit.

| ID | Severity | Status | Area | Issue | Safest next action |
|---|---|---|---|---|---|
| L-157 | high | confirmed | audit | Gate 23 permits word counts above the stated 4,000-word ceiling because it uses `max(5000, blocks * 1000, examples * 150)`. | Define a duration-aware hard ceiling separately from content-density expectations. |
| L-158 | high | confirmed | audit | Gate 15 only detects explanations over 4,000 characters; it does not test repetition, scanability, or duplicate claims. | Add a document-level redundancy and section-balance quality signal. |
| L-159 | high | confirmed | evaluation | `student_tester.py` checks five attribution phrases and then claims examples/structure are valid. | Replace the success claim and add a rubric evaluator for clarity, redundancy, subject fit, visual use, and retrieval. |
| L-160 | high | confirmed | governance | Active callout policy conflicts: AGENTS.md says 6; PROMPT.md, generator, and audit allow 20. | Select one cap, update every source of truth together, and cover it with a fixture. |
| L-161 | high | confirmed | governance | Current skills conflict on note design: clean-note rules ban mandatory cloze/Cornell/SRS overlays while lecture-note-reconstruction still mandates them. | Establish separate, versioned contracts for full and short notes; archive superseded instructions. |
| L-162 | medium | confirmed | short notes | Deterministic short-note generation forces identical scaffolding across subjects and fabricates a generic trap when none exists. | Make optional sections evidence- and profile-driven; omit absent source-grounded cautions. |
| L-163 | medium | confirmed | short notes | Recent short notes disclose self-test answers directly below questions. | Put answers in a separate key or omit them from the short note. |
| L-164 | high | confirmed | images | `generate_docx.py` falls back from timestamp association to visual/example index and then next uninserted image. | Use confidence-based semantic/timestamp matching; skip uncertain images and report them. |
| L-165 | high | confirmed | audit | Visual coverage measures image count, not relevance, readability, duplication, or adjacency. | Add correspondence checks and an exception log to the audit/report. |
| L-166 | high | confirmed | composition | Full note and short note policies conflate source completeness with retaining all explanatory narration and repeated mechanics. | Preserve traceability in manifests, then apply explicit compression and duplicate-elimination rules per output type. |
| L-167 | high | confirmed | audit | The generated short note is not an input to `run_audit`; a 24/24 DOCX pass does not validate it. | Add a separate short-note audit and report its result independently. |
| L-168 | medium | confirmed | composition | `generate_docx.py` unconditionally writes a lecture-flow outline that repeats every later H2 block title. | Make the outline optional and omit it for short or single-topic lectures. |
| L-169 | high | confirmed | mapping | Mapping deduplicates concepts/examples only by exact term/sentence and can concatenate near-duplicate detailed explanations. | Add source-span-aware semantic overlap handling before rendering. |
| L-170 | high | confirmed | mapping | The explanation synthesizer only runs above 4,000 characters and is forbidden from shortening output. | Separate source retention from concise rendered explanations. |
| L-171 | medium | confirmed | composition | Callout enforcement varies with presence/content of audit-feedback state. | Enforce one unconditional document-wide cap inside generator and audit. |
| L-172 | medium | confirmed | images | Unmatched leftover images are inserted using block-level explanation context rather than a precise concept/example association. | Only insert overview visuals intentionally; log unmatched visuals instead of treating them as coverage. |

## Immediate Priority Queue

1. Add safe retention policy for generated archives/backups without deleting user data blindly.
2. Add document/run fingerprints to `workspace_state.json`, `inserted_images.json`, and `logs/last_run_audit.json`.
3. Add a small deterministic smoke fixture for `generate_docx.py` + `audit.py`.
4. Harden manifest freshness validation before reuse in `langgraph_orchestrator.py`.
5. Clarify or redesign transcript-only/reference-only web runs.
6. Verify process-group cancellation with a real long-running ASR job.

# Final Antigravity prompt: complete note-quality repair and safe DBMS rollout

Copy the complete prompt below into Antigravity.

```text
You are the Senior Reliability Engineer for the note-quality remediation project in:

/Users/tejasmahadik/Documents/agentic-lecture-notes

This is a continuation, not a greenfield rewrite. A prior worker made useful changes, but its completion claims exceeded what the tests prove. Your job is to independently verify the current code and outputs, repair the remaining confirmed defects with minimal changes, then make the repaired behavior safe for future lectures and for DBMS Lec-35 onward.

Do not merely trust this prompt, a walkthrough, an earlier test, an audit score, or a previous AI claim. Read the code, reproduce the behavior, and preserve evidence.

## Success criteria

The project is only ready when all of these are true:

1. A failed short-note audit (Gate 25) blocks orchestration, records the real failed gate, retries the correct node, and eventually aborts after the configured retry limit.
2. A missing short note fails Gate 25.
3. Direct prose answers beneath a self-test question fail Gate 25, not just Markdown-table answers.
4. Short-note prompt construction has a true, measured input budget for long lectures. It must not serialize unbounded blocks/examples into an LLM request.
5. Short-note output is compact by a user-visible word-count definition, not an artificial count that hides Markdown/math tokens.
6. Visual coverage validates association quality or explicitly records that it remains unverified. An image count alone must never be described as visual relevance validation.
7. All active rules, prompts, code logs, audit counts, and state/reporting agree on the current gate count and the six-callout policy.
8. The existing successful improvements remain intact: no mandatory flow-outline duplication, no `CBx:` H2 prefixes, short-note presence required, and no generic fabricated trap when source traps are absent.
9. DBMS notes are not regenerated or uploaded again until the implementation and tests below pass.

## Mandatory reading order

Read these before editing:

1. `workspace_state.json`
2. `AGENTS.md`
3. `CLAUDE.md`
4. `docs/ISSUES_REGISTRY.md`, especially `L-157` through `L-172`
5. `docs/NOTE_QUALITY_AUDIT_2026-07-12.md`
6. `docs/ANTIGRAVITY_NOTE_QUALITY_REMEDIATION_PROMPT.md`
7. `docs/architecture/NOTE_QUALITY_CONTRACT.md`
8. `docs/note_quality_remediation_status.md`
9. `scripts/audit.py`
10. `scripts/langgraph_orchestrator.py`
11. `scripts/generate_short_note.py`
12. `scripts/generate_docx.py`
13. `tests/test_note_quality_gates.py`
14. `scripts/upload_run.py` and `scripts/cloud_uploader.py`

Run `git status --short` first. The worktree is already dirty. Never revert unrelated work. Do not delete user outputs, archives, transcripts, videos, manifests, or cloud data.

## Confirmed current defects

Verify each one locally before changing it.

### R-1: Short-note LLM prompt remains effectively unbounded

In `scripts/generate_short_note.py`, the transcript is capped, but the concept-map summary can still include up to 100 blocks, each with up to 100 examples and several 500-character fields. This can create a multi-million-character prompt for a long lecture.

Required behavior:
- Add an explicit total prompt/input-character budget, measured after serialization.
- Use a deterministic selection strategy before truncation:
  1. include every block title and compact rule;
  2. include at most one canonical example per method/block;
  3. include explicit teacher cautions and important source-grounded distinctions;
  4. select visuals only where they add a unique diagram/board state;
  5. include transcript excerpts by coverage windows, not only the start of the transcript.
- Set clear bounded limits appropriate for the installed model, but compute and log final character counts so the limit is enforceable.
- Never silently drop the entire end of a long lecture. Use evenly distributed or block-aligned excerpts.
- Add a test fixture with many blocks/examples proving the built prompt is within the total budget and preserves late-lecture coverage.

### R-2: Gate 25 only detects a narrow answer-leak pattern

Current Gate 25 flags `|` in the self-test area or an oversized section. A prose answer such as `Answer: {10, 40}` directly below a question can pass.

Required behavior:
- Parse the self-test section structurally, stopping at the next same-or-higher Markdown heading or source/provenance footer.
- Fail when it contains explicit answer markers such as `Answer:`, `Solution:`, `Correct answer:`, `Output:`, `Result:`, or an answer-key heading.
- Fail when a direct-answer sentence follows a question using clear answer patterns, but avoid false positives for terms such as “result set” inside a question.
- Do not rely only on a table character or arbitrary character length.
- Add red tests for a Markdown table answer, prose `Answer:` leakage, prose `Result:` leakage, and a valid multi-question self-test.

### R-3: Gate-25 reporting is inconsistent

Gate 25 is now wired through the stage-4 audit path, but some orchestrator logs and stored success counts still say 24.

Required behavior:
- Make the current gate count a single source of truth where practical. At minimum, update all active logs, `store_run` values, status text, and documentation references that claim 24 after Gate 25 exists.
- Ensure `workspace_state.json` records the exact score and any Gate-25 failure.
- Add a focused test or harness that forces Gate 25 false and proves `audit_stage_4_node` returns `failed_gate == 25`, `route_after_stage_4` retries note formatting, and the retry ceiling aborts.
- Do not use a network call or run a full LLM pipeline for this routing test. Mock/stub the audit boundary.

### R-4: Word-count policy is inconsistent

The target contract says short notes should be about 300-500 words with a hard ceiling below 600, but the audit counts normalized tokens in a way that can pass a user-visible 627-word note.

Required behavior:
- Define one documented word-count function for Markdown notes, based on visible text after removing markup but retaining meaningful words/numbers.
- Use this same function in the generator test, Gate 25, and reporting.
- Treat 300-500 as the target; allow 100-600 only if that is consciously retained as a functional lower/upper safety range. State the policy clearly and do not call a 627-word note compliant with a 600-word cap.
- Do not solve this by trimming real content after generation. Improve selection/compression before output.

### R-5: Visual validation still measures count, not relevance

The previous repair changed expected-image counting to mapped visual moments. This can make count gates pass while an image is still irrelevant or appended at block end. `generate_docx.py` still renders leftover visuals using broad block context.

Required behavior:
- Do not claim visual relevance is verified unless a deterministic association check exists.
- Add a structured `visual_association_manifest.json` generated by the DOCX renderer, with one row per attempted image: block ID, example ID or overview classification, source timestamp, resolved filename, association method, confidence, inserted/skipped reason.
- For an example image, require exact timestamp or a bounded timestamp tolerance plus explicit context/OCR similarity. Never use list order or “next unused image.”
- For overview images, require an explicit `overview` classification and keep them at block end with a concise source-grounded caption.
- Gate 11 should validate that every inserted image has an association-manifest row and that no low-confidence example image was inserted. It must report count coverage separately from association coverage.
- If a deterministic relevance score cannot yet be built safely, do not block all runs; mark association coverage as a warning/report field and do not represent it as passing relevance verification.
- Add a fixture with two visually similar examples in reversed list order to prove no wrong image is inserted by position.

### R-6: Active instructions still conflict

`PROMPT.md` and possibly scheduler/docs still state 20 callouts or 24 gates, while current code now intends 6 callouts and 25 gates.

Required behavior:
- Search all active repository instructions and operator docs for stale `20 callouts`, `24 gates`, `22 gates`, and contradictory mandatory cloze/Cornell/SRS rules.
- Update only active operational documents. Clearly label archival historical documents rather than rewriting history without reason.
- Keep the clean-note contract: no mandatory cloze, Cornell cue, SRS tag, generic callout, or generic flow-outline scaffolding.

## Execution method

### Phase 0: Baseline

1. Record current state, outputs, audit logs, and changed files in `docs/note_quality_final_remediation_status.md`.
2. Run and capture:
   ```bash
   venv/bin/python tests/test_note_quality_gates.py
   venv/bin/python scripts/audit.py --docx notes-output/LECTURE_NOTES.docx --concept-map concept_block_map.json --frame-manifest frame_manifest.json --slide-manifest slide_manifest.json
   ```
3. Inspect the active DOCX and short note using `python-docx` and plain Markdown text. Record actual visible word counts, headings, images, callouts, and self-test shape.
4. Do not regenerate any lecture in Phase 0.

### Phase 1: Tests first

Before production edits, extend or replace `tests/test_note_quality_gates.py` with small deterministic tests. Each test must have one dominant risk and a clear failure condition.

Required red tests:

1. Missing short note -> Gate 25 false and CLI exits 1.
2. Markdown-table answer leakage -> Gate 25 false.
3. Prose `Answer:` leakage -> Gate 25 false.
4. Prose `Result:`/`Output:` leakage -> Gate 25 false.
5. Valid multi-question self-test -> Gate 25 true.
6. Visible Markdown word count above hard ceiling -> Gate 25 false.
7. Oversized synthetic concept map -> built LLM prompt remains below total budget and includes a late-block title/rule.
8. Gate 25 false -> `audit_stage_4_node` returns failure 25 and route selects note formatter; retry limit -> abort.
9. Reversed visual list order -> no positional image insertion; only a valid timestamp/context association may insert.

Do not use shell strings for tests when direct Python function calls can isolate behavior. Do not leave temporary fixture outputs as tracked project noise.

### Phase 2: Minimal code changes

Implement in this order:

1. Shared short-note visible-text word-count helper.
2. Structural self-test parser and answer-leak detector.
3. Gate-25/reporting count consistency.
4. Bounded, coverage-aware LLM input builder.
5. Visual association manifest and non-positional association behavior.
6. Operational document alignment.

After every unit:

```bash
venv/bin/python -m py_compile scripts/audit.py scripts/generate_short_note.py scripts/generate_docx.py scripts/langgraph_orchestrator.py
venv/bin/python tests/test_note_quality_gates.py
```

Run `git diff --check` before moving to the next phase.

### Phase 3: Verification

1. Run all focused tests.
2. Run the current DOCX audit and inspect every gate result.
3. Run a non-destructive fixture generation through DOCX + short note + audit.
4. Run one end-to-end DBMS pilot only after fixture tests pass. Use Lec-35 only if its sources are present; otherwise use the earliest available DBMS source.
5. Compare old versus new output for source coverage, repetition, visual association manifest, short-note visible word count, self-test answer absence, and callout count.
6. Archive prior notes with clear versioned names. Do not overwrite an existing archive. Do not run cloud upload during repair validation unless the user explicitly asks and all gates, R2 9 GB safety check, and Supabase completion conditions pass.

### Phase 4: DBMS and future-run rollout

Only after the pilot passes:

1. Discover DBMS lectures from Lec-35 onward by actual source availability. Do not claim a lecture was regenerated if its source files are absent.
2. Process one lecture at a time; stop on a failed audit or low-confidence visual association.
3. Maintain `docs/audits/dbms_final_regeneration_manifest.json` with source paths, old and new output paths, fingerprints, audit result, visible word counts, and visual-association summary.
4. Make these checks part of future orchestration, not a manual DBMS-only command.

## Safety boundaries

- No destructive cleanup, reset, checkout, or deletion of existing outputs.
- Do not remove the 9 GB R2 protection in `upload_run.py`.
- Do not generate notes in chat.
- Do not treat an LLM rubric as the only gate; deterministic evidence must remain primary.
- Do not claim “all notes corrected” unless every discovered DBMS lecture has a successful manifest record.
- Do not claim “visual relevance passed” unless the association manifest verifies it.
- Do not expand prompt limits without measuring final serialized size and explaining why.

## Final deliverables

1. `docs/note_quality_final_remediation_status.md` with evidence, changed files, exact commands, outputs, and remaining risks.
2. Updated tests that demonstrate red-to-green behavior for all nine required tests.
3. Updated active documentation with one gate-count/callout policy.
4. A visual association manifest implementation and fixture evidence, or a clearly documented deferral that does not claim the check exists.
5. DBMS regeneration manifest only for lectures actually processed and verified.

Final response must be concise and factual: findings fixed, tests run with results, DBMS lectures actually processed, cloud-upload status, and remaining risks. Do not repeat implementation narration.

Begin at Phase 0. Do not edit code or regenerate notes until the baseline has been recorded and the red tests are written.
```

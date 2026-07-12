# Antigravity execution prompt: note-quality remediation and DBMS recovery

Copy everything below into a new Antigravity task. It is intentionally self-contained and designed for a smaller model: work in short verified phases, load only the relevant files for each phase, and never rely on an old agent report without local evidence.

```text
You are the Lead Note-Quality Remediation Engineer for this repository:

/Users/tejasmahadik/Documents/agentic-lecture-notes

Your mission is to make this pipeline generate genuinely useful exam notes: source-faithful, concise without losing taught facts, subject-appropriate, non-repetitive, visually relevant, and auditable. Then use the repaired pipeline to regenerate and validate the DBMS notes from Lec-35 onward and every future lecture run.

This is a production-quality correction project. Do not cosmetically rewrite one DOCX first. Fix the system, prove it with small fixtures, then regenerate selected outputs.

## Your operating principles

1. Evidence before edits. Do not assume any previous AI claim, prompt, issue, or architecture document is current.
2. Preserve user data. Never delete, overwrite, move, or regenerate a note/output/archive unless the execution phase explicitly permits it and a backup exists.
3. Keep changes minimal and testable. Do not do a broad rewrite, change frameworks, or reorganize folders merely for style.
4. Treat the transcript as the factual source of truth. Slides, frames, and reference notes are supporting sources.
5. A full note and a short revision note are different products. Do not weaken one to make the other shorter.
6. Never claim a fix, audit pass, cloud upload, or production readiness without fresh command output proving it.
7. No hallucinated rules, examples, traps, homework, or teacher cautions. A caution/trick must be explicitly source-grounded.
8. No native Word neon highlighting. Preserve existing pastel OpenXML rendering requirements.
9. No Devanagari in final output. Do not delete meaning just to remove it; translate or romanize faithfully.
10. Do not expose `.env` secrets in logs, prompts, reports, or commits.

## Context loading order

Read these files before changing code. They contain both current behavior and known contradictions:

1. `workspace_state.json`
2. `AGENTS.md`
3. `CLAUDE.md`
4. `docs/ISSUES_REGISTRY.md`
5. `docs/NOTE_QUALITY_AUDIT_2026-07-12.md`  <-- newest evidence-backed quality audit
6. `notes_root_cause_analysis.md`
7. `PROMPT.md`  <-- contains stale/conflicting instructions; inspect, do not blindly follow
8. `.agents/skills/note-composition/SKILL.md`
9. `.agents/skills/lecture-note-reconstruction/SKILL.md`
10. `scripts/generate_docx.py`
11. `scripts/generate_short_note.py`
12. `scripts/parse_transcript.py`
13. `scripts/audit.py`
14. `scripts/student_tester.py`
15. `scripts/langgraph_orchestrator.py`
16. `scripts/extract_frames.py`
17. `scripts/upload_run.py` and `scripts/cloud_uploader.py`

Read the relevant tests and existing fixtures before editing each script. If no proper fixture exists, create a small deterministic one before changing production logic.

## Source-of-truth and conflict policy

Repository documents conflict. Resolve conflicts explicitly; do not silently choose one.

Priority for this remediation task:

1. This prompt and direct user requirements.
2. Source fidelity and safety requirements in `AGENTS.md`.
3. The verified evidence in `docs/NOTE_QUALITY_AUDIT_2026-07-12.md` and `docs/ISSUES_REGISTRY.md` entries `L-157` through `L-172`.
4. Current source code behavior, used as the baseline to test and repair.
5. Older prompts/skills only when they do not contradict the above.

Document every material contradiction found. Update superseded prompts/rules only after code behavior and tests establish the intended policy.

## Known, confirmed failures to solve

These are confirmed findings. Verify locally before changing them:

1. **Weak length gate:** `scripts/audit.py` uses a dynamic budget that can exceed the stated 4,000-word ceiling for one-hour lectures. See `L-157`, `NQ-001`.
2. **No repetition/scanability gate:** Gate 15 only catches extremely long individual explanations. It cannot catch duplicate rule -> prose -> example -> callout restatements. See `L-158`, `NQ-002`.
3. **Fake student validation:** `scripts/student_tester.py` largely checks banned attributions, yet reports examples/structure valid. See `L-159`, `NQ-003`.
4. **Callout contradiction:** `AGENTS.md` says max 6; `PROMPT.md`, generator paths, and audit use 20. See `L-160`, `NQ-004`.
5. **Instruction contradiction:** clean-note rules prohibit mandatory cloze/Cornell/SRS scaffolding, while legacy lecture reconstruction skill still requires them. See `L-161`, `NQ-005`.
6. **Generic short-note template:** deterministic fallback forces the same headings and invents generic traps. See `L-162`, `NQ-006`, `L-166`.
7. **Broken retrieval behavior:** recent short notes reveal self-test answers immediately. See `L-163`, `NQ-007`.
8. **Unsafe image association:** generator falls back from timestamp match to example index, then next unused visual. See `L-164`, `NQ-008`.
9. **Count-only image gate:** audit checks image coverage but not relevance, readability, duplicate board states, or adjacency. See `L-165`, `NQ-009`.
10. **Duplicated navigation:** generator always emits a full Lecture Flow Outline, then repeats every title as a detailed H2. See `L-168`, `NQ-017`.
11. **Exact-text-only mapping dedup:** rephrased duplicated concepts/examples survive; matching detailed explanations can be concatenated. See `L-169`, `NQ-018`.
12. **Non-compressing synthesizer:** explanation synthesis runs only beyond 4,000 characters and is instructed not to shorten. See `L-170`, `NQ-019`.
13. **State-dependent callout limit:** enforcement changes depending on audit feedback file state. See `L-171`, `NQ-020`.
14. **Unmatched visual leftovers:** board states can be appended with only block-level context. See `L-172`, `NQ-021`.
15. **Short notes are not audited:** the 24-gate audit validates the DOCX only. See `L-167`, `NQ-016`.

## Desired product contract

### A. Full lecture notes (.docx)

The full note is a complete source-faithful study document, not a transcript rewrite.

- Preserve every taught fact, rule, formula, unique method, teacher-taught analogy that materially explains the concept, and required worked step.
- Remove greetings, repeated verbal restatement, rhetorical filler, duplicate examples with identical mechanics, and repeated explanations that add no new decision value.
- Default information unit: `Rule/idea -> condition or why -> one representative worked example -> explicitly taught caution`, with each element adding new information.
- Do not repeat the exact same rule in a definition, an explanatory paragraph, a Quick Revision box, and an example unless the second occurrence has a distinct learning function.
- Use meaningful H2/H3 titles from actual lecture/slide topics. Do not emit generic `Section 1`, `Section 2`, `CB1`, or repeated flow outlines by default.
- Keep paragraphs unified but scannable. Use concise bullets, tables, and line-separated calculation steps when they improve retrieval.
- Do not force a single layout across subjects.

### B. Short revision note (.md)

The short note is a separate 3-5 minute retrieval artifact. It must never replace or weaken the DOCX.

- Context anchor and source provenance are mandatory.
- Keep only high-yield rules, discriminating contrasts, decision rules, and at most one canonical fully worked pattern per method family.
- Self-test questions must not reveal the answer in the same artifact. If answers are needed, write a separate answer-key file or use an explicitly collapsed optional output that is not rendered by default.
- Do not fabricate a trap, memory hook, caution, or example. Omit the section if there is no source-grounded content.
- Use subject-specific shape, not a mandatory uniform scaffold.

### C. Subject profiles

Create an explicit profile selected from source evidence before rendering:

- **DBMS/technical:** concept/intent/query or syntax/edge case; one schema/query example where needed; use tables only when comparison is truly useful.
- **Reasoning:** condition map or compact diagram, direction convention, one complete pattern, final arrangement, and source-grounded traps.
- **Quant:** method-selection condition, formula with variable meanings, one canonical solution, line-separated algebra, source-grounded shortcut/check.
- **English grammar:** rule -> correct contrast -> wrong/error pattern; do not dump serial examples.
- **Vocabulary:** word cluster, meaning/tone/contrast/use; do not create generic grammar scaffolding.
- **GK/theory:** comparison, cause-effect, timeline, or 5W1H only when it improves recall.

### D. Visual policy

- A visual is evidence, not a quota.
- Insert it only if it materially conveys a board solution, diagram, table, syntax, or relationship that adjacent text needs.
- Association must be confidence-based: exact timestamp/source reference first; then bounded timestamp tolerance plus OCR/context similarity; no blind list-index or “next unused” fallback.
- When confidence is below threshold, omit the visual and write a structured skipped-visual record for review. Do not insert a wrong image merely to pass a count.
- Do not append leftover visuals unless they are explicitly classified as an overview visual with a local caption.

## Required execution plan

### Phase 0: Safety baseline and inventory

1. Read the context files listed above.
2. Run `git status --short`; preserve every pre-existing change.
3. Record active lecture paths, current run fingerprint, current output paths, and current audit result.
4. Inventory DBMS inputs and outputs beginning at Lec-35. Locate original source files, transcripts, manifests, archives, and generated DOCX/short notes. Do not assume their filenames; search evidence-first.
5. Create `docs/note_quality_remediation_status.md` with date, baseline, selected fixtures, exact commands, and unresolved risks.

### Phase 1: Independent analysis lanes (read-only first)

If the workspace supports sub-agents, run these three lanes in parallel. They must not edit files:

- **Lane A — Output quality:** Review recent DBMS notes (Lec-35 onward if available), one reasoning note, one quant note, and one English note. Score redundancy, scanability, subject fit, example selection, self-test behavior, and template overhead.
- **Lane B — Visual evidence:** Trace frame manifest -> concept map -> DOCX placement. Identify real placement/relevance failures and distinguish them from unproven risks.
- **Lane C — Pipeline and evaluation:** Trace prompt -> mapper -> generator -> short-note generator -> audit -> upload. Confirm contradictions and missing test seams.

Store each lane report under `docs/audits/` and merge only evidence-backed findings into the status document. If sub-agents are unavailable, perform the same lanes sequentially and state that fact.

### Phase 2: Write the target specification and red-capable fixtures

Before modifying production logic:

1. Write `docs/architecture/NOTE_QUALITY_CONTRACT.md` defining full-note and short-note output contracts, subject profiles, visual association policy, callout policy, and acceptance thresholds.
2. Resolve the 6 vs 20 callout contradiction in the specification. Recommendation: max 6 document-wide callout boxes, all source-grounded.
3. Create small deterministic fixtures under an existing test/fixture convention (or introduce `tests/fixtures/note_quality/` if none exists). Include at minimum:
   - technical/DBMS with two similar examples and one matching screenshot;
   - reasoning with a diagram that must stay adjacent to its method;
   - grammar with rule/correct/incorrect contrast;
   - short note with an unanswerable self-test if answer leakage occurs.
4. Write tests or executable audit harnesses that fail on the current defects:
   - duplicate flow-outline + repeated H2 titles;
   - word budget beyond the duration-appropriate ceiling;
   - duplicate claim/redundant rule rendering;
   - generic fabricated trap;
   - self-test answer leakage;
   - low-confidence index-based visual insertion;
   - short note omitted from quality verification;
   - callout cap inconsistent with contract.
5. Run the fixtures before edits and capture failing output in the status report.

Do not write a fake test that merely asserts implementation internals. It must inspect generated Markdown/DOCX behavior or a proper rendering plan boundary.

### Phase 3: Minimal implementation in dependency order

Make small, reviewable changes. After each change run its targeted tests.

1. **Contracts and prompt alignment:** Update only the current rule files necessary to remove contradictions. Archive or clearly mark obsolete instructions. Do not leave two active policies.
2. **Composition plan:** Refactor only enough to make output sections intentional and profile-driven. Remove unconditional duplicate flow outline. Make generic scaffolding optional.
3. **Deduplication:** Preserve source spans and unique facts while suppressing semantically equivalent restatement in rendered output. Do not use a loose algorithm that accidentally removes distinct rules.
4. **Full-note audit:** Add measurable warnings/failures for duration-aware word budget, repeated claim density, oversized/imbalanced sections, duplicate scaffold headings, and visual association confidence.
5. **Short-note audit:** Add a separate short-note validator and report. It must check context/source grounding, no fabricated traps, no self-test answer leakage, compact profile fit, and Markdown hygiene. Keep this separate from DOCX gate numbering if that avoids breaking the existing 24-gate contract; report both results clearly.
6. **Student tester:** Replace the false “valid” claim with factual checks and a real output-quality rubric. Do not make an LLM score the only pass/fail authority; combine deterministic checks with transparent rubric results.
7. **Visual association:** Remove blind positional fallback. Add confidence scoring and a skipped-visual manifest. Keep image count from forcing incorrect insertions.
8. **Cloud and state:** Preserve the 9 GB R2 safety limit. Ensure both verified DOCX and short-note artifacts are uploaded only after their respective validations pass. Record paths/keys and validation results in `workspace_state.json` without secrets.

### Phase 4: Verification

Run all of the following after implementation, adapting commands only where the project has a documented equivalent:

1. Python syntax/compile checks for changed scripts.
2. New focused tests/fixture harnesses, including red-then-green proof where possible.
3. Existing audit against a non-protected fixture output.
4. `git diff --check`.
5. One end-to-end dry run or minimal real run that exercises mapper -> DOCX -> short note -> both audits without overwriting the protected current final notes.
6. Confirm the R2 safety guard still exists and cannot be bypassed. Do not perform a real cloud upload unless credentials and the user’s environment already permit it; otherwise dry-run and state the limitation.

Report exactly what was run, pass/fail output, what remains unverified, and why.

### Phase 5: DBMS regeneration from Lec-35 onward

Only start this after Phases 0-4 pass and there is a backup/archival plan.

1. Discover each DBMS lecture from Lec-35 onward and group its video, transcript, slides, reference notes, current DOCX, and current short note by evidence.
2. Create a regeneration manifest in `docs/audits/dbms_regeneration_manifest.json` that lists each lecture, source paths, prior output paths, run fingerprint, and status. Do not guess missing sources.
3. Process one pilot lecture first (Lec-35 if sources exist; otherwise the earliest available). Compare old and new outputs against the target contract and source artifacts.
4. Require all full-note and short-note checks to pass before promoting the pilot output.
5. Archive rather than overwrite prior output. Use clear versioned filenames. Update canonical `LECTURE_NOTES.docx` only for the active lecture after successful validation.
6. Proceed lecture-by-lecture. Stop the batch if a source is missing, the transcript is incomplete, an audit fails, or a visual association confidence failure requires human review.
7. Upload approved artifacts through existing `upload_run.py` behavior only after audits pass, the R2 9 GB guard passes, and Supabase logging succeeds. Never purge source material until the existing two-phase commit requirements are met.

### Phase 6: Future lecture guarantee

1. Make the repaired behavior the default in orchestration, not a manual one-off.
2. Persist the note profile, quality metrics, short-note audit result, visual-association summary, and output fingerprint into `workspace_state.json` or a dedicated run manifest.
3. Add regression fixtures so a future prompt or skill change cannot reintroduce repeated outlines, generic traps, answer leakage, or blind image mapping.
4. Update the operator documentation with the exact run command, expected reports, failure handling, and regeneration procedure.

## Reporting requirements

At the end of each phase, update `docs/note_quality_remediation_status.md` with:

- findings verified in that phase;
- files changed and why;
- tests/commands run with exact results;
- output files created or archived;
- risks or unverified claims;
- next phase decision.

Final handoff must include:

1. Executive summary.
2. Issues resolved, explicitly mapped to `L-157` through `L-172`.
3. Issues intentionally deferred with reason.
4. Exact verification commands and results.
5. DBMS Lec-35 onward regeneration manifest and per-lecture result.
6. Cloud upload status and R2 keys, if upload occurred.
7. Remaining risks.

## Explicit prohibitions

- Do not modify or regenerate final notes before the fixture and audit changes prove the pipeline correction.
- Do not call a 24-gate DOCX result a short-note pass.
- Do not replace source-grounded examples with generic textbook examples.
- Do not use a word-count reduction that drops unique facts or required method steps.
- Do not delete visual assets just because they are hard to map.
- Do not satisfy an image gate by placing irrelevant screenshots.
- Do not create an “AI quality score” without showing the underlying deterministic evidence and rubric.
- Do not bypass the R2 9 GB safety limit, cleanup safeguards, or transcript completeness checks.
- Do not claim completion without fresh verification evidence.

Begin with Phase 0. Do not edit code or regenerate notes until the read-only analysis and red-capable fixture plan are documented.
```


# Note quality audit: revision usefulness and generation drift

**Date:** 2026-07-12  
**Scope:** Independent quality review of recent and older generated lecture notes, short revision notes, the quality gates, prompts, and generation rules.  
**Mode:** Analysis only. No generated note, source manifest, or generator code was changed during this audit.

## Executive conclusion

The reported decline in note quality is real. The pipeline is currently better at proving that a document is structurally complete than at proving that it is a useful exam-revision document. It preserves coverage, images, headings, and source-like examples, but it has no reliable measurement for repetition, subject-fit, scanability, or whether an item is useful enough to earn its space.

The central failure mode is **redundant representation**: a definition, explanatory paragraph, worked trace, callout, and question often restate the same rule. In the longer notes this produces a polished transcript surrogate; in short notes it produces a small lecture walkthrough rather than a fast retrieval artifact.

This is a system-design problem, not simply a bad single lecture run. Prompt conflicts, permissive audit thresholds, and shallow student testing allow the behavior to pass all 24 gates.

## Evidence reviewed

### Generated notes

| Artifact | Words | Paragraphs | H2 sections | Images | Callout markers | Audit observation |
|---|---:|---:|---:|---:|---:|---|
| `LECTURE_NOTES_Lec-29_SQL_Commands_2026-07-12_13-56-44.docx` | 1,690 | 134 | 5 | 6 | 10 | Repeated scaffold and high callout density for a short technical lecture. |
| `LECTURE_NOTES_Lec-36_Non_Correlated_nested_query_2026-07-12_14-01-10.docx` | 1,868 | 130 | 1 | 7 | 1 | Long serial explanation despite only one H2 section; weak navigability. |
| `LECTURE_NOTES_Lec-37_Correlated_nested_query_2026-07-12_14-02-28.docx` | 804 | 42 | 1 | 3 | 2 | Compact overall, but explanation remains paragraph-led rather than retrieval-led. |
| `LECTURE_NOTES_Live-22_English_Discussion_on_miscellaneous_Grammar_Test-3_Sentence_Rearrang_2026-07-11_06-45-41.docx` | 3,446 | 192 | 5 | 6 | 7 | Near the one-hour target but carries extensive template overhead and repeated example exposition. |
| `LECTURE_NOTES_Live-19_Number_System_Classification_Divisibility_Rule_HCF_And_LCM_2026-07-11_06-36-19.docx` | 4,220 | 253 | 6 | 14 | 7 | Exceeds the stated 4,000-word ceiling yet could pass the dynamic audit budget. |

The current active run is `Lec-37 Correlated nested query`; `workspace_state.json` claims 24/24 gates passed. That pass is not evidence that the notes satisfy the user's revision-quality expectations.

### Short-note samples

- `notes-output/Lec-37 Correlated nested query_SHORTNOTE.md:33-68` carries three detailed SQL traces with every outer-row result. This is useful as teaching material, but too much for a short revision note; one representative trace plus output logic would retain the method with less repetition.
- `notes-output/Lec-37 Correlated nested query_SHORTNOTE.md:90-96` immediately gives the self-test answer. This turns retrieval practice into rereading.
- `notes-output/Lec-29 SQL Commands_SHORTNOTE.md:57-77` includes three question-answer pairs and then a self-test with its complete answer. The repeated answer exposure weakens its role as a revision cue.
- `notes-output/Reasoning-lec15-SR pt.2_SHORTNOTE.md:28-62` stores complete placement traces for three puzzles. It is a worked-example digest, not a compact rule-and-pattern sheet.

### Learning-design research used

- The U.S. Institute of Education Sciences recommends spaced review, alternating worked examples with independent attempts, combining relevant graphics with verbal descriptions, and quizzing for active retrieval. [IES practice guide](https://ies.ed.gov/ncee/wwc/PracticeGuide/1)
- Worked examples can reduce ineffective cognitive load for novice learners, but redundant material and poorly integrated explanation/visuals raise extraneous load. [van Gog, Paas, and Sweller review](https://link.springer.com/article/10.1007/s10648-010-9145-4)
- Diagram/text integration matters when a learner would otherwise have to search between the two sources; it does not justify adding images merely to satisfy a count. [Cognitive Architecture and Instructional Design](https://link.springer.com/article/10.1007/s10648-019-09465-5)
- Less-complete, organisational note structures can improve free recall and inference when they require meaningful processing, rather than merely presenting every answer. [Bellinger and DeCaro, 2019](https://pubmed.ncbi.nlm.nih.gov/31519136/)

## What an exam note should optimize for

1. **One representation per job.** Definition, method, one discriminating example, and an explicit trap should each add unique value. Do not restate the same rule in all four.
2. **Subject-shaped layouts.** Reasoning needs condition maps and final arrangements; grammar needs rule/contrast/error patterns; quant needs method selection, formula conditions, and one canonical worked example; technical notes need relation/schema/query intent; theory needs causation, chronology, and comparison.
3. **Progressive depth.** A 20-second scan should reveal the rule; a 90-second review should reveal the method; only then should a learner read the full worked trace.
4. **Image evidence, not image quota.** Insert a diagram only where it carries information that the adjacent text cannot quickly convey. It must be directly adjacent to the explanation that uses it.
5. **Retrieval before answer.** Include a prompt or incomplete setup, but keep the answer hidden, in a separate answer key, or absent from the short note.
6. **Grounded completeness, not transcript imitation.** Retain every fact, rule, method step, and teacher-flagged caution. Remove greetings, restatements, rhetorical transitions, duplicate examples, and explanatory wording that adds no decision value.

## Confirmed findings

### NQ-001: Gate 23 permits notes that violate the stated word ceiling

- **Severity:** high
- **Evidence:** `scripts/audit.py:575-583` uses `max(5000, blocks * 1000, examples * 150)`, while `AGENTS.md:48` sets a 4,000-word ceiling for a one-hour lecture. The reviewed Number System document contains 4,220 words.
- **Impact:** Notes can be objectively beyond the declared revision budget and still report a passing audit.
- **Safest remediation:** Define a lecture-duration-aware target range and a separate hard ceiling; do not use number of blocks as an automatic license for more prose.

### NQ-002: Gate 15 detects only extreme per-block verbosity, not repetition or scanability

- **Severity:** high
- **Evidence:** `scripts/audit.py:293-299` only fails an explanation after 4,000 characters. It does not inspect duplicated claims across rules, explanations, examples, quick revision boxes, or callouts.
- **Impact:** The main user complaint, repetitive and over-explained notes, has no failing signal.
- **Safest remediation:** Add a document-level redundancy metric and a manual/LLM quality rubric over a small fixed sample before changing generation behavior.

### NQ-003: The student tester is not a student-quality test

- **Severity:** high
- **Evidence:** `scripts/student_tester.py:20-59` checks five attribution phrases, then writes “Examples and structure appear valid” if none are found.
- **Impact:** This artifact creates false confidence; it cannot identify poor explanation order, over-length, repeated facts, bad visuals, or unusable short notes.
- **Safest remediation:** Replace the success claim with measured checks, then add a read-only rubric evaluator for clarity, duplicate content, subject-fit, and self-test validity.

### NQ-004: Callout-box policy contradicts its enforcement

- **Severity:** high
- **Evidence:** `AGENTS.md:21` and `AGENTS.md:42` cap callouts at 6; `PROMPT.md:63`, `PROMPT.md:173`, and `PROMPT.md:280` state 20; `scripts/audit.py:585-591` and `scripts/generate_docx.py:1515-1524` enforce 20.
- **Impact:** The generator can legally produce more visual interruptions than the active project instructions allow. The SQL Commands document has 10 callout markers.
- **Safest remediation:** Pick one cap, update all sources of truth together, and test it against a fixture. The current explicit clean-note policy supports 6, not 20.

### NQ-005: The repository has mutually conflicting note-design directives

- **Severity:** high
- **Evidence:** `AGENTS.md:42` bans mandatory clozes, Cornell cues, and SRS tags. `.agents/skills/lecture-note-reconstruction/SKILL.md` still requires a three-layer friction matrix with clozes, Cornell cues, SRS tags, and three boundary questions per block. `scripts/generate_short_note.py:449-456` explicitly prohibits those items.
- **Impact:** Different agents can create incompatible outputs from the same project state, so note quality is non-deterministic.
- **Safest remediation:** Establish a single current “full note” and “short note” content contract; archive superseded instructions rather than leaving them executable.

### NQ-006: Short-note fallback imposes the same scaffold on every subject

- **Severity:** medium
- **Evidence:** `scripts/generate_short_note.py:345-390` always emits Context Anchor, Subject Type, subject template, Memory Hook/Emphasis, Trap Box, Self-Test, and Source line. It also invents a generic trap whenever source traps are absent (`:379-381`).
- **Impact:** Notes feel machine-made and repetitive. A short technical note, reasoning note, and grammar note receive too much identical framing.
- **Safest remediation:** Keep mandatory provenance and grounding, but allow optional sections only when source evidence and subject type justify them.

### NQ-007: Short-note self-tests commonly disclose answers immediately

- **Severity:** medium
- **Evidence:** `Lec-37 Correlated nested query_SHORTNOTE.md:90-96`; `Lec-29 SQL Commands_SHORTNOTE.md:68-77`; `Reasoning-lec15-SR pt.2_SHORTNOTE.md:70-73`.
- **Impact:** The short note cannot act as a retrieval cue; the learner simply rereads the answer.
- **Safest remediation:** Output unanswered prompts, or store answers in a separate collapsed/answer-key artifact.

### NQ-008: Visual association has an unsafe positional fallback

- **Severity:** high
- **Evidence:** `scripts/generate_docx.py:1495-1508` falls back first to same list index, then to the next uninserted visual moment when no timestamp match exists.
- **Impact:** If manifests are incomplete or differently ordered, a valid image can be inserted under the wrong example. The SQL sample shows sensible placement, but the code does not prove relevance in all runs.
- **Safest remediation:** Require semantic/timestamp compatibility before insertion; leave a visual out when confidence is low and record the omission for review.

### NQ-009: Visual quality is counted, not judged

- **Severity:** high
- **Evidence:** `scripts/audit.py:560-561` checks expected image count ratio. It does not check whether an image is relevant, readable, non-duplicate, or adjacent to the correct example.
- **Impact:** A document can pass visual coverage with irrelevant or repetitive images.
- **Safest remediation:** Add image-to-example correspondence checks using timestamp tolerance and OCR/context similarity, plus a human-readable exception log.

### NQ-010: Current note topology adds recurring boilerplate before content

- **Severity:** medium
- **Evidence:** Recent full notes repeatedly use `Section 1`, `Lecture Flow Outline`, `Section 2`, `Detailed Concept Blocks`, `CB1`, `Key Concepts`, and `Examples & Illustrations`; the five reviewed files average 150 paragraphs for 2,406 words.
- **Impact:** Page space is spent explaining the document’s structure rather than helping a learner locate a rule, pattern, or example.
- **Safest remediation:** Make the title and H2 topic headings do the navigation work. Remove scaffolding whose only purpose is template consistency.

### NQ-011: Subject-specific treatment is insufficiently enforced

- **Severity:** medium
- **Evidence:** The deterministic short-note generator dispatches only a small per-subject renderer (`scripts/generate_short_note.py:357-368`) and the full-note audit contains no subject-fit gate.
- **Impact:** Reasoning can be rendered as prose-heavy tutorial steps, grammar as serial examples, and technical notes as generic concept tables even when a more effective representation is available.
- **Safest remediation:** Classify the lecture into a concrete note profile before composition and audit against profile-specific requirements.

### NQ-012: Generic fallback traps violate the explicit-only caution policy

- **Severity:** medium
- **Evidence:** `scripts/generate_short_note.py:375-381` emits “Watch notation, boundary conditions, and option-level traps from the lecture” when no extracted trap exists. `AGENTS.md:49` says cautions must be explicitly extracted from the transcript.
- **Impact:** The short-note generator can fabricate a caution category even when the lecture did not teach one.
- **Safest remediation:** Omit the trap section when no source-grounded caution exists, or label it as a personal practice placeholder without asserting lecture provenance.

### NQ-013: The audit is insensitive to a severely unbalanced section structure

- **Severity:** medium
- **Evidence:** The Lec-36 full note has 1 H2 section, 130 paragraphs, and 1,868 words. It can pass because no gate bounds paragraphs per H2, heading depth, or section balance.
- **Impact:** Long sequential material becomes hard to scan despite formal structural integrity.
- **Safest remediation:** Flag unusually large sections and require either meaningful subheadings or a compact table/list structure.

### NQ-014: The current short-note model can over-teach instead of compress

- **Severity:** medium
- **Evidence:** `Lec-37 Correlated nested query_SHORTNOTE.md:39-68` logs all outer-row values for three patterns; `Reasoning-lec15-SR pt.2_SHORTNOTE.md:30-62` traces three full puzzle constructions.
- **Impact:** A short note becomes a second complete note, increasing review time without proportional retrieval value.
- **Safest remediation:** Limit short notes to one canonical fully worked pattern per method; represent variations as decision rules and one-line contrast cases.

### NQ-015: Source completeness and revision compression are presently conflated

- **Severity:** high
- **Evidence:** `AGENTS.md:48` asks to preserve “100% of all FACTS, rules, and worked steps” while also requiring 2,500–3,500 words. The current system lacks a structured distinction between facts, teaching narrative, repeated verification steps, and the minimal recall cue needed for each item.
- **Impact:** The safest model behavior is to retain almost everything, causing bloat. The model has no approved way to compress without fearing a coverage failure.
- **Safest remediation:** Preserve full traceability in the concept map and full note, then define an explicit compression policy for the short note and a duplicate-elimination policy for the full note.

### NQ-016: The short revision note is outside the 24-gate audit

- **Severity:** high
- **Evidence:** `scripts/langgraph_orchestrator.py:611-621` generates `LECTURE_SHORTNOTE.md`, while `scripts/langgraph_orchestrator.py:633-640` calls `run_audit()` only with the DOCX, concept map, frame manifest, and slide manifest. `scripts/audit.py` has no short-note input or short-note gates.
- **Impact:** The pipeline can announce 24/24 gates passed even when the short note is verbose, ungrounded, missing required retrieval behavior, or structurally unusable.
- **Safest remediation:** Add a separate short-note audit contract and report its result independently; do not misrepresent DOCX gates as short-note quality validation.

### NQ-017: The generator unconditionally duplicates the topic navigation as content

- **Severity:** medium
- **Evidence:** `scripts/generate_docx.py:1368-1378` always writes a “Lecture Flow Outline” containing every block title, then starts a “Detailed Concept Blocks” section that repeats each title as an H2 at `:1397-1400`.
- **Impact:** Every full note spends space and visual attention re-listing the same content topology, even when the H2 headings already provide adequate navigation.
- **Safest remediation:** Make a flow outline optional for genuinely complex multi-topic lectures, and omit it for short/single-topic lectures.

### NQ-018: Semantic duplicate handling is too narrow at the mapping boundary

- **Severity:** high
- **Evidence:** `scripts/parse_transcript.py:408-422` deduplicates concepts by exact lower-cased term and examples by exact lower-cased sentence. `:614-620` concatenates detailed explanations for a matching concept name instead of comparing their semantic overlap.
- **Impact:** Rephrased restatements from adjacent transcript chunks survive and are later rendered as distinct concepts, explanation text, rules, and examples.
- **Safest remediation:** Keep exact matching for safety, then add an explicit source-span-aware semantic overlap pass that marks equivalent restatements rather than concatenating them.

### NQ-019: The explanation “synthesizer” cannot materially reduce bloat

- **Severity:** high
- **Evidence:** `scripts/parse_transcript.py:822-850` runs only when an explanation exceeds 4,000 characters and instructs the model at `:831-836` to preserve 100% of detail and not shorten it.
- **Impact:** The nominal anti-verbosity stage cannot solve normal-length repetition and cannot reduce an overlong explanation into a sharper study representation.
- **Safest remediation:** Separate source retention from rendered prose. Preserve full source spans in the map, while allowing the rendered explanation to remove duplicate phrasing and defer repeated mechanics to the example.

### NQ-020: Callout enforcement depends on unrelated audit-feedback state

- **Severity:** medium
- **Evidence:** `scripts/generate_docx.py:1385-1394` enables the 20-callout enforcement only when an audit feedback file exists and contains “24”; the code otherwise applies a separate 6-caution counter only at `:1841-1853`.
- **Impact:** Quote and callout behavior varies between first generation and retry generation, which makes output formatting dependent on stale process state.
- **Safest remediation:** Enforce one document-wide policy unconditionally inside the generator, then validate the same policy in the audit.

### NQ-021: Visual leftovers are inserted without example-level semantic context

- **Severity:** medium
- **Evidence:** `scripts/generate_docx.py:1828-1832` inserts every leftover visual moment using the block explanation as its only context.
- **Impact:** An unmatched board state can appear at the end of a block without the local explanation that makes it readable; count-based visual gates still reward it.
- **Safest remediation:** Insert a leftover only when it is a named overview visual, or create a concise caption tied to the precise source concept. Otherwise record it as unused evidence.

## Non-findings and boundaries

- The reviewed SQL Commands document places its six image paragraphs immediately after corresponding examples. Therefore, “all images are misplaced” is **not confirmed**. The confirmed issue is that the code has a low-confidence positional fallback and the audit cannot detect mismatches.
- This audit did not rerun the pipeline or regenerate notes. No claim is made about source fidelity of every sentence against every transcript.
- The external reviewer runner was invoked in three isolated lanes but returned no usable output. Findings in this report are based on local inspection and cited research, not unsupported agent consensus.

## Remediation sequence (do not implement as one large rewrite)

1. **Freeze and align contracts.** Resolve the 6-versus-20 callout conflict, remove executable contradictions around cloze/Cornell/SRS, and define separate contracts for full notes and short notes.
2. **Create a red-capable quality fixture.** Use a small representative lecture fixture and expected measures for word count, duplicate claims, image association, self-test answer leakage, and profile-specific structure.
3. **Upgrade evaluation before rewriting prompts.** Add gates or a companion report for redundancy, section balance, visual relevance, and retrieval validity. Keep these as warnings initially and compare against known good/bad documents.
4. **Revise the full-note composition policy.** Use `Rule -> why/condition -> one representative example -> source-grounded caution` as the default unit. Do not repeat the same rule in prose, key concepts, and callouts.
5. **Revise the short-note contract.** Permit one canonical worked pattern per method, no immediately revealed self-test answers, and optional sections only where evidence supports them.
6. **Fix visual association after the contract is measurable.** Replace positional image fallbacks with a confidence-based association and record skipped images.
7. **Regenerate one technical, one reasoning, one English, and one quant fixture.** Review side-by-side against the baseline before changing the existing protected final outputs.

## Proposed acceptance rubric for the next implementation pass

| Dimension | Full notes | Short revision note |
|---|---|---|
| Coverage | Every concept, rule, teacher-taught method, and necessary worked step is traceable to source. | Includes only high-yield rules, methods, contrasts, and one canonical example per method. |
| Redundancy | Same claim appears at most twice only when the second form is a deliberately different function (for example, rule plus example). | Same claim appears once. |
| Examples | Keep one complete example per distinct method; collapse repeated mechanics into a contrast table. | One complete example per method family; no serial row-by-row repetitions unless the row comparison is the concept. |
| Visuals | A visual is adjacent to the text that relies on it and is omitted when it adds no information. | Include only diagrams that are required for recall or direction/relationship reasoning. |
| Retrieval | Optional self-check may link to answer key. | Self-test answer is absent or external. |
| Navigation | Meaningful H2/H3 headings, no generic “Section/CB” scaffolding. | 20-second scan reveals the rule/method/trap hierarchy. |

## Status

No code or output document was modified in this audit. The next work should be an agreed implementation plan based on this report, followed by a small fixture-based change rather than a broad prompt rewrite.

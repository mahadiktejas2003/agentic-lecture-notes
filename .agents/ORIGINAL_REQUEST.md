# Original User Request

## 2026-06-22T10:00:51Z

# Teamwork Project Prompt

Working directory: /Users/tejasmahadik/Documents/agentic-lecture-notes
Integrity mode: development

The goal of this project is to construct a comprehensive, permanent system prompt for all AI agents in the lecture-note reconstruction pipeline (Orchestrator, Transcript-Mapping, Frame-Extraction, Slide-Parsing, and Note-Composition). This prompt will detail all rules, constraints, quality gates, and styling protocols to ensure zero-defect note generation and pipeline execution.

The final prompt should be written to `.agents/rules/agent_prompt.md`.

## Requirements

### R1. Unified Context and Persona Definitions
Draft clear role descriptions, constraints, and tasks for the Orchestrator, transcript-mapping, frame-extraction, slide-parsing, and note-composition agents, aligning them with the codebase's existing script behaviors and schemas.

### R2. Strict Source Fidelity & Formatting Protocol Integration
Embed the 13+ source fidelity rules, the attribution ban, Hinglish/bilingual translation exceptions, Cornell layout requirements, math formatting/LaTeX conventions, and Cloze deletion structures directly into the prompt instructions.

### R3. Quality Gate Alignment
Explicitly define all 19 mechanical quality gates in the prompt instructions to ensure that implementing agents perform pre-delivery self-audits that mimic the behavior of `scripts/audit.py`.

## Acceptance Criteria

### Prompt Coverage & Accuracy
- [ ] The generated system prompt contains exhaustive sections for Source Fidelity, Note Layout and Content Constraints, Mathematical Explanations, Topper-Grade Tone, and Productive Friction.
- [ ] The system prompt includes explicit guidelines for each of the sub-agent roles: Orchestrator, frame-extraction, transcript-mapping, and slide-parsing.
- [ ] Every one of the 19 quality gates is documented with its exact mechanical pass/fail criteria.
- [ ] The file is successfully written to `.agents/rules/agent_prompt.md` and contains no placeholder blocks (e.g., "TBD", "TODO").

## 2026-06-24T11:10:49Z

Perform a one-time exhaustive multi-round analysis on the current generated notes (Live-13) and previous notes to identify the root cause of the repetitive Hindi/Hinglish, garbage content, and duplicate screenshot issues across the entire agentic pipeline.

Working directory: /Users/tejasmahadik/Documents/agentic-lecture-notes
Integrity mode: development

## Requirements

### R1. Deep Root-Cause Analysis
The team must perform an exhaustive analysis of the generated notes (Live-13 and previous) against the original transcripts and the user's historical complaints. Identify the exact architectural root causes in the pipeline (e.g., LLM prompts, deduplication logic, extraction thresholds).

### R2. Codebase Investigation
The team must review `scripts/parse_transcript.py`, `scripts/extract_frames.py`, `scripts/generate_docx.py`, and other relevant files to trace exactly *why* the pipeline injects garbage conversational filler, uses unneeded Hinglish, and duplicates screenshots.

### R3. Comprehensive Analysis Report
The team must output a comprehensive, structured report that explains the root causes across any lecture topic, and provides concrete, permanent architectural solutions to guarantee these mistakes never happen again.

## Acceptance Criteria

### Execution & Verification
- [ ] A final report artifact `notes_root_cause_analysis.md` is created in the working directory.
- [ ] The report contains specific code citations from the `scripts/` directory proving where the flawed logic exists.
- [ ] The report explains why the previous architecture failed across multiple lectures, not just a single instance.
- [ ] The analysis proves why the recommended solutions will prevent these specific issues globally for any future lecture.

## 2026-06-26T07:43:03Z

Structured multi-agent project to analyze, plan, study, and execute a complete overhaul of the lecture-note reconstruction pipeline (code, prompts, agents, rules, skills, and configuration) to permanently enforce concept block consolidation and soft pastel highlighting.

Working directory: /Users/tejasmahadik/Documents/agentic-lecture-notes
Integrity mode: development

## Requirements

### R1. Deep Analysis Phase
Spawn researcher agents to study all scripts (scripts/generate_docx.py, scripts/parse_transcript.py, etc.), rule documents (AGENTS.md, .agents/rules/), skills (pdf-ocr-extraction, lecture-note-reconstruction), and state/context files. Identify all places where standard neon highlights, old block mappings, or contradictions exist.

### R2. Planning & Study Phase
Generate a detailed planning document (reconstruction_improvement_plan.md) outlining all proposed file modifications. Re-analyze and review the plan across agent roles before execution to ensure no side effects on the orchestrator graph.

### R3. Style & Highlights Execution
Modify the codebase to permanently ban standard neon yellow and green highlights. Enforce OpenXML run shading for soft pastels (blue #E1F5FE, red #FEE2E2, yellow #FFF2CC, green #E8F8F5, purple #F3E8FF, orange #FFEDD5, gray #F1F5F9) in scripts/generate_docx.py, and map all double-equals ==text== tags to soft pastel blue.

### R4. Concept Block Consolidation & Slide Alignment
Update transcript parsing prompts in scripts/parse_transcript.py to prevent arbitrary AI-generated categories. Enforce 1-to-1 alignment with slide titles and actual lecture topic headings.

### R5. System Rules, Skills, and Prompts Alignment
Align all system prompt files (AGENTS.md, .agents/rules/note-style.md, and .agents/rules/agent_prompt.md) and skill files to make them fully consistent, removing any obsolete rules or TODO placeholders.

## Acceptance Criteria

### Structured Hand-Off and Analysis
- [ ] Researcher agents output a comprehensive audit report of files to be changed.
- [ ] A plan reconstruction_improvement_plan.md is written and reviewed by the team before modifications begin.

### Soft Pastel Highlights & Shading
- [ ] No scripts apply standard neon yellow/green highlighting. All highlight tags map to OpenXML run-level shading values.
- [ ] Doubts box background shading is set to #F0F4F8 across all document-generating scripts.

### Strict Concept Block Mapping
- [ ] Prompts in scripts/parse_transcript.py contain strict rules against custom concept block titles and enforce alignment with actual topics.

### Prompt & Rules Consistency
- [ ] All references in AGENTS.md, note-style.md, and agent_prompt.md are aligned with the new logic rules and pastel color themes.
- [ ] No "TODO" or "TBD" placeholders exist in .agents/rules/agent_prompt.md.

## 2026-06-27T03:32:05Z

This project overhauls and generalizes the lecture note reconstruction pipeline across the codebase to permanently guarantee 100% detail retention from verbal transcripts, correct multi-source slide/reference alignment, clean mathematical Unicode layout, and beautiful soft pastel highlights.

Working directory: /Users/tejasmahadik/Documents/agentic-lecture-notes
Integrity mode: development

## Requirements

### R1. Project-Wide 100% Transcript & Video Detail Retention
- Ensure the chunk parsing prompts in `scripts/parse_transcript.py` are robustly engineered to extract every spoken example, analogical illustration, warning, and student doubt from the transcript.
- Enforce that the pipeline never condenses, summarizes, or skips verbal content for the sake of brevity.

### R2. Precise Multi-Source Ingestion & Alignment
- Implement logic to fully merge slide headings, slide OCR content, video screenshots, and student reference notes (`lecture-input/REFERENCE_NOTES.pdf`) chronologically into the concept block map without any loss.
- Ensure screenshots are placed directly under their corresponding example/explanation block using a 1-to-1 index matching.

### R3. Unicode Math & Step-by-Step Layout Conversion
- Translate LaTeX formulas (like `^n\text{P}_r`, fractions, equations) to clean Unicode representations (`ⁿPᵣ`, `n! / (n-r)!`).
- Ensure multi-step math calculations are split into separate lines/paragraphs in the generated DOCX.

### R4. Premium Styling and Highlight Guardrails
- Enforce run-level background shading for soft pastel highlights (banning standard neon yellow/green) and specific paragraph shading for revision and student note boxes (`#F0F4F8`).

## Acceptance Criteria

### Verification & Quality Gates
- [ ] No compiler errors in python scripts: `venv/bin/python -m py_compile scripts/*.py` passes.
- [ ] Pipeline runs successfully: `venv/bin/python scripts/langgraph_orchestrator.py` completes.
- [ ] The 22-gate audit script reports PASS on all gates: `venv/bin/python scripts/audit.py --docx notes-output/LECTURE_NOTES.docx`.
- [ ] Multi-step calculations are split into distinct paragraphs/lines.
- [ ] All LaTeX formulas are converted to clean Unicode equivalents (e.g. `ⁿPᵣ`, `ⁿCᵣ`).

## 2026-06-29T07:00:05Z

Perform an exhaustive, system-wide analysis of the lecture-note reconstruction pipeline (including all skills, agents, prompts, and Python scripts) to identify and permanently fix the root causes of inconsistent, incomplete, or surface-level note generation.

Working directory: /Users/tejasmahadik/Documents/agentic-lecture-notes

## Requirements

### R1. Deep Pipeline Audit
The team must systematically review `scripts/parse_transcript.py`, `scripts/generate_docx.py`, the `lecture-note-reconstruction` skill, and all related LLM prompts to identify why the AI fails to natively extract deep, nuanced explanations (like real-world analogies, traps/tricks, and complex mathematical problem-solving steps) without relying on the user's manual reference notes.

### R2. Output Quality Remediation
The team must identify the exact architectural bottlenecks (e.g., rigid JSON schemas, overly strict prompt constraints, token truncation, or poor chunk overlapping) that cause these omissions, and implement a concrete, permanent codebase fix that guarantees 100% detail retention natively from the transcript.

## Acceptance Criteria

### Verification
- [ ] A comprehensive `system_audit_report.md` is generated detailing exactly which lines of code or prompt instructions were causing the omissions.
- [ ] The core extraction scripts (`parse_transcript.py`, etc.) are actively modified by the team to permanently solve the identified bottlenecks.
- [ ] The modifications strictly adhere to the `AGENTS.md` 100% Detail Retention (Zero Summarization Policy) and Friction-Optimized Note Matrix requirements.


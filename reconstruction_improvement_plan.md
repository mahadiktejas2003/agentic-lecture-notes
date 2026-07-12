# Reconstruction Improvement Plan

## Objectives
Overhaul the lecture-note reconstruction pipeline (code, prompts, rules, skills, and configuration) to permanently enforce:
1. **Concept Block Consolidation**: Prevent arbitrary AI-generated categories and merge duplicate/overlapping concept blocks.
2. **Soft Pastel Highlighting & Callout Shading**: Eliminate all neon yellow/green references in favor of run-level OpenXML shading for soft pastels (blue #E1F5FE, red #FEE2E2, yellow #FFF2CC, green #E8F8F5, purple #F3E8FF, orange #FFEDD5, gray #F1F5F9). Set doubts box background to `#F0F4F8`.
3. **Programmatic Audit Verification**: Add Gate 22 to `scripts/audit.py` to enforce styling, highlight colors, and box shading.
4. **Documentation Alignment**: Synchronize the quality gate count to 22 and resolve all color/shading mismatches across AGENTS.md, note-style.md, agent_prompt.md, and pipeline skills.

---

## Proposed File Modifications

### 1. Codebase Style & Highlights (Milestone 3)
* **`scripts/generate_docx.py`**:
  - Verify that the custom color map maps `YELLOW` and `GREEN` to pastels (`FFF2CC` and `E8F8F5`).
  - Verify that double-equals (`==text==`) is mapped to `<highlight color="BLUE">` (pastel blue `#E1F5FE`).
  - Verify that student note / doubts callout boxes are shaded using `#F0F4F8` (Ice-Blue) across all generator pathways (lines 1007, 1209, 1280).

### 2. Concept Block Consolidation & Slide Alignment (Milestone 4)
* **`scripts/parse_transcript.py`**:
  - Implement a `consolidate_blocks(blocks)` function to merge blocks with identical or highly similar titles (case-insensitive) across overlapping chunks.
  - Call `consolidate_blocks` right before the reference notes injection pass (line 347).
  - Update the prompt in `process_chunk()` (line 158) to restrict the LLM to slide titles/actual headings and forbid custom/arbitrary AI categories.

### 3. Rules & Prompts Alignment (Milestone 5)
* **`scripts/audit.py`**:
  - Increase the gate audit count from 19 to 22.
  - Implement **Gate 22: Styling and Highlighting Conformity** checking for:
    - Zero native Word highlight tags (ban standard neon colors).
    - Run shading fill values belonging to the approved pastel set: `{'FFF2CC', 'E8F8F5', 'E1F5FE', 'F1F5F9', 'FEE2E2', 'FFEDD5', 'F3E8FF'}`.
    - Quick Revision box shading must be exactly `#D6EAF8`.
    - Doubts / Student Notes box shading must be exactly `#F0F4F8`.
* **`AGENTS.md`** (Root):
  - Clarify that highlighting tags are rendered as soft pastels via run shading.
  - Update quality gate counts from 19 to 22 and document Gates 20, 21, and 22.
* **`.agents/rules/note-style.md`**:
  - Enforce that highlighting tags map to soft pastels.
  - Ensure no TODOs/TBDs exist.
* **`.agents/rules/agent_prompt.md`**:
  - Resolve the doubts box background conflict (standardize to `#F0F4F8` premium soft Ice-Blue).
  - Update gate count references and document Gates 20, 21, and 22.
  - Remove all TODO and TBD placeholders.
* **Skill Files** (`pdf-ocr-extraction`, `lecture-note-reconstruction`, `note-composition`):
  - Update highlighting details, doubts box background to `#F0F4F8`, and audit gate count references.

---

## Verification & Acceptance Criteria
* Programmatic audit: `python3 scripts/audit.py` runs successfully on generated documents with all 22 gates reporting PASS.
* Clean compilation check: No syntax/compile errors inside any modified python scripts.

# Original User Request

## Request — 2026-07-08T07:51:22+05:30

Fix rendering issues in `generate_docx.py` and `parse_transcript.py` related to OneNote copy-paste/dark mode compatibility, broken LaTeX parsing, and excessively long paragraphs, then regenerate and verify the notes.

Working directory: /Users/tejasmahadik/Documents/agentic-lecture-notes  
Integrity mode: development  

## Requirements

### R1. Dark Mode & OneNote Copy-Paste legibility
1. **Explicit Text Color on Light Shading**: Ensure that all text within shaded paragraphs or runs (such as `[⚡ Quick Rev]` boxes, `💡 Student Note / Doubt` boxes, table alternating rows, and centered formulas) has its run font color explicitly forced to black (`RGBColor(0, 0, 0)`) or a dark color. This prevents OneNote dark mode from auto-inverting the text to white on a light background.
2. **Formula Shading Text Color**: Explicitly force text color to black in `add_shaded_formula` to fix invisibility in dark mode.

### R2. LaTeX & Mathematical Symbols Parsing
1. **Subscript Adjacent Text Fix**: Add a regex conversion in `add_rich_runs` to handle variable-adjacent LaTeX text blocks (like `d\text{min}` or `d_\text{min}`) and correctly translate them to subscript formatting `\1<sub>\2</sub>`.
2. **Robust Mathematical Operators**: Ensure raw operators (like `\min`, `\pm`, `\times`) and unbraced subscripts are correctly handled without breaking.

### R3. Paragraph Length Control
1. **Paragraph Splitting**: In `add_formatted_explanation_paragraphs` in `generate_docx.py`, split regular paragraph lines that exceed 350-400 characters into smaller paragraphs of at most 2-3 sentences.
2. **Abbreviation Safe Splitting**: Use a regex split like `(?<!\bi\.e)(?<!\be\.g)(?<!\bvs)(?<!\bapprox)(?<!\bfig)(?<!\bno)(?<=[.!?])\s+(?=[A-Z"“0-9])` to avoid split-errors on common abbreviations.

### R4. Note Regeneration & Verification
1. **Regenerate Recent CN Notes**: Compile and regenerate all recent CN notes:
   - `Lec-6 Physical layer, Analog & Digital Signal`
   - `Lec-8 Modulation Demodulation`
   - `Lec-9 Digital to Analog conversion`
   - `Lec-12 Types of Multiplexing FDM TDM WDM`
   - `Lec-14 Error Control in Data Link Layer`
2. **Verification Suite**: Validate all generated notes using the 22-gate audit script (`audit.py`) and ensure they all pass.

## Acceptance Criteria

### Formatting & Rendering
- [ ] No shaded runs or paragraphs contain default "Auto" text color (to prevent OneNote auto-inverting text to white).
- [ ] Subscript text like `d\text{min}` renders correctly as a subscript `d` with `min` subscripted.
- [ ] Explanations have paragraph splits at logical sentence boundaries, resulting in no single paragraph block exceeding 400 characters or 3 sentences.
- [ ] All 22-gate audit tests pass successfully on all 5 regenerated CN notes.

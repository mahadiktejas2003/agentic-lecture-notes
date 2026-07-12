# Synthesis of Codebase Exploration

## Consensus
All three codebase explorers agree on the exact locations and strategies for implementing the required fixes:
1. **R1 (OneNote/Dark Mode Compatibility)**:
   - Shaded boxes (`[⚡ Quick Rev]` in `add_revision_box`, student notes in `add_cornell_block`, alternating table rows in `add_styled_table`) and formulas in `add_shaded_formula` must explicitly force text color to black (`RGBColor(0, 0, 0)`).
   - In `add_revision_box`, `add_cornell_block`, and `add_styled_table`, the loop that forces text color to black should only overwrite the color if the run does not already have a color set (i.e. `run.font.color.rgb is None`). This protects custom inline tags like clozes (blue) or highlights.
   - `add_shaded_formula` should be refactored to use `add_rich_runs` instead of a plain `p.add_run` so that mathematical subscripts within formulas are correctly formatted.

2. **R2 (LaTeX and Mathematical Symbol Parsing)**:
   - A pre-processing regex pattern in `add_rich_runs` must run before general `\text{}` stripping to handle adjacent text subscripts like `d\text{min}` or `d_\text{min}`:
     ```python
     text = re.sub(r'([a-zA-Z0-9])_?\{?\\text\{([^}]+)\}\}?', r'\1<sub>\2</sub>', text)
     ```
   - Standard LaTeX math operators (like `\min`, `\pm`, `\times`, `\leq`, `\geq`, `\neq`, `\approx`, `\div`, `\cdot`, `\rightarrow`, `\leftarrow`, `\Rightarrow`, `\infty`, `\max`) should be pre-converted to their Unicode equivalents at the beginning of `add_rich_runs` so they can participate in braced and unbraced subscript regex matching.
   - Greek letters and operators inside subscripts should also be replaced cleanly by supporting optional backslashes in Greek letter replacements.

3. **R3 (Paragraph Length Control)**:
   - In `add_formatted_explanation_paragraphs`, any plain explanation paragraph (not starting with bullet/list markers) that exceeds 350 characters should be split using:
     ```python
     sentences = re.split(r'(?<!\bi\.e)(?<!\be\.g)(?<!\bvs)(?<!\bapprox)(?<!\bfig)(?<!\bno)(?<=[.!?])\s+(?=[A-Z"“0-9])', line)
     ```
   - The resulting sentences should be grouped into chunks of at most 3 sentences (representing paragraphs of 2-3 sentences) and written as separate paragraph blocks.

## Refined Action Plan
- Spawn `teamwork_preview_worker` to implement all these changes in `scripts/generate_docx.py`.
- Run the build/compile verification and run the audit tool on mock notes.

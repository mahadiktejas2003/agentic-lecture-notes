# Project: Rendering and Parsing Fixes for Lecture-Note Reconstruction Pipeline

## Architecture
- Core Scripts:
  - `scripts/parse_transcript.py`: Handles transcript chunking, semantic block extraction, and LaTeX formatting.
  - `scripts/generate_docx.py`: Renders the JSON concept map into the final `.docx` file using custom styling.
  - `scripts/audit.py`: Validates the generated `.docx` against the 22 mechanical quality gates.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Explore rendering and parsing issues | Investigate generate_docx.py and parse_transcript.py to find code sections for OneNote/dark mode rendering, LaTeX subscripts and operators, and paragraph splitting. | none | DONE |
| 2 | Implement fixes | Implement R1 (OneNote/dark mode compatibility), R2 (LaTeX subscript & operators parsing), and R3 (abbreviation-safe paragraph splitting) in generate_docx.py and parse_transcript.py. | M1 | IN_PROGRESS |
| 3 | Regenerate & Verify | Regenerate all 5 CN notes and verify they pass the 22-gate audit script. | M2 | PLANNED |

## Interface Contracts
### `parse_transcript.py` ↔ `generate_docx.py`
- `parse_transcript.py` output `concept_block_map.json` contains blocks of text with rich markup/runs and LaTeX math formulas.
- `generate_docx.py` reads `concept_block_map.json` and renders paragraphs, tables, and runs with explicit styles, applying subscript translations and paragraph splitting.

## Code Layout
- `scripts/parse_transcript.py`: Parsing and formatting.
- `scripts/generate_docx.py`: Formatting, styling, and rendering logic.
- `scripts/audit.py`: 22-gate validation script.

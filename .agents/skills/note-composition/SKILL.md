---
name: note-composition
description: Composes exam‑ready .docx notes from manifests using the v8.0 Source Fidelity Protocol.
---

# Note Composition Skill

## Tools
- `run_shell_command` – generate_docx.py, audit.py
- `read_file` – manifests
- `write_file` – corrections

## Pre‑Condition Check
1. `frame_manifest.json` exists and not `{}`
2. `concept_block_map.json` exists with ≥2 blocks
3. `slide_manifest.json` exists (empty `[]` OK)
Abort if any fails.

## Execution

1. Validate manifests with `read_file`.
2. Generate document:
   ```bash
   source venv/bin/activate && python3 scripts/generate_docx.py --concept-map concept_block_map.json --frame-manifest frame_manifest.json --slide-manifest slide_manifest.json --output notes-output/LECTURE_NOTES.docx
   ```
3. Run audit:
   ```bash
   source venv/bin/activate && python3 scripts/audit.py --docx notes-output/LECTURE_NOTES.docx --concept-map concept_block_map.json --frame-manifest frame_manifest.json --slide-manifest slide_manifest.json
   ```
4. Fix failures and re‑audit until all 15 gates pass.

## Attribution Ban
NEVER write "the lecturer says", "the teacher explains", etc. Write content directly.

## Hardened Composition Constraints
- **Silent Visual Moments**: Never write `[BOARD MOMENT at ...]` or `[SLIDE MOMENT at ...]` in the notes. Images should be placed silently inline without any preceding descriptions or placeholder labels.
- **Exercise Omissions**: If an exercise item has no real content (i.e. is an empty string or placeholder integer), skip it entirely. Only render exercises that contain real text content.
- **Inline Screenshot Placement**: Always insert the corresponding visual moment screenshot inline immediately following the example's Answer/Working section. Use a 1-to-1 index matching between examples and visual moments in each block, keeping leftover images at the end of the block.
- **Rule Deduplication**: Filter out redundant rules within the same block. A rule should not print if it has a word overlap similarity ratio > 0.50 with any rule already printed in the current block.

## Anti-Patterns List
| Anti-Pattern | Description | Corrective Guideline |
| :--- | :--- | :--- |
| Wall of Text | Long, multi‑sentence paragraphs that restate rules already in examples | 2‑3 sentence introduction max; move details to worked examples, traps, and quotes |

## Delivery
"📄 Lecture notes generated: notes-output/LECTURE_NOTES.docx"

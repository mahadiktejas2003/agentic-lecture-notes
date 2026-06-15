---
name: transcript-mapping
description: Analyzes lecture transcripts to produce a chronological Concept Block Map.
---

# Transcript Mapping Skill

## Tools
- `read_file` – transcript
- `write_file` – concept_block_map.json

## Execution

1. Read transcript with `read_file`. Note total character count and estimate lecture duration (from SRT/VTT timestamps, or assume ~150 words/min spoken pace).
2. If <3000 characters for a 30+ min lecture, abort.
3. Scan linearly for: topics, every example, exercise questions, visual references, traps, tricks, quotes.
4. Group into chronological Concept Blocks (CB1, CB2…). Never regroup.
5. Build JSON per block:
```json
{
  "block_id": "CB1",
  "title": "...",
  "transcript_range_percent": [5, 25],
  "examples": [{"sentence":"...","rule":"...","working":"..."}],
  "exercise_questions": [1,2],
  "visual_moments": [{"timestamp":"00:03:30","type":"board","description":"..."}],
  "teacher_quotes": ["..."],
  "traps": ["..."],
  "tricks": ["..."]
}
```
6. Save `concept_block_map.json`.

## Hardened Mapping Constraints
- **Meaningful Block Titles**: Use the grammatical concept being taught as the title for each concept block, never generic question ranges (e.g. use "Disease Names & 'One Of' SVA Rules" instead of "Noun Practice Test Discussion (Questions 1 to 5)").
- **Quote Quality**: Clean each extracted teacher quote. Strip all SRT metadata (timestamps/line counters), leading stray vowel signs or symbols, ensure it is a complete sentence, and deduplicate identical quotes.
- **Lecture Title**: Store a dedicated `"lecture_title"` field in the first block of the manifest based on the overall topic (e.g., "English Discussion on Noun Exercise & Pronoun -1 (Live-7)").
- **Support for Tables**: If a concept block introduces a reference grid or table (such as the pronouns case grid), include a `"table"` property with `"title"`, `"headers"`, and `"rows"` so that the note compiler can render it as a styled Word table.
- **Math Explanations & Layout**: Ensure that all algebraic workings are detailed step-by-step and equations are written clearly. Highlight the Golden Rule check first. State "Don't even need to solve for roots" when roots are trivially compared.
- **Prime Factorization Method**: Map the grouping combinations and prime factors ladder for large constants.
- **Original Equations**: Extract original equations from the transcript/slides (like denominator variables or decimals) first.
- **Homework Questions (HW Que)**: Label homework questions clearly as "Homework Questions (HW Que): Try:" and map them correctly. Do not mix them with lecture examples. Do not hallucinate or invent extra questions.

## Density Verification Gate (MANDATORY — run before saving)

After building the map, perform these checks. If any fail, re‑scan the transcript and fix the map before writing it.

### Check 1: Example Density
- Count total examples across all blocks.
- Estimate lecture duration in minutes (from timestamps or word count ÷ 150).
- Expected density: ≥1 example per 3 minutes of lecture.
- If `total_examples < duration_minutes / 3`, the map is suspiciously sparse → re‑scan the transcript for missed examples.

### Check 2: Block Coverage
- Sum all `transcript_range_percent` spans. Total coverage must be ≥80% of the transcript.
- If large gaps exist between blocks, content was skipped → re‑scan those gaps.

### Check 3: Visual Moment Count
- Count total `visual_moments` across all blocks.
- If the transcript contains ≥5 visual cue phrases ("board", "slide", "screen", "look at", "see here") but the map has 0 visual moments, re‑scan for missed visuals.

### Check 4: No Hallucinated Content
- For each example in the map, verify the example sentence or a key phrase from it appears verbatim (or near‑verbatim) in the transcript text.
- If an example cannot be traced back, remove it.

Only save `concept_block_map.json` after all four checks pass.

## Deliverable
`concept_block_map.json` (≥2 blocks, real examples, density‑verified)
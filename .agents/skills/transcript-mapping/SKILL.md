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
  "examples": [{"timestamp": "00:03:30", "sentence":"...", "rule":"...", "working":"..."}],
  "exercise_questions": ["What is the first step?", "Why does this happen?"],
  "visual_moments": [{"timestamp":"00:03:30","type":"board","description":"..."}],
  "teacher_quotes": ["..."],
  "traps": ["..."],
  "tricks": ["..."]
}
```
6. Save `concept_block_map.json`.

## Hardened Mapping Constraints
- **Source Fidelity (CRITICAL — HIGHEST PRIORITY — APPLIES TO ALL FIELDS)**: ALL content in the concept block map — `working`, `rule`, `explanation`, `traps`, `tricks`, `teacher_quotes`, `exercise_questions` — must come EXCLUSIVELY from the teacher's spoken words in the transcript or the text on slides. The AI must NEVER:
  - Solve a problem using its own knowledge and write that as the `working`. Instead, extract the teacher's exact step-by-step reasoning from the transcript.
  - Replace the teacher's intuitive method (e.g. "look at both ends, gap is small") with a textbook method (e.g. "assuming common difference of AP...").
  - Invent `traps` or `tricks` that sound plausible but were not spoken by the teacher. If the teacher said "prime number mein koi trick nahi hoti", do NOT fabricate a trick.
  - Generate generic homework/exercise questions (e.g. "What is a hybrid series?"). Only include questions the teacher actually assigned.
  - Drop the teacher's contextual observations, identification heuristics (e.g. "if gap between first and last is small → add/subtract series, not multiply"), or trial-and-error verification steps.
  - Rephrase the teacher's simple Hinglish explanation into formal academic language. Preserve the teacher's phrasing, bilingual explanations, and colloquial transitions (e.g. *"kehna ye chah rha hai..."*, *"different के साथ..."*) verbatim inside `working`, `explanation`, and `teacher_quotes`.
  - Add steps, shortcuts, or notes the teacher did not mention.
- **Exclusion of Logistical & Administrative Content (CRITICAL)**: Do NOT map, extract, or explain any logistical comments, audio/video status check remarks, laptop battery/power status, construction, scheduling, greetings, or class management chatter. Notes must focus strictly on pedagogical content.
- **Rich Text Markdown Enforcement**: The generated JSON must use Markdown tags extensively to create visual hierarchy in the `explanation`, `rule`, and `working` fields.
  - Use `**bold**` for key terms, definitions, and important phrases.
  - Use `==highlight==` or `<highlight color="BLUE">` tags for critical formulas, standout facts, or crucial warnings. Yellow/green highlights are strictly banned.
- **Preposition & Grammar Exhaustiveness**: For prepositional or rule variations discussed by the teacher (e.g., `agree with/on/to`), map out every single option, its context, and corresponding example sentences. Never aggregate or summarize them into a single bullet.
- **Exhaustive Example Extraction**: Every worked example mapped must contain the full question sentence, all option choices, correct key, applicable rule, and step-by-step reasoning/working. Never shorten or truncate these fields.
- **Meaningful Block Titles**: Use descriptive titles. For conceptual parts, use the grammatical concept. For assignments or practice tests, use titles like "Noun Practice Test Discussion (Questions 1 to 5)" to preserve chronological flow.
- **Strict Chronological Sequence**: When mapping assignments or practice tests, do NOT group questions by topic if it breaks the chronological order. Maintain the strict numerical sequence of the lecture (e.g., Q1, Q2, Q3).
- **Timestamp Binding**: Every example MUST have a `timestamp` field that matches the exact time the question is solved on the board, ensuring the correct screenshot is pulled.
- **Quote Quality**: Clean each extracted teacher quote. Strip all SRT metadata (timestamps/line counters), leading stray vowel signs or symbols, ensure it is a complete sentence, and deduplicate identical quotes. Do not extract any logistical/administrative quotes.
- **Lecture Title**: Store a dedicated `"lecture_title"` field in the first block of the manifest based on the overall topic (e.g., "English Discussion on Noun Exercise & Pronoun -1 (Live-7)").
- **Support for Tables**: If a concept block introduces a reference grid or table (such as the pronouns case grid), include a `"table"` property with `"title"`, `"headers"`, and `"rows"` so that the note compiler can render it as a styled Word table.
- **Math Explanations & Layout**: Ensure that all algebraic workings are detailed step-by-step and equations are written clearly. Highlight the Golden Rule check first. State "Don't even need to solve for roots" when roots are trivially compared.
- **Prime Factorization Method**: Map the grouping combinations and prime factors ladder for large constants.
- **Original Equations**: Extract original equations from the transcript/slides (like denominator variables or decimals) first.
- **Exercise Questions**: Exercise questions must be full sentences containing real text (e.g. "What is the first step?"), not just raw integers or question numbers.
- **Homework Questions (HW Que)**: Label homework questions clearly as "Homework Questions (HW Que): Try:" and map them correctly. Do not mix them with lecture examples. Do not hallucinate or invent extra questions.
- **Student Reference Notes**: If `reference_manifest.json` exists, you MUST read its OCR text to extract the student's handwritten instructions (e.g., "AI / note this"), scribbles, and extra content. Integrate this content chronologically into the concept blocks. Treat these notes as absolute ground truth for overrides. Never hallucinate or ignore the student's explicit instructions. **If the lecture video is unavailable or no frames were extracted**, treat these reference notes as the primary visual source and map their pages into the `visual_moments` array as `type: "slide"`, so they get inserted into the final document.

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
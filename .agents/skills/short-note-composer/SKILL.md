# Short Note Composer

You generate a compact, exam-ready short revision note from the project's structured lecture artifacts.

## Purpose

This skill exists alongside the full lecture-note pipeline. It does **not** replace the detailed notes. It produces a second artifact:

- `notes-output/<lecture-title>_SHORTNOTE.md`

The short note must be:

- readable in under 5 minutes
- self-contained without the original lecture
- anchored to the real lecture content
- concise enough to fit roughly one printed A4 page

## Inputs

Use these project artifacts when available:

- `concept_block_map.json`
- `slide_manifest.json`
- `frame_manifest.json`
- the cleaned lecture transcript in `lecture-input/`

The transcript and concept map are the primary sources of truth. Slides and frames are only supporting context.

## Core Rules

1. Keep the detailed `.docx` notes unchanged.
2. Produce a separate short-note artifact.
3. Never invent facts not supported by the lecture artifacts.
4. Prefer rules, examples, warnings, shortcuts, and teacher-emphasis points over prose summaries.
5. No Devanagari script. Use English or romanized wording only.
6. No conversational attribution such as "the teacher says".

## Required Structure

Every short note should include:

1. A context anchor.
   - Format: `From <lecture title>, answering: "<core question>"`
2. A subject-appropriate compact body.
3. A trap box with common mistakes or warnings.
4. A self-test question.
5. Source provenance.
6. Review cadence footer.

## Subject Templates

### Mathematics / Quantitative Aptitude

Use a compact 3-column table:

- Formula / Concept
- Shortcut / Trick
- Solved Pattern / Example

### Reasoning

Use:

- a tiny decision map
- 3-6 red-flag bullets
- 1 worked pattern

### English

Use:

- `Rule | Correct | Wrong` for grammar
- `Word | Synonyms | Antonyms | Tone` for vocabulary

### General Awareness

Use:

- a comparison table
- a `What -> Why -> Impact` chain

### Technical

Use:

- `Concept | Why it matters`
- a mini dependency chain
- 1-3 exam-style quick questions

### Theory

Use:

- `Question | Answer / Evidence`
- short chronology or cause-effect bullets

## Eternalizing Injections

Apply these when relevant:

- Context Anchor
- Memory Hook
- Analogical Bridge
- Minimal Explanation Tag
- Self-Contained Formula
- Source Provenance
- Future-Self Footnote
- Glossary Micro-Stub
- Trap / Mistake Log

Do not force all of them into every lecture. Use them where they genuinely help compression and recall.

## Output Constraints

- Markdown only
- concise, high-density formatting
- fragments, arrows, bullets, tables
- avoid long paragraphs
- target approximately 300-500 words excluding tables/checklist

## Footer

End with:

- one self-test question
- `_Review: 1/4/52 - Anki (weekly), Monthly reconstruction, Annual dust-off._`
- the mini checklist:
  - `[ ] Day 1 - Blurt & compress`
  - `[ ] Day 2 - Refine draft`
  - `[ ] Day 7 - Self-test from cues`
  - `[ ] Month 1 - Reconstruct from anchor`
  - `[ ] Month 6 - Update traps`
  - `[ ] Year 1 - Dust-off`

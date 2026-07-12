---
name: lecture-note-reconstruction
description: The ultimate master orchestrator skill to run the entire lecture‑note reconstruction pipeline, enforce source fidelity, and audit the 22 quality gates.
version: 2.0
---

# Lecture Note Reconstruction Master Skill

This skill acts as the unified, authoritative guide for the entire lecture-note reconstruction pipeline. It integrates the guidelines from all sub-skills (transcript-mapping, frame-extraction, slide-parsing, note-composition, student-tester, and pdf-ocr-extraction) and styling rules into a single, cohesive source of truth for all AI agents.

---

## 1. Pipeline Orchestration & State Protocol

### A. Central State Tracking
All state transitions, stage completions, and pipeline checks must be registered in the central state file `workspace_state.json` at the project root. This maintains coordination between different agents and executions:
1. **Active Lecture Info**: Track the title, video path, transcript path, and run fingerprint.
2. **Pipeline Stage**: Track the current stage (`start`, `content-mapped`, `examples_extracted`, `reference_extracted`, `completed`, `failed`, or `abort`).
3. **Audit Status**: Track the audit score (passed gates count) and the list of failed gates.

### B. SHA-256 Run Fingerprint
To prevent the accidental reuse of stale manifests across different runs or lectures:
- Compute a SHA-256 fingerprint from the active `LECTURE.mp4` video size/modification time, `transcript.srt` size/modification time, and `SLIDES.pdf` size/modification time.
- Verify this fingerprint against the one in `workspace_state.json`. If they do not match, clear all stale files: `concept_block_map.json`, `frame_manifest.json`, `slide_manifest.json`, `reference_manifest.json`, `embedded_manifest.json`, `inserted_images.json`, and `notes-output/LECTURE_NOTES.docx`.

### C. Process Locking
To prevent concurrent write conflicts:
- Check for `logs/pipeline.lock`. If present, read the PID inside it.
- Verify if a Python orchestrator process is currently running under that PID. If active, abort.
- If inactive, write the current PID to `logs/pipeline.lock` and remove the file upon completion.

---

## 2. Ingestion & Transcript Mapping

### A. Source Ingestion & OCR Processing
1. **ASR Transcription**: If the transcript is missing or incomplete (ratio of transcript end time to video duration < 85% or containing truncation warnings), run `scripts/transcribe_lecture.py` using local GPU/ASR models to generate `transcript.srt`.
2. **Slide & Reference Parsing**: Run `scripts/process_slides.py` on `lecture-input/SLIDES.pdf` and `lecture-input/REFERENCE_NOTES.pdf` to convert pages to PNG, run OCR (using pytesseract with language flag `eng+hin`), and extract raw embedded screenshots.
3. **Coordinate-Based Screenshot Filtering**: Extract embedded image blocks from reference PDFs using PyMuPDF. Ignore elements with width <= 400 or height <= 100 to filter out strokes, lines, and icons.
4. **No Note Pages Screenshotting**: Do NOT take full-page screenshots of the handwritten reference note pages themselves. Only extract raw embedded images/assets or use video frames.

### B. Transcript-Mapping Protocol
Parse the transcript chronologically to segment it into distinct concept blocks:
1. **No Invention**: Do not add outside knowledge. If a term is unclear, use `[Transcript unclear]`.
2. **Exclusion of Logistical Content**: Exclude comments on audio/video clarity, stream status, power cuts, laptop battery, greetings, and class scheduling.
3. **Semantic Differentiation**: Define terms in the `concepts` list. The `explanation` block is reserved ONLY for high-level context, real-world analogies, and the "Why". If there is no analogy, leave `explanation` empty.
4. **Student Reference Note Integration**: If `REFERENCE_NOTES.pdf` contains handwritten annotations, read its OCR text to extract instructions (e.g., "AI / note this"), warnings, or side-notes, and integrate them chronologically into the concept blocks. If a lecture video is unavailable, map reference note pages as slides into the visual moments to serve as the visual source.
5. **Exact worked examples**: Map out the full question sentence, all option choices, correct key, applicable rule, and step-by-step reasoning/working. Never shorten these fields.

### C. Override Heuristic for User Corrections
Interpret handwritten or typed annotations like 'WRONG', 'USKA KHUDKA BRAIN KYU USE KARTA HAI...', or 'WRONG EXPLANATION' as explicit instructions to discard default AI math/grammar/logical logic, replacing them entirely with the student's exact specified steps, calculations, and diagrams.

### D. Banned Conversational Attributions
Never write introductory attributions. State facts directly. The following 36 phrases are strictly banned:
- "the lecturer says", "the teacher explains", "the instructor mentions", "this is discussed in the lecture", "the teacher describes", "the teacher outlines", "the teacher demonstrates", "the teacher analyzes", "the teacher shares", "the teacher introduces", "the teacher reviews", "the teacher teaches", "the teacher shows", "the teacher discusses", "the instructor outlines", "the instructor demonstrates", "the instructor analyzes", "the instructor shares", "the instructor introduces", "the instructor reviews", "the instructor teaches", "the instructor shows", "the instructor discusses", "the lecturer outlines", "the lecturer demonstrates", "the lecturer analyzes", "the lecturer shares", "the lecturer introduces", "the lecturer reviews", "the lecturer teaches", "the lecturer shows", "the lecturer discusses", "we see", "we analyze", "let's see", "let's look".

---

## 3. Visual Moment Extraction

### A. Windowed Candidate Search (Frame Extraction)
For every visual moment timestamp $T$ in the concept map:
- Extract 5 candidate frames at `[T-8s, T-5s, T-2s, T, T+2s]`.
- Run OCR on all candidates and select the frame with the **highest alphanumeric word count** (minimum 3-char words). This captures the most complete slide/board state and avoids teacher occlusion.
- **Solved-State Timestamps**: Target timestamps towards the end of each question explanation (right before the next segment starts) to capture completed board writing, handwritten solutions, and vector diagrams.

### B. Deduplication & Branding Filters
- **Deduplication Bypass**: If specific timestamps are requested (i.e. hand-picked visual moments), bypass OCR deduplication in `extract_frames.py` entirely. Hand-picked moments represent distinct concept states and must not be deleted.
- **Branding Filter**: Discard any frame whose OCR contains "Gate Smashers" or "Gate Smasher" if the word count is less than 25 or contains subscription/social cues.
- **High Insertion Similarity Threshold (0.85)**: In `generate_docx.py`, use an OCR similarity threshold of 0.85 or higher to prevent distinct worked examples from being omitted due to common mathematical/directional terms.

---

## 4. Note Composition & Styling

### A. Document Layout & Colors
- **Main Font**: Calibri 11pt, color Charcoal/Slate Gray (`RGB 43, 47, 54` or `#2B2F36`).
- **Heading Colors**:
  - Title (Level 0): Deep Navy (`RGB 19, 40, 75` or `#13284B`). No generic prefixes like "NOTES ##".
  - H1 (Level 1): Slate Blue (`RGB 42, 75, 126` or `#2A4B7E`).
  - H2/H3 (Level 2/3): Steel Blue (`RGB 63, 108, 175` or `#3F6CAF`).
- **Highlighting Colors (mapped to custom OpenXML run-level shading)**:
  - `BLUE` -> Soft Pastel Sky Blue (`#E1F5FE`)
  - `GRAY` -> Soft Pastel Gray (`#F1F5F9`)
  - `RED` -> Soft Pastel Red (`#FEE2E2`)
  - `ORANGE` -> Soft Pastel Orange (`#FFEDD5`)
  - `PURPLE` -> Soft Pastel Purple (`#F3E8FF`)
- **Box Background Shading Fills**:
  - `[⚡ Quick Rev]` Box: Light Blue shading (`#D6EAF8`), text size Calibri 9pt.
  - `💡 Student Note / Doubt` Box: Premium soft Ice-Blue shading (`#F0F4F8`), text size Calibri 11pt.
  - Centered Shaded Formulas: Light Gray shading (`#EAECEE`), center-aligned, Calibri 11pt, bold.
  - Tables: Calibri 9pt. Header row cell background is Dark Slate (`#2C3E50`) with bold white text (`#FFFFFF`). Alternating rows (odd row indices) have cell background shading of Light Gray (`#F2F3F4`).

### B. Note Layout and Content Constraints
- **Inline Image Placement**: Place screenshots inline, directly under the worked example they illustrate, using a 1-to-1 index association between `examples` and `visual_moments`. Leftover visual moments (e.g., introduction diagrams or slides) must remain at the end of the concept block. Never cluster images at the end of sections.
- **Teacher's Emphasis**: Highlight important points emphasized by the teacher (e.g., "this is very important", "will come in exam") using stars, specifically formatting them as `⭐ **[IMPORTANT]**` or `⭐ **IMPORTANT**`.
- **Dynamic Example Formatting**: Do not force all examples into Q&A blocks. Use Q&A (`Q: / Applicable Rule: / Explanation/Working: / Answer:`) for active, question-based worked examples and simple `Example: / Explanation:` or `Example: / Key Concept: / Explanation:` for scenario-based teaching.
- **Productive Friction Matrix**: Compile notes using the three-layer Friction-Optimized Note Matrix:
  - *Layer 1 (AI Synthesis)*: Passive Base conceptual outlines and outline trees.
  - *Layer 2 (Friction Overlay)*: Active Cloze deletions using `<cloze answer="X" hint="Y">[......]</cloze>` for key formulas, definitions, and conclusions; Cornell "Why/How" cues (columns 2.0" and 4.5"); and spaced-repetition tags like `[SRS: +3 Days]`.
  - *Layer 3 (Boundary Testing)*: Three unsolved edge-case boundary testing questions placed at the end of each block.
- **Bolding and Highlighting with Colored Markers**: Use markdown bolding (`**text**`) extensively. Apply color highlighting using tags like `<highlight color="BLUE">text</highlight>`, `<highlight color="RED">text</highlight>`, `<highlight color="PURPLE">text</highlight>`, or `<highlight color="ORANGE">text</highlight>` for critical rules, standout facts, or crucial formulas.

### C. Topper-Grade Tone & Explanatory Balance
- **Childish Language Elimination**: Eliminate childish, conversational commentary (e.g., "Let's draw this step-by-step"). Present information directly as facts in direct, analytical prose.
- **Bilingual Transitions**: Preserve the teacher's Hinglish/bilingual explanations or colloquial transitions (e.g., *"kehna ye chah rha hai ki..."*) in *italics*, paired with their English meaning or explanation.
- **Detailed Preposition & Grammar Maps**: Map out every single preposition or rule variant in detail with corresponding examples (e.g., `agree with (person)`, `agree on (matter/point)`, `agree to (proposal/suggestion)`, `different from` rather than `different than/to`). Do not aggregate or summarize them into a single line.

### D. Mathematical Unicode Mapping
All mathematical text and LaTeX expressions must be formatted into clean, readable Unicode equivalents:
1. **Exponents**: Convert exponent patterns like `x^2`, `y^(n+1)`, or `(A)^k` to superscript Unicode characters:
   - `0`->`⁰`, `1`->`¹`, `2`->`²`, `3`->`³`, `4`->`⁴`, `5`->`⁵`, `6`->`⁶`, `7`->`⁷`, `8`->`⁸`, `9`->`⁹`, `-`->`⁻`, `+`->`⁺`, `=`->`⁼`, `(`->`⁽`, `)`->`⁾`, `n`->`ⁿ`, `i`->`ⁱ`, `x`->`ˣ`, `y`->`ʸ`.
   - Fractions: `x^(1/2)` -> `x¹/²`.
2. **Subscripts**: Convert subscript patterns like `x_1`, `y_(n-1)` to subscript Unicode characters:
   - `0`->`₀`, `1`->`₁`, `2`->`₂`, `3`->`₃`, `4`->`₄`, `5`->`₅`, `6`->`₆`, `7`->`₇`, `8`->`₈`, `9`->`₉`, `-`->`₋`, `+`->`₊`, `=`->`₌`, `(`->`₍`, `)`->`₎`, `n`->`ₙ`, `i`->`ᵢ`, `x`->`ₓ`, `y`->`ᵧ`.
3. **LaTeX Mathematical Operators**:
   - `\pm` -> `±`, `\times` -> `×`, `\leq` -> `≤`, `\geq` -> `≥`, `\neq` -> `≠`, `\approx` -> `≈`, `\div` -> `÷`, `\cdot` -> `·`, `\rightarrow` -> `→`, `\leftarrow` -> `←`, `\Rightarrow` -> `⇒`, `\infty` -> `∞`.
   - Replace ASCII symbols: `->` -> `→`, `<-` -> `←`, `=>` -> `⇒`, `<=` -> `≤`, `>=` -> `≥`, `!=` -> `≠`, `+/-` -> `±`.
   - Multiplications: Replace `*` with spaces around it to ` × ` (e.g., `5 * x` -> `5 × x`).
4. **Square Roots**:
   - Convert `\sqrt{expression}` to `√(expression)`.
   - Convert `\sqrt` to `√`.
   - Convert `sqrt(expression)` to `√(expression)`.
5. **Fraction Character Map**: Convert standard simple fractions to single Unicode fraction glyphs:
   - `1/2` -> `½`, `1/4` -> `¼`, `3/4` -> `¾`, `1/3` -> `⅓`, `2/3` -> `⅔`, `1/5` -> `⅕`, `2/5` -> `⅖`, `3/5` -> `⅗`, `4/5` -> `⅘`, `1/6` -> `⅙`, `5/6` -> `⅚`, `1/8` -> `⅛`, `3/8` -> `⅜`, `5/8` -> `⅝`, `7/8` -> `⅞`.
6. **Greek Letter Map**: Convert common Greek letter names to their lowercased Unicode equivalent characters:
   - `alpha` -> `α`, `beta` -> `β`, `gamma` -> `γ`, `delta` -> `δ`, `epsilon` -> `ε`, `zeta` -> `ζ`, `eta` -> `η`, `theta` -> `θ`, `iota` -> `ι`, `kappa` -> `κ`, `lambda` -> `λ`, `mu` -> `μ`, `nu` -> `ν`, `xi` -> `ξ`, `pi` -> `π`, `rho` -> `ρ`, `sigma` -> `σ`, `tau` -> `τ`, `upsilon` -> `υ`, `phi` -> `φ`, `chi` -> `χ`, `psi` -> `ψ`, `omega` -> `ω`.

### E. Math Layout & Worked Examples
- **Step-by-Step Layout**: Algebraic manipulations or multi-step explanations must place intermediate equations on separate lines or list elements.
- **Golden Rule Shortcut**: Prioritize checking root signs from equation coefficients before performing any splits. In comparison questions, check if signs are opposite. If they are, state that no root solving is needed: "Don't even need to solve for roots."
- **Prime Factorization**: For large constant terms, show the step-by-step prime factors ladder and combinations that sum to the middle term.
- **Leading Coefficients (a > 1)**: Explain the product of coefficients `a × c`, finding factors, and division by the leading coefficient `a` explicitly.
- **Middle Term Square Roots**: Explain the shortcut step-by-step: divide constant `c` by radicand `k`, split `c/k` to sum to `b`, then attach `\sqrt{k}` back.
- **Original Equations**: Always present the original equation forms as written on the board (fraction or decimal equations) first, before showing simplified integer equations.
- **Homework Questions (HW Que)**: Label homework/practice questions explicitly as "Homework Questions (HW Que): Try:" and do not mix them with lecture examples. Do not hallucinate or invent extra questions.

### F. Pointing-Type Worked Examples
For pointing-type blood relations questions, always provide two methods:
- **Method 1 (Analytical Tracing)**: Tracing backward step-by-step starting from the possessive pronoun anchor (e.g., "my", "me").
- **Method 2 (Visual Drawing via Numbered Nodes)**: Step-by-step drawing of the family tree by mapping speaker references directly to numbered nodes.

---

## 5. The 22 Quality Gates Audit

Every compiled notes document is audited using these 22 quality gates:

1. **Gate 1: Structural Integrity**: Heading 2 count `h2 > 0`, revision box count `rev <= h2`, visual placeholder strings `vis_fail == 0`, and banned attributions `attr_fail == 0`.
2. **Gate 2: Revision Box Placement**: Revision box paragraphs (containing `[⚡ Quick Rev]`) must be at most equal to Heading 2 paragraphs.
3. **Gate 3: Chronological Flow**: The count of Heading 2 sections in the document matches exactly the length of the concept blocks array.
4. **Gate 4: Content Completeness**: The concept block map array is not empty.
5. **Gate 5: Factual Accuracy**: Worked examples count in document is greater than or equal to the count mapped in the concept map.
6. **Gate 6: Image Integrity**: No paragraphs in the document contain the placeholder string `"Visual anchor"`.
7. **Gate 7: Minimum Counts**: Document has at least 1 heading and contains at least 80% of expected images.
8. **Gate 8: Source Traceability**: The normalized document title matches the normalized concept map lecture title.
9. **Gate 9: Slide Handling**: Fails if slides are expected but slide manifest is empty. Otherwise, passes if no slide marked `discussed: false` has its OCR text (>5 chars) present in the document.
10. **Gate 10: Example Coverage**: All mapped examples are present in the final compiled document.
11. **Gate 11: Visual Coverage**: Final document contains at least 80% of the expected unique images.
12. **Gate 12: Exercise Content**: All exercises are descriptive text strings rather than template integers or empty spaces.
13. **Gate 13: Quote Quality**: No quotes match raw SRT timeline formatting or start with broken symbols, vowel modifiers, or spaces.
14. **Gate 14: Meaningful Titles**: Block titles are meaningful concept names, not generic question ranges (matching regex `r'^.*\(Questions?\s*\d+'`).
15. **Gate 15: Explanation Conciseness**: Explanations must not exceed 2000 characters or contain the word `"First,"` more than once.
16. **Gate 16: Table Presence**: If any concept block defines a table, the compiled document must contain at least 1 table.
17. **Gate 17: Sequence Integrity**: The section headings in the document follow the exact sequence defined in the concept map.
18. **Gate 18: Exact Worked Examples**: Every worked example sentence from the concept map is present in the final document text.
19. **Gate 19: Friction Index Constraint**: Friction Index, calculated as `(cloze_count + cornell_cues_count) / total_words`, does not exceed 0.40 (40%).
20. **Gate 20: Transcript Coverage**: Validates chronological coverage calculations properly span the transcript duration (at least 80% coverage) and H2 heading presence (at least 80% headings found in docx).
21. **Gate 21: English Enforcement**: Verifies Devanagari script is strictly cleaned from all text fields and limits transliterated Hinglish keywords to at most 40.
22. **Gate 22: Styling and Highlighting Conformity**: Enforces zero native Word highlights, pastel shades for run shading, specific paragraph shading for Quick Revision boxes (`#D6EAF8`), and Student Note/Doubt boxes (`#F0F4F8`).

---

## 6. Integrated Tooling & Commands

To ensure optimal execution and coordination, agents should understand and recommend the following integrated slash commands and tooling protocols during the reconstruction lifecycle:

### A. Core Slash Commands
1. **/goal**: Recommend this command when the user initiates note reconstruction. It forces the system to run in a loop with deep self-auditing, only terminating when the 22 quality gates pass perfectly.
2. **/teamwork-preview**: Spawn a collaborative subagent team (`teamwork_preview`) when tasks require broad template creation, multi-source mapping coordination, or complex formatting layout designs.
3. **/learn**: Recommend after applying custom corrections (e.g., twin series sequences, grammar exception lists, or visual crop mappings). This registers rules permanently in the repository config to prevent regression in future sessions.
4. **/grill-me**: Trigger when resolving design trees, ambiguity in mathematical formulas, or when deciding whether to prioritize slides over transcript explanations.

### B. Specialized Sub-skills Integration
1. **PDF OCR Extraction**: When processing scanned documents, handwritten notes, or PDFs with embedded vector graphics, use Optical Character Recognition (`pytesseract` with `eng+hin` configuration) to extract text content, warnings, and corrections from reference documents.
2. **Context Engineering**: Before beginning a run, audit and recovery must check `workspace_state.json`, build/compile locks under `logs/`, and the `docs/ISSUES_REGISTRY.md` to align the agent context with the active codebase state.
3. **Video Frames Extraction**: Trigger frame extraction sequentially using ffmpeg to extract candidate slides and completed worked examples. Select frames with the highest alphanumeric word count to ensure teacher occlusion is bypassed.


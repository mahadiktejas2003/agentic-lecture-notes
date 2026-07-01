# Note Writing Style Rules

## Source Fidelity Protocol (HIGHEST PRIORITY — APPLIES TO ALL LECTURES)
ALL content in the notes — explanations, workings, methods, rules, traps, tricks — must come EXCLUSIVELY from the teacher's spoken words in the transcript or the slides. The AI must NEVER:
- Solve a problem using its own mathematical/grammatical/logical knowledge
- Replace the teacher's intuitive method with a textbook method
- Add steps, shortcuts, or explanations the teacher did not mention
- Rephrase a simple spoken explanation into formal academic language
- Invent "traps" or "tricks" that the teacher did not explicitly state

The teacher's method IS the correct method for these notes, even if the AI knows a "better" or "more elegant" way. If the teacher uses trial-and-error, write trial-and-error. If the teacher says "koi particular method nahi hai, trick hai", write that.

## Attribution Ban (STRICT)
NEVER write: "the lecturer says", "the teacher explains", "the instructor mentions", "this is discussed in the lecture", "the teacher describes", "the teacher outlines", "the teacher demonstrates", "the teacher analyzes", or any similar attribution phrase. Write the content directly as fact.

Paragraphs must remain unified and not be split into single-sentence lines in the final compiled Word document. Use single asterisks (like *plays*, *play*) for italicized words.

## Color Highlighting & Markers (STRICT)
Aggressively apply bolding (`**text**`) for key terms and definitions. Apply color highlighting using tags like `<highlight color="BLUE">text</highlight>`, `<highlight color="RED">text</highlight>`, `<highlight color="PURPLE">text</highlight>`, `<highlight color="ORANGE">text</highlight>`, or `<highlight color="GRAY">text</highlight>` for critical rules, standout facts, or formulas. Crucially, standard neon yellow/green highlights are strictly banned; all highlight tags are converted by the docx generator to soft pastel background run-level shading (blue `E1F5FE`, red `FEE2E2`, purple `F3E8FF`, orange `FFEDD5`, gray `F1F5F9`).

## Exception
Hindi mnemonics preserved in *italics* with English meaning: *"सहज पके सो मीठा होय"* (Slow and steady wins the race).

## Anti‑Screenshot‑As‑Content
Screenshots supplement; they do NOT replace written content. Never use "as shown in the screenshot" as a substitute for explaining content.

## Mathematical Explanations and Layout Guidelines
- **Math Formatting**: Always output math expressions clearly. LaTeX syntax inside paragraphs (e.g. `\(ax^2 + bx + c = 0\)`) is preferred for the mapping agent. The compilation script will convert this to unicode. Avoid raw, unparsed LaTeX markup in the final docx.
- **Step-by-Step Layout**: Algebraic manipulations or multi-step explanations must NOT be written in a single block paragraph. They must be formatted with each step on a new line or sentence. For example:
  1. First, evaluate the signs using the Golden Rule.
  2. Next, split the constant term.
  3. Divide by the leading coefficient.
- **Golden Rule Shortcut**: Prioritize checking root signs from equation coefficients before performing any splits. In comparison questions, check if signs are opposite (e.g., all positive roots for one vs all negative roots for the other). If they are, state that no root solving is needed: "Don't even need to solve for roots."
- **Prime Factorization**: For large constant terms, show the step-by-step prime factors ladder and combinations that sum to the middle term.
- **Leading Coefficients (a > 1)**: Explain the product of coefficients `a \times c`, finding factors, and division by the leading coefficient `a` explicitly.
- **Middle Term Square Roots**: Explain the shortcut step-by-step: divide constant `c` by radicand `k`, split `c/k` to sum to `b`, then attach `\sqrt{k}` back.
- **Original Equations**: Always present the original equation forms as written on the board (e.g., fractional equations like `50/x^2 - 15/x + 1 = 0` or decimals like `0.25x^2...`) first, then show the scaled integer equations (e.g., `x^2 - 15x + 50 = 0` or `x^2 + 14x + 45 = 0`).
- **Avoid Complex Jargon**: Always use simple, student-friendly terminology for equation conversion techniques rather than complex academic terms.
  - Use **Clearing Fractions** (or "Multiply by Denominator") instead of "Fractional Term Clearing" or "Fractional Constant".
  - Use **Clearing Denominator Variables** (or "Clearing Denominators") instead of "Reciprocal Variable Clearing" or "Denominator Variables".
  - Use **Clearing Decimals** (or "Scale Decimals") instead of "Decimal Scaling Factor" or "Decimal Coefficients".
  - Always include a simple, short 1-line mathematical example inline for each concept (e.g., "multiply by 4 to turn 0.25 into 1").
- **Homework Questions (HW Que)**: Label homework/practice questions explicitly as "Homework Questions (HW Que): Try:" and do not mix them with lecture examples. Do not hallucinate or invent extra questions unless they are explicitly in the source material.

## Topper-Grade Tone & Explanatory Guidelines (Balanced Clarity)
- **Analytical & Explanatory Balance**: Avoid dry, overly abstract summaries. Keep the notes highly explanatory, preservation-oriented, and structured. Retain the teacher's core analogies, explanations, and workings.
- **Explanations & Definitions Quality**: Definitions must be mathematically, grammatically, and logically precise. Avoid circular or overly brief explanations. Explain the underpinnings of why a pattern works and how to identify it.
- **Important Points & Key Terms**: Bold all critical terms, mathematical operations, pattern names, variables, and formulas (using `**[text]**` or `**text**` tags) to create a visual hierarchy.
- **Bilingual & Colloquial Explanations**: Preserve the teacher's Hinglish/bilingual explanations, mnemonic sayings, and colloquial Hindi explanations/transitions (e.g., *"kehna ye chah rha hai ki..."*, *"different के साथ from आता है..."*) in italics, paired with their English meaning or explanation.
- **Exclusion of Logistical & Administrative Content**: Do NOT include any quotes, notes, Cornell blocks, or explanations regarding class logistics, audio/video settings, stream status, power cuts, construction, laptop battery levels, class scheduling, or teacher greetings. Keep the notes 100% focused on pedagogical and content-related instruction.
- **Highlighting & Colors**: Use soft pastel highlights for important terms instead of default harsh highlighters. Color selections must feel premium, using soft shades: light sky blue (`E1F5FE`), light red (`FEE2E2`), light purple (`F3E8FF`), light orange (`FFEDD5`), or light gray (`F1F5F9`). Standard high-contrast neon yellow and green highlights are strictly banned; highlights must be applied using custom run shading in the docx generator.
- **Detailed Preposition & Grammar Maps**: For grammatical concepts, map out every single preposition or rule variant (e.g., `agree with (person)`, `agree on (matter/point)`, `agree to (proposal/suggestion)`) in detail with corresponding examples for each. Do not aggregate or summarize them into a single line.
- **Exhaustive Example Elements**: Always render examples in full. Include the complete question text, all options, correct answer key, the specific rule applied, and the step-by-step working/reasoning. Never truncate options or shorten question sentences.
- **Childish Language Elimination**: Avoid casual motivational fillers, conversational commentary (e.g., "Let's solve this together", "Practice makes it easy"), and meta-commentary (e.g., "In this slide, the lecturer tells us..."). Present information directly as facts.
- **Common Student Doubts & Warnings**: Actively capture common student doubts, misconceptions, and warning points mentioned by the teacher (e.g., "students often make sign errors here" or "paternal vs maternal confusion"). Document these concisely inside inline `student_notes` callouts. Keep them brief and focused so they do not bloat or distract from the main topic.
- **Annotated Typo Resolution**: Document slide text cut-offs, transcription errors, or teacher contradictions in square brackets `[...]` as inline annotations, detailing how context or lookup resolved them.

## Pointing-Type Question Working
- For pointing-type blood relations questions, always provide two methods:
  - **Method 1 (Analytical Tracing)**: Tracing backward step-by-step starting from the possessive pronoun anchor (e.g., "my", "me").
  - **Method 2 (Visual Drawing via Numbered Nodes)**: Step-by-step drawing of the family tree by mapping speaker references directly to numbered nodes.

## Productive Friction Guidelines (Against Cognitive Offloading)
- Compile notes using a **three-layer Friction-Optimized Note Matrix** to promote active recall:
  - **Layer 1: Passive Base**: The conceptual outline hierarchy, standard math definitions, and diagrams.
  - **Layer 2: Active Friction Overlay**:
    - *Cloze Deletions*: Wrap critical terms, formulas, and key conclusions in `<cloze answer="X" hint="Y">[......]</cloze>` tags to display as underlines.
    - *Cornell Margins*: Formulate conceptual "Why" or "How" questions in the cue margin of the section to facilitate student self-quizzing.
    - *SRS Metadata*: Tag each concept section with a Spaced-Repetition interval tag (e.g., `[SRS: +3 Days]`) to enable programmatic flashcard export.
  - **Layer 3: Boundary Testing**: Place three unsolved edge-case application questions at the end of each block, representing scenario variations where standard rules require extrapolation.

## Syllogism Formatting and Diagram Rules:
- **Exclusivity Notation**: When styling "Only A are B" (All B are A), highlight the exclusive nature of B: *Note: Since B is exclusive to A, it has no relation to any other term.*
- **Venn Diagram Cues**: When describing diagrams in visual moments:
  - For standard intersection: Intersecting circles A and B.
  - For "Only a few A are B": Intersecting circles A and B, with a shaded/crossed section in A pointing to B representing the "Some A are not B" restriction.
- **Option Equivalence**: Always explicitly note option equivalents in practice exercises: *Neither I nor II follows is equivalent to Both do not follow.*

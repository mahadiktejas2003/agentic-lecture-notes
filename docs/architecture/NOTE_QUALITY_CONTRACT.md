# Note Quality Contract & Specifications

This document defines the strict quality, formatting, structural, and visual standards that all generated lecture notes (full and short) must satisfy.

---

## 1. Output Contracts

### A. Full Lecture Notes (.docx)
- **Goal:** Comprehensive, scannable, and factually accurate study document.
- **Factual Fidelity:** 100% of all taught concepts, formulas, rules, and worked steps must be preserved. No information may be dropped or summarized away.
- **Anti-Redundancy:** No semantic duplicate rendering. A concept, rule, or explanation must be printed only once per block. Do not repeat definitions or rules in explanations or callouts.
- **Topic Headings:** All H2/H3 titles must correspond directly to actual lecture sub-topics. Scaffolding prefixes like "Section X", "Detailed Concept Blocks", and "CBx" are prohibited.
- **No-Paragraph Rule:** Any explanation, concept, or logical trace taking more than 3 sentences to explain must be formatted as structured bullets or a Markdown table.
- **Word Budget:** Target range of 2,500–3,500 words for a standard 1-hour lecture, with a strict hard ceiling of 4,000 words.

### B. Short Revision Notes (.md)
- **Goal:** Fast, 3-5 minute active-recall retrieval artifact.
- **Content:** Keep only high-yield rules, formulas, comparisons, and exactly one canonical worked example per method family.
- **Self-Test Answer Privacy:** Self-test questions must NEVER disclose their answers in the same file. Answers must be kept in a separate answer-key file or hidden in a collapsed fold (such as `<details>` tags if supported, or omitted entirely).
- **Grounded Cautions:** Do not fabricate cautions, traps, or hooks. If none were explicitly taught by the teacher in the transcript, the section must be omitted.
- **Provenance:** Every short note must start with a context anchor matching:
  `From **[Lecture Title]**, answering: "[Core Question]"`

---

## 2. Subject Profiles

Every note must align structurally with its designated subject profile:

- **DBMS/Technical:** Focus on syntax, schema creation, query execution flows (e.g., `FROM` -> `WHERE` -> `GROUP BY` -> `HAVING`), and logical query evaluation.
- **Reasoning:** Focus on decision maps, boundary rules, direction/order conventions, and node family trees.
- **Quant:** Focus on method-selection rules, algebraic step-by-step layout, prime factorization lists, and shortcut checks.
- **English Grammar:** Focus on rule -> correct pattern -> incorrect/error contrast pairs. Do not list repetitive examples.
- **Vocabulary:** Focus on word clusters with synonyms, antonyms, tone, and contextual usage sentences.
- **GK/Theory:** Focus on comparative tables and cause-and-effect flowcharts.

---

## 3. Visual Association Policy

- **No Quota-Based Insertion:** Visuals must only be inserted if they contain board writing, slides, or diagrams that add distinct value to adjacent text.
- **Confidence-Based Matching:** Images must be associated with concept blocks or examples strictly based on timestamp matches or semantic/contextual OCR similarity.
- **No Positional Fallback:** Falling back to list indices or inserting "next unused image" is strictly banned.
- **Skipped-Visual Manifest:** If visual association confidence is below `0.75`, the visual must be omitted from the document, and its path and metadata must be logged in `logs/skipped_visuals.json` for review.

---

## 4. Callout Box Policy

- **Cap:** Maximum of 6 document-wide callout boxes (including traps, tricks, cautions, and quotes) per lecture notes document.
- **Provenance:** Every callout box must be directly derived from explicit teacher cautions or emphasis in the transcript. Auto-generation of speculative traps is prohibited.

---

## 5. Acceptance Thresholds (Audit Gates)

The note pipeline will be audited against:
1. **Mechanical Integrity:** All 22 original DOCX gates.
2. **Redundancy Score:** Checked by measuring sentence-level semantic similarity (threshold: 0.50).
3. **Word Budget:** Hard ceiling of 4,000 words for standard lectures.
4. **Short Note Integrity:** Audit the generated short note for no Devanagari, no answer leakage, correct context anchor, and word limits (300-500 words).
5. **Visual Association Audit:** Ensure all images in the document match the expected timestamps/contexts and check the skipped-visual log.

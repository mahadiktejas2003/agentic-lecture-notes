# System Audit Report: Lecture-Note Reconstruction Pipeline Bottlenecks & Omission Root Causes

## 1. Executive Summary & Core Conclusion
An exhaustive system-wide analysis of the lecture-note reconstruction pipeline has identified the exact technical and prompt bottlenecks that cause inconsistent, incomplete, or surface-level note generation.

The primary root cause of missing worked examples and empty fields is a **catastrophic schema key mismatch** between the LLM chunking prompt (which uses keys like `"scenario_or_problem"`, `"core_principles"`, and `"step_by_step_logic"`) and the Python consolidation and normalization code (which expects `"sentence"`, `"rule"`, and `"working"`). This mismatch causes:
1. **Silently dropping** subsequent examples during block merging (falsely classifying them as duplicates of `""`).
2. **Normalizing all text content to empty strings `""`** in the final `concept_block_map.json`, resulting in downstream rendering without examples.

Additional critical bottlenecks include:
- **Indentation flow bug in `generate_docx.py`** leading to double-rendering of traps, tricks, and student notes in custom flow layouts.
- **Regex word-filtering `r'\b[a-z]{4,}\b'`** in Jaccard similarity and OCR matching that strips digits, capitals, and single-letter math variables, causing mathematical slides and examples to be incorrectly flagged as duplicates and skipped.
- **Linguistic filter output token truncation** caused by sending the entire consolidated JSON block list at once.
- **Gate 15 character limit (2,000 chars)** and arbitrary `"First,"` word limits in `audit.py` that force the LLM to summarize/truncate explanations.
- **Answer omission for statement-style questions** due to a narrow `is_question` definition in the document builder.
- **Data loss in `<cloze>` compilation** where answers and hints are discarded by the docx builder.

---

## 2. Detailed Breakdown of Root Causes & Code Citations

### A. Catastrophic Schema Key Mismatches in `scripts/parse_transcript.py`
- **Location**: `scripts/parse_transcript.py` (lines 187-196) and (lines 535-560, 357-362, 787-801)
- **The Issue**:
  - The LLM chunking prompt defines the schema for examples using:
    - `"scenario_or_problem"`
    - `"core_principles"`
    - `"step_by_step_logic"`
    - `"teacher_analogies"`
  - The merging (`merge_two_blocks`), consolidation (`consolidate_blocks`), and normalization (`format_examples`) functions look up `"sentence"`, `"rule"`, and `"working"`.
- **Consequence**:
  - In `merge_two_blocks`: `e2.get("sentence", "")` evaluates to `""` for all items. The comparison `sent1.lower() == sent2.lower()` (which becomes `"" == ""`) evaluates to `True`, so all subsequent examples in overlapping chunks are marked as duplicates and discarded.
  - In the normalization loop (lines 787-801), keys `"sentence"`, `"rule"`, and `"working"` are looked up on the LLM-returned dict and evaluate to `""`, overwriting the final `concept_block_map.json` values with empty strings.

### B. Indentation & Flow Control Bug in `scripts/generate_docx.py`
- **Location**: `scripts/generate_docx.py` (lines 1573-1632)
- **The Issue**: Sequential blocks (traps, tricks, quotes, student notes) are indented with 8 spaces. This places them outside the sequential `else:` block (which ends on line 1572) and at the same level as the outer `for` loop.
- **Consequence**: These elements run unconditionally for every concept block. If a custom flow is defined and has already rendered these elements, they are rendered a second time at the end of the block.

### C. Alphanumeric Regex Filtering (`[a-z]{4,}`) Omit Math and Short Words
- **Location**: `scripts/generate_docx.py` (lines 38-39, 51-52) and `find_best_embedded_screenshot` (lines 885, 891)
- **The Issue**: Set evaluations for Jaccard and OCR similarity use:
  ```python
  w1 = set(re.findall(r'\b[a-z]{4,}\b', text1.lower()))
  ```
- **Consequence**: This strips out all numbers, uppercase variables, single-letter variables (`n`, `r`, `x`, `y`), and short operators (`add`, `mul`, `div`). Two distinct mathematical slides (e.g. `5P2` vs `6P3`) reduce to the identical set `{'example', 'find'}`, returning a Jaccard similarity of `1.0`. They are skipped as duplicate slides, causing massive content omissions.

### D. Post-Processing Linguistic Filter (Pass 3) Token Limits
- **Location**: `scripts/parse_transcript.py` (lines 432-484)
- **The Issue**: The entire JSON block array is sent to the LLM for Hinglish cleaning in a single prompt.
- **Consequence**: For long lectures, the JSON exceeds output token limits (typically 2,048 or 4,096 tokens). The LLM either cuts off (causing JSON parse failure and fallback to uncleaned text) or silently summarizes/compresses the explanations and examples to fit the output limit.

### E. Gate 15 Conciseness Check in `scripts/audit.py`
- **Location**: `scripts/audit.py` (lines 228-231)
- **The Issue**: The gate checks:
  ```python
  if len(expl) > 2000 or expl.count('First,') > 1:
  ```
- **Consequence**: A 2,000-character limit forces the LLM to summarize complex explanations to pass the audit. The `"First,"` limit forces awkward wording and prevents multi-step explanations.

### F. Statement-Style Question Answer Omission
- **Location**: `scripts/generate_docx.py` (lines 1261 and 1492)
- **The Issue**: Answers are printed only if `is_question` is `True`. `is_question` evaluates to `False` for statement-style prompts (e.g., *"Find the number of ways..."*).
- **Consequence**: Answer blocks for statement worked examples are silently skipped.

### G. Cloze Deletion Information Loss
- **Location**: `scripts/generate_docx.py` (lines 351-353)
- **The Issue**: `<cloze>` tags are rendered as blue underlined text, but the `answer` and `hint` attributes are completely discarded.
- **Consequence**: The compiled document contains empty `[......]` blanks with no answer key or hints generated anywhere, burying the information in the JSON file.

### H. Banned Attributions scanned inside Quotes
- **Location**: `scripts/audit.py` (lines 173-176)
- **The Issue**: Banned attributions scan all paragraphs in the document.
- **Consequence**: Verbatim teacher quotes containing conversational filler (e.g., *"let's look"*) trigger Gate 1 failures, causing conflicts with the Source Fidelity Protocol.

---

## 3. Recommended Architectural Remediation

1. **Schema Standardization**: Update the LLM prompting schema inside `scripts/parse_transcript.py` to use `"sentence"`, `"rule"`, and `"working"` directly to match the Python parser.
2. **Correct Indentation**: Indent `generate_docx.py` lines 1573-1632 under the `else:` block so that they only execute when no custom flow is defined.
3. **Regex Expansion**: Change Jaccard tokenization regex to `\b[a-zA-Z0-9_\-\+]{2,}\b` to preserve numbers and variables during deduplication.
4. **Linguistic Filter Batching**: Modify `apply_linguistic_filter` to clean blocks individually or in small batches instead of passing the entire array at once.
5. **Gate 15 Relaxation**: Remove the character and `"First,"` limit in `audit.py` to allow detailed, un-summarized explanations.
6. **Loosen `is_question` Answer Check**: Print the answer block unconditionally if `ans_text` is present.
7. **Cloze Answer Key**: Extract cloze answers and hints and compile them into a styled Appendix section at the end of the document.
8. **Banned Attribution Quote Exclusions**: Exclude text inside quote-styled paragraphs from the banned attributions search.
9. **Reduce Visual dhash Threshold**: Decrease visual deduplication similarity diff threshold to `2` or `3` in `insert_image_for_vm`.

#!/usr/bin/env python3
import os
import sys
import json
import re
import time
import argparse
import logging
import subprocess
import shutil
import math

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Import verify_density locally
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from verify_density import verify_density
except ImportError:
    verify_density = None

def timestamp_to_seconds(ts_str):
    """Parses timestamp format (HH:MM:SS, MM:SS, or SS) to total seconds."""
    if not ts_str:
        return 0.0
    ts_str = ts_str.strip().rstrip('*').replace(',', '.')
    parts = ts_str.split(':')
    try:
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = int(parts[0]), float(parts[1])
            return m * 60 + s
        else:
            return float(parts[0])
    except Exception:
        return 0.0

def seconds_to_timestamp(sec):
    """Converts seconds to HH:MM:SS format."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_srt(srt_path):
    """Parses an SRT file into timestamped entries."""
    if not os.path.exists(srt_path):
        logger.error(f"SRT file not found: {srt_path}")
        return []
    
    with open(srt_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read().replace('\r\n', '\n')
        
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\n(.*?)(?=\n\d+\n|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    entries = []
    for m in matches:
        idx = int(m[0])
        start = timestamp_to_seconds(m[1])
        end = timestamp_to_seconds(m[2])
        text = m[3].strip()
        entries.append({
            'index': idx,
            'start': start,
            'end': end,
            'text': text,
            'start_str': m[1].split(',')[0],
            'end_str': m[2].split(',')[0]
        })
    return entries

def call_antigravity_chat(prompt):
    """Calls the antigravity chat CLI command and extracts JSON from the response."""
    cli_path = os.environ.get("ANTIGRAVITY_CLI_PATH") or shutil.which("antigravity") or "/Users/tejasmahadik/.gemini/antigravity/bin/antigravity"
    if not os.path.exists(cli_path):
        logger.error(f"Antigravity CLI not found at: {cli_path}")
        return None
        
    logger.info(f"Calling Antigravity CLI...")
    try:
        result = subprocess.run([cli_path, "chat", prompt], capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            logger.error(f"Antigravity CLI returned exit code {result.returncode}. Error: {result.stderr}")
            return None
            
        output = result.stdout
        
        # 1. Look for ```json ... ```
        match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip(), strict=False)
            except Exception as je:
                logger.warning(f"Failed to parse JSON inside markdown block: {je}")
                
        # 2. Look for outer {...}
        first_brace = output.find('{')
        last_brace = output.rfind('}')
        if first_brace != -1 and last_brace != -1:
            try:
                return json.loads(output[first_brace:last_brace+1], strict=False)
            except Exception as je:
                logger.warning(f"Failed to parse JSON from outer braces: {je}")
                
        # 3. Strip CLI prefix lines and check if whole string is JSON
        clean_lines = [line for line in output.split('\n') if not line.startswith('[Antigravity CLI]')]
        clean_output = '\n'.join(clean_lines).strip()
        try:
            return json.loads(clean_output, strict=False)
        except Exception as je:
            logger.error(f"All JSON parsing attempts failed. Raw output: {output[:500]}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("Antigravity CLI call timed out (600s).")
        return None
    except Exception as e:
        logger.error(f"Failed to execute Antigravity CLI: {e}")
        return None

def call_antigravity_chat_raw(prompt):
    """Calls the antigravity chat CLI command and returns the raw output text."""
    cli_path = os.environ.get("ANTIGRAVITY_CLI_PATH") or shutil.which("antigravity") or "/Users/tejasmahadik/.gemini/antigravity/bin/antigravity"
    if not os.path.exists(cli_path):
        logger.error(f"Antigravity CLI not found at: {cli_path}")
        return None
        
    logger.info(f"Calling Antigravity CLI (raw text mode)...")
    try:
        result = subprocess.run([cli_path, "chat", prompt], capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            logger.error(f"Antigravity CLI returned exit code {result.returncode}. Error: {result.stderr}")
            return None
            
        output = result.stdout
        # Strip CLI prefix lines
        clean_lines = [line for line in output.split('\n') if not line.startswith('[Antigravity CLI]')]
        return '\n'.join(clean_lines).strip()
    except Exception as e:
        logger.error(f"Failed to execute Antigravity CLI in raw mode: {e}")
        return None

def clean_devanagari_from_text(text):
    if not isinstance(text, str):
        return text
    # Check if there is any Devanagari character
    if not re.search(r'[\u0900-\u097F]', text):
        return text
        
    logger.info(f"Devanagari character detected in text: '{text[:100]}...'. Running dedicated translation cleaning...")
    prompt = f"""You are a translator and text cleaner.
Your task is to translate and clean any Devanagari (Hindi/Hinglish script) words or phrases in the following text into formal Topper-Grade English.
Keep all other English words, punctuation, formatting, and mathematical equations intact. Do NOT summarize or shorten the text. Only translate the Devanagari words.

Text to clean:
{text}

Respond with ONLY the translated text. Do NOT add any introductory or concluding comments, and do NOT wrap it in quotes or markdown formatting blocks unless they are already in the source text."""

    res = call_antigravity_chat_raw(prompt)
    if res and isinstance(res, str) and res.strip():
        cleaned_text = res.strip()
        # Verify the LLM didn't return an empty response or error message containing Devanagari
        if not re.search(r'[\u0900-\u097F]', cleaned_text):
            logger.info("Successfully cleaned Devanagari characters via LLM translation.")
            return cleaned_text
            
    logger.warning("LLM cleanup failed or returned Devanagari. Programmatically removing Devanagari characters as fallback.")
    cleaned = re.sub(r'[\u0900-\u097F]', '', text)
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def clean_dict_fields(val):
    if isinstance(val, dict):
        return {k: clean_dict_fields(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [clean_dict_fields(v) for v in val]
    elif isinstance(val, str):
        return clean_devanagari_from_text(val)
    else:
        return val

def process_chunk(entries, chunk_index, total_chunks, slide_data, continuity_context=""):
    """Processes a single 10-minute overlapping chunk using the Antigravity CLI."""
    start_time = entries[0]['start']
    end_time = entries[-1]['end']
    start_str = seconds_to_timestamp(start_time)
    end_str = seconds_to_timestamp(end_time)
    
    logger.info(f"Processing Chunk {chunk_index}/{total_chunks} ({start_str} to {end_str})...")
    
    # Format transcript text
    transcript_lines = []
    for entry in entries:
        transcript_lines.append(f"[{entry['start_str']}] {entry['text']}")
    transcript_text = "\n".join(transcript_lines)
    
    # Filter slide and reference data for this chunk's time window
    relevant_slides = []
    for s in slide_data:
        ts = timestamp_to_seconds(s.get('discussed_at', ''))
        if start_time <= ts <= end_time:
            relevant_slides.append(f"Slide {s.get('slide_number')}: {s.get('ocr_text', '')}")
            
    slides_section = ""
    if relevant_slides:
        slides_section = "### Slide Content for this timeframe:\n" + "\n".join(relevant_slides) + "\n\n"

    continuity_section = ""
    if continuity_context:
        continuity_section = f"### CONTEXT FROM PREVIOUS LECTURES/PARTS:\n{continuity_context}\n\nUse this context to maintain consistent terminology and notation, link related concepts back to previous parts, and avoid repeating definitions that were already covered in detail.\n\n"

    prompt = f"""
You are the Transcript Mapping Specialist Subagent.
Analyze the following lecture transcript segment from {start_str} to {end_str}.
Your task is to extract all key teaching concepts, rules, formulas, examples, visual moments, traps, and exercises discussed in this segment. Synthesize verbose teacher explanations into concise, exam-ready study notes. Preserve all FACTS and RULES but express them EFFICIENTLY using bullet points and short paragraphs.

--- TRANSCRIPT SEGMENT ---
{transcript_text}
-------------------------

{slides_section}
{continuity_section}Based on this transcript, produce a JSON object with a single key "blocks", containing a list of concept blocks matching this exact schema.
CRITICAL JSON SYNTAX RULE: Double quotes (") must ONLY be used for JSON keys and string boundaries. Inside JSON string values themselves, you MUST use single quotes (e.g. 'the') and never unescaped double quotes.

{{
  "blocks": [
    {{
      "title": "Slide title or explicit lecture heading. You may create descriptive sub-headings if a slide contains multiple distinct sub-concepts.",
      "explanation": "High-level explanation, why the rule exists, or real-world analogy. Explain the context or logical flow here.",
      "concept_explanations": [
        {{
          "concept_name": "Name of the sub-concept or theory part",
          "detailed_explanation": "A concise 2-4 sentence explanation of the concept. State the rule, its purpose, and one key analogy if given. Use bullet points for multi-part explanations. Max 100 words."
        }}
      ],
      "concepts": [
        {{
          "term": "Term, rule, or formula name",
          "definition": "Definition, description of the rule, or formula. Apply **bolding** to key terms. Apply color highlighting using <highlight color='BLUE'>text</highlight> or <highlight color='RED'>text</highlight> for critical rules, standout facts, or warnings. Do NOT use yellow or green."
        }}
      ],
      "examples": [
        {{
          "timestamp": "HH:MM:SS", // Timestamp at the END of the example discussion (solved-state timestamp)
          "sentence": "The complete word problem, scenario, or equation discussed",
          "rule": "The specific rule or theorem applied (1-2 sentences max)",
          "working": "Step-by-step solution in concise numbered steps. Use elimination tables for MCQ-type problems. Max 150 words.",
          "student_notes": "Key student doubts or warning points (1-2 sentences). Preserve teacher's best analogy if any. DO NOT use Hindi/Hinglish."
        }}
      ],
      "visual_moments": [
        {{
          "timestamp": "HH:MM:SS", // Must match the solved-state timestamp of the example
          "type": "board",
          "description": "Short description of the board/slide content corresponding to the example"
        }}
      ],
      "teacher_quotes": [
        "Maximum 5 most impactful teacher statements per block. Paraphrase into formal English. Only preserve verbatim if the exact wording is a definition or rule."
      ],
      "traps": [
        "Common student mistakes (1 sentence each, max 5)"
      ],
      "tricks": [
        "Exam shortcuts or tips (1 sentence each, max 5)"
      ],
      "exercise_questions": [
        "Homework, practice, or unsolved questions assigned or discussed"
      ]
    }}
  ]
}}

STRICT RULES:
1. DEEP EXTRACTION (TWO-PASS): Before outputting the JSON, use a `<think>` block to list out all raw insights, formulas, real-world analogies, and examples found in the chunk. Then build the JSON.
1b. SMART SYNTHESIS: Preserve all facts, formulas, rules, and worked examples. Condense verbose teacher explanations into concise bullet-point study notes. Never lose information — but never repeat it or pad it with filler prose either. Target concise, exam-ready output.
2. EXTRACT EVERYTHING: Extract EVERY SINGLE example problem and question discussed in the transcript segment. Group continuous back-to-back examples under a single visual moment if they belong to the same board state to avoid duplicate screenshots.
3. ENGLISH ENFORCEMENT: Write purely in English. Do NOT preserve the teacher's Hinglish/bilingual conversational filler, BUT YOU MUST PRESERVE the intuitive real-world analogies translated into clear English. 
4. BOLDING & MARKDOWN: Aggressively use **bolding** for key terms, definitions, and formulas. Use single asterisks (like *plays*) for italics.
5. TRANSCRIPT FIDELITY: Your primary source of truth is the verbal transcript, not the slides. Extract the teaching logic, examples, and key analogies concisely. Prefer bullet points over prose paragraphs. Do not write generic slide summaries, but also do not write textbook-length essays — write study notes.
6. SYLLOGISM SPECIAL RULES (ONLY WHEN RELEVANT): Apply the following rules and interpretations ONLY if the corresponding syllogism concept or example is discussed in the transcript segment. Do NOT inject them if the segment does not cover these concepts:
   - Exclusivity of "Only A are B": Translate to "All B are A". B can NEVER intersect or have any relation with any other set C except A. Any possibility statement asserting an overlap between B and C must be marked as FALSE.
   - Surety vs. Possibility Rule: If a relationship is definitely true (Surety), any corresponding possibility conclusion (e.g., "X being Y is a possibility" or "X can be Y") is strictly FALSE.
   - "Only a few A are B" Dual Constraint: Map as both "Some A are B" (positive intersection) and "Some A are not B" (negative restriction). "All A can be B is a possibility" is FALSE (some A must remain outside B). "All B can be A is a possibility" is TRUE.
   - Either-Or Condition Constraints: Active only when both conclusions have the same subject and predicate, both are individually false (failed under certainty), and they form a complementary pair (e.g. Some + No). If a possibility option becomes true and a negative option is false, Either-Or does NOT apply.
   - Quantifier Equivalents: Treat "At least" and "Many" as exact synonyms of "Some".
   - Option Equivalents: Treat "Neither I nor II follows", "Neither follows", and "Both do not follow" as identical options.
7. PERMUTATION & COMBINATION SPECIAL RULES (ONLY WHEN RELEVANT): Apply the following rules and interpretations ONLY if the corresponding P&C concept or example is discussed in the transcript segment. Do NOT inject them if the segment does not cover these concepts:
   - Probability link: Explain how P&C directly connects to Probability.
   - Examiner priority: Acc to last 5 years, Combinations questions are the primary priority, followed by Permutations.
   - Time saving: Highlight that mastering this topic saves time.
   - Basic counting principles over formulas: Highlight that no formulas need to be remembered (the number of formulas to memorize is zero); focus on basic counting principles (addition for OR/cases, multiplication for AND/continuous process).
   - Method 2 Prominence: For restricted permutations (always occur together, always included, always excluded), make Method 2 (Without Formula) the primary explanation. Show the formula method as secondary.
   - For "always occur together": treat grouped items as a single entity, arrange the new entities, and multiply by the internal arrangements of the grouped items.
   - For "always included": first select/arrange the x fixed items into the r seats (rPx ways), then select/arrange the remaining n-x items in the remaining r-x seats ((n-x)P(r-x) ways).
   - For "always excluded": completely forget/ignore the excluded items, and select/arrange from the remaining n-x items.
   - "Vowels do not sit together" (total unrestricted arrangements minus vowels together arrangements) vs "No two vowels sit together" (Gap Method: place consonants first, count the gaps which is consonants + 1, and place/arrange vowels in the gaps). They are completely different.
   - Rings and fingers: Identify fixed positions (fingers) and moving items (rings). Explain why at least 1 ring per finger in 3 rings/4 fingers is impossible (results in 0 ways).
   - Circular permutations: Standard is (n-1)!. Necklace/Garland (clockwise and anti-clockwise are identical) is (n-1)! / 2. Identical items is 1. Gaps in circular seating of n items is exactly n gaps (not n+1).
   - Combination: Selection of items where order doesn't matter, compared to permutation (arrangement where order matters).
8. JSON FORMAT: Enclose your final JSON inside ```json ... ``` tags.
9. CONCEPT BLOCK CONSOLIDATION: You must strictly align all concept block titles with actual slide titles or explicit lecture headings. Do NOT invent arbitrary, custom, or extra concept block titles or categories that are not explicitly present in the lecture slides or transcript. Group related content under these primary topic blocks rather than creating tiny or custom-named blocks.
10. STRICT FIDELITY CONSTRAINT (NO HALLUCINATIONS / ALTERATIONS): You must ONLY extract concepts, formulas, rules, examples, and definitions that are explicitly taught or mentioned in the provided transcript segment. Do NOT invent, assume, or add any extra topics, theories, rules, or questions that were not discussed by the teacher, even if they are standard academic concepts. You must NOT alter the facts, formulas, or examples taught by the teacher. The notes must represent a 100% faithful reconstruction of the actual lecture segment, nothing more and nothing less.
"""
    
    # Retry loop
    for attempt in range(3):
        res = call_antigravity_chat(prompt)
        if res and isinstance(res, dict) and "blocks" in res:
            # Add segment start/end timestamps to each block's temporary metadata
            for block in res["blocks"]:
                block["_chunk_start"] = start_time
                block["_chunk_end"] = end_time
            return res["blocks"]
        logger.warning(f"Attempt {attempt+1} failed to parse or return valid JSON. Retrying...")
        if attempt < 2:
            time.sleep(2 ** attempt)
        
    logger.error(f"Failed to process chunk {chunk_index} after 3 attempts.")
    return []

def consolidate_blocks(blocks):
    """Groups blocks by title (fuzzy matching / substring matching) and merges their attributes."""
    if not blocks:
        return []
    
    import difflib
    consolidated = []
    
    for block in blocks:
        title = block.get("title", "").strip()
        if not title:
            continue
        
        # Clean title for comparison
        title_clean = re.sub(r'[^a-zA-Z0-9\s]', '', title).lower().strip()
        
        # Look for a similar existing block to merge into
        matched_idx = None
        for idx, cb in enumerate(consolidated):
            existing_title = cb["title"]
            existing_clean = re.sub(r'[^a-zA-Z0-9\s]', '', existing_title).lower().strip()
            
            # Match conditions:
            # 1. Exact match (cleaned)
            # 2. Substring match if long enough (>= 8 chars)
            # 3. Fuzzy similarity score >= 0.75
            is_match = False
            if title_clean == existing_clean:
                is_match = True
            elif len(title_clean) >= 8 and len(existing_clean) >= 8:
                if title_clean in existing_clean or existing_clean in title_clean:
                    is_match = True
            
            if not is_match:
                ratio = difflib.SequenceMatcher(None, title_clean, existing_clean).ratio()
                if ratio >= 0.75:
                    is_match = True
                    
            if is_match:
                matched_idx = idx
                break
                
        if matched_idx is None:
            # Create new block
            merged_block = {
                "title": title,
                "explanation": block.get("explanation", ""),
                "_chunk_start": block.get("_chunk_start"),
                "_chunk_end": block.get("_chunk_end"),
                "concepts": list(block.get("concepts", [])),
                "examples": list(block.get("examples", [])),
                "visual_moments": list(block.get("visual_moments", [])),
                "teacher_quotes": list(block.get("teacher_quotes", [])),
                "traps": list(block.get("traps", [])),
                "tricks": list(block.get("tricks", [])),
                "exercise_questions": list(block.get("exercise_questions", []))
            }
            consolidated.append(merged_block)
        else:
            existing = consolidated[matched_idx]
            
            # Prefer shorter title if it matches a clean heading
            if len(title) < len(existing["title"]) and len(title) > 5:
                existing["title"] = title
                
            # Merge timeframes
            if block.get("_chunk_start") is not None:
                if existing["_chunk_start"] is None:
                    existing["_chunk_start"] = block["_chunk_start"]
                else:
                    existing["_chunk_start"] = min(existing["_chunk_start"], block["_chunk_start"])
            
            if block.get("_chunk_end") is not None:
                if existing["_chunk_end"] is None:
                    existing["_chunk_end"] = block["_chunk_end"]
                else:
                    existing["_chunk_end"] = max(existing["_chunk_end"], block["_chunk_end"])
                    
            # Concatenate explanations
            exp1 = existing.get("explanation", "").strip()
            exp2 = block.get("explanation", "").strip()
            if exp2 and exp2 != exp1:
                if exp1:
                    if exp2 not in exp1:
                        existing["explanation"] = exp1 + " " + exp2
                else:
                    existing["explanation"] = exp2
                    
            # Deduplicate concepts by 'term' (case-insensitive)
            existing_terms = {c.get("term", "").strip().lower() for c in existing["concepts"] if c.get("term")}
            for c in block.get("concepts", []):
                term = c.get("term", "").strip()
                if term and term.lower() not in existing_terms:
                    existing["concepts"].append(c)
                    existing_terms.add(term.lower())
                    
            # Deduplicate examples by 'sentence' (case-insensitive)
            existing_sentences = {e.get("sentence", e.get("scenario_or_problem", "")).strip().lower() for e in existing["examples"] if e.get("sentence") or e.get("scenario_or_problem")}
            for e in block.get("examples", []):
                sent = e.get("sentence", e.get("scenario_or_problem", "")).strip()
                if sent and sent.lower() not in existing_sentences:
                    existing["examples"].append(e)
                    existing_sentences.add(sent.lower())
                    
            # Deduplicate visual_moments by (timestamp + type)
            existing_visuals = {
                (v.get("timestamp", "").strip(), v.get("type", "").strip().lower())
                for v in existing["visual_moments"]
            }
            for v in block.get("visual_moments", []):
                ts = v.get("timestamp", "").strip()
                vtype = v.get("type", "").strip().lower()
                if (ts, vtype) not in existing_visuals:
                    existing["visual_moments"].append(v)
                    existing_visuals.add((ts, vtype))
                    
            # Deduplicate lists of strings
            def merge_str_lists(list1, list2):
                seen = {item.strip().lower() for item in list1 if item}
                for item in list2:
                    if item and item.strip().lower() not in seen:
                        list1.append(item)
                        seen.add(item.strip().lower())
            
            merge_str_lists(existing["teacher_quotes"], block.get("teacher_quotes", []))
            merge_str_lists(existing["traps"], block.get("traps", []))
            merge_str_lists(existing["tricks"], block.get("tricks", []))
            merge_str_lists(existing["exercise_questions"], block.get("exercise_questions", []))
            
    consolidated.sort(key=lambda x: x.get("_chunk_start") if x.get("_chunk_start") is not None else 0.0)
    return consolidated

def inject_reference_notes(blocks, ref_data):
    if not ref_data:
        return blocks
    logger.info("Running Pass 2: Injecting reference notes (block-by-block)...")
    
    updated_blocks = []
    for idx, block in enumerate(blocks):
        chunk_start = block.get("_chunk_start")
        chunk_end = block.get("_chunk_end")
        
        if chunk_start is None or chunk_end is None:
            relevant_ref = ref_data
        else:
            relevant_ref = []
            for r in ref_data:
                discussed_at = r.get("discussed_at")
                if discussed_at:
                    try:
                        ts = timestamp_to_seconds(discussed_at)
                        if chunk_start <= ts <= chunk_end:
                            relevant_ref.append(r)
                    except Exception:
                        pass
                        
        if not relevant_ref:
            updated_blocks.append(block)
            continue
            
        logger.info(f"Injecting {len(relevant_ref)} reference notes into block '{block.get('title')}' (block {idx+1}/{len(blocks)})...")
        
        prompt = f"""You MUST respond with ONLY valid JSON and nothing else. No explanations, no commentary — ONLY a raw JSON object.

REFERENCE NOTES FOR THIS BLOCK (user's manual handwritten notes):
{json.dumps(relevant_ref, indent=1)}

CONCEPT BLOCK TO UPDATE:
{json.dumps(block, indent=1)}

TASK: Inject any missing rules, handwritten examples, or specific analogies from the reference notes into the concept block. Match the keys in the concept block (e.g. concepts, examples, visual_moments, teacher_quotes, traps, tricks, student_notes, boundary_questions). Return the updated concept block.

OUTPUT FORMAT (respond with ONLY this JSON):
{{
  ... updated concept block fields ...
}}"""
        res = call_antigravity_chat(prompt)
        if res and isinstance(res, dict):
            # Preserve internal block metadata keys
            for key, val in res.items():
                if val is not None:
                    if isinstance(val, (list, dict, str)):
                        if len(val) > 0:
                            block[key] = val
                    else:
                        block[key] = val
            if chunk_start is not None:
                block["_chunk_start"] = chunk_start
            if chunk_end is not None:
                block["_chunk_end"] = chunk_end
                
        updated_blocks.append(block)
    return updated_blocks


def apply_linguistic_filter(blocks):
    if not blocks:
        return []
    logger.info("Running Pass 3: Post-Processing Linguistic Filter...")
    
    # Process blocks in small batches of 1-2 blocks to prevent token limit truncation and silent summarization
    batch_size = 1
    
    for idx in range(0, len(blocks), batch_size):
        batch = blocks[idx:idx+batch_size]
        input_blocks = [dict(b) for b in batch]
        
        prompt = f"""You are the Post-Processing Linguistic Filter. You MUST respond with ONLY valid JSON and nothing else. No explanations, no commentary — ONLY a raw JSON object.

INPUT — Concept blocks:
{json.dumps(input_blocks, indent=1)}

TASK: Clean all text fields in the blocks to satisfy Topper-Grade English. Rules:
1. STRICT DEVANAGARI BAN: Translate any Devanagari script (Hindi/Hinglish characters) to English or remove it.
2. HINGLISH CLEANUP: Translate Hinglish conversational filler (e.g. 'hai', 'toh', 'ki', 'bhi', 'aur') from explanations, workings, and definitions into formal English.
3. TEACHER QUOTES: Clean direct quotes (`teacher_quotes`) of Hinglish filler and translate them into formal Topper-Grade English, UNLESS a specific quote uses a very unique, irreplaceable Hindi analogy that is strictly required to explain the concept. Otherwise, direct quotes must be translated.
4. NO SUMMARIZATION (CRITICAL): You must preserve 100% of the detail, formulas, examples, step-by-step workings, and explanations. Do not summarize, shorten, or simplify the explanation text. Only translate Devanagari and Hinglish filler to formal English while keeping the exact same depth and length of information.
5. SCHEMA COMPLIANCE: Keep the JSON structure exactly identical to the input.

OUTPUT FORMAT (respond with ONLY this JSON):
{{"blocks": [...]}}"""

        max_retries = 2
        success = False
        for attempt in range(max_retries + 1):
            res = call_antigravity_chat(prompt)
            if res:
                new_blocks = []
                if isinstance(res, dict) and "blocks" in res:
                    new_blocks = res["blocks"]
                elif isinstance(res, list):
                    new_blocks = res
                
                if new_blocks and len(new_blocks) == len(batch):
                    logger.info(f"Linguistic filter batch {idx//batch_size + 1} succeeded on attempt {attempt+1}")
                    for orig_b, new_b in zip(batch, new_blocks):
                        orig_b["title"] = new_b.get("title", orig_b.get("title"))
                        orig_b["explanation"] = new_b.get("explanation", orig_b.get("explanation"))
                        orig_b["concepts"] = new_b.get("concepts", orig_b.get("concepts"))
                        orig_b["examples"] = new_b.get("examples", orig_b.get("examples"))
                        orig_b["teacher_quotes"] = new_b.get("teacher_quotes", orig_b.get("teacher_quotes"))
                        orig_b["traps"] = new_b.get("traps", orig_b.get("traps"))
                        orig_b["tricks"] = new_b.get("tricks", orig_b.get("tricks"))
                        if "student_notes" in new_b:
                            orig_b["student_notes"] = new_b["student_notes"]
                        if "method2" in new_b:
                            orig_b["method2"] = new_b["method2"]
                    success = True
                    break
    return blocks

def check_sentence_similarity(s1, s2):
    if not s1 or not s2:
        return 0.0
    w1 = set(re.findall(r'\b[a-z0-9]+\b', s1.lower()))
    w2 = set(re.findall(r'\b[a-z0-9]+\b', s2.lower()))
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / len(w1 | w2)

def merge_two_blocks(b1, b2, consolidated_title=None):
    title = consolidated_title or b1.get("title", "")
    
    exp1 = b1.get("explanation", "").strip()
    exp2 = b2.get("explanation", "").strip()
    if exp1 == exp2:
        explanation = exp1
    elif exp2 in exp1:
        explanation = exp1
    elif exp1 in exp2:
        explanation = exp2
    else:
        explanation = exp1 + "\n\n" + exp2
        
    start1 = b1.get("_chunk_start")
    start2 = b2.get("_chunk_start")
    if start1 is None:
        chunk_start = start2
    elif start2 is None:
        chunk_start = start1
    else:
        chunk_start = min(start1, start2)
        
    end1 = b1.get("_chunk_end")
    end2 = b2.get("_chunk_end")
    if end1 is None:
        chunk_end = end2
    elif end2 is None:
        chunk_end = end1
    else:
        chunk_end = max(end1, end2)
        
    # Merge concept explanations
    concept_explanations = list(b1.get("concept_explanations", []))
    seen_exp_concepts = {ce.get("concept_name", "").strip().lower() for ce in concept_explanations if ce.get("concept_name")}
    for ce in b2.get("concept_explanations", []):
        name = ce.get("concept_name", "").strip().lower()
        if name not in seen_exp_concepts:
            concept_explanations.append(ce)
            seen_exp_concepts.add(name)
        else:
            for existing_ce in concept_explanations:
                if existing_ce.get("concept_name", "").strip().lower() == name:
                    e_detail = existing_ce.get("detailed_explanation", "").strip()
                    n_detail = ce.get("detailed_explanation", "").strip()
                    if n_detail and n_detail.lower() not in e_detail.lower():
                        existing_ce["detailed_explanation"] = (e_detail + "\n\n" + n_detail).strip()
                    break
        
    concepts = list(b1.get("concepts", []))
    concept_map = {c.get("term", "").strip().lower(): c for c in concepts if c.get("term")}
    for c in b2.get("concepts", []):
        term = c.get("term", "").strip().lower()
        if term not in concept_map:
            concepts.append(c)
            concept_map[term] = c
        else:
            existing_def = concept_map[term].get("definition", "").strip()
            new_def = c.get("definition", "").strip()
            if new_def and new_def.lower() not in existing_def.lower():
                concept_map[term]["definition"] = (existing_def + "\nAlso: " + new_def).strip()
            
    examples = list(b1.get("examples", []))
    for e2 in b2.get("examples", []):
        sent2 = e2.get("sentence", e2.get("scenario_or_problem", "")).strip()
        is_dup = False
        for i, e1 in enumerate(examples):
            sent1 = e1.get("sentence", e1.get("scenario_or_problem", "")).strip()
            if sent1.lower() == sent2.lower() or check_sentence_similarity(sent1, sent2) >= 0.98:
                is_dup = True
                w1 = e1.get("working", e1.get("step_by_step_logic", "")).strip()
                w2 = e2.get("working", e2.get("step_by_step_logic", "")).strip()
                if w2 and w2.lower() not in w1.lower():
                    e1["working"] = (w1 + "\n\n" + w2).strip()
                
                r1 = e1.get("rule", e1.get("core_principles", "")).strip()
                r2 = e2.get("rule", e2.get("core_principles", "")).strip()
                if r2 and r2.lower() not in r1.lower():
                    e1["rule"] = (r1 + " | " + r2).strip(" | ")
                
                sn1 = e1.get("student_notes", "").strip()
                sn2 = e2.get("student_notes", "").strip()
                if sn2 and sn2.lower() not in sn1.lower():
                    e1["student_notes"] = (sn1 + "\n\n" + sn2).strip()
                
                m1 = e1.get("method2", "").strip()
                m2 = e2.get("method2", "").strip()
                if m2 and m2.lower() not in m1.lower():
                    e1["method2"] = (m1 + "\n\n" + m2).strip()

                c1 = e1.get("cloze_text", "").strip()
                c2 = e2.get("cloze_text", "").strip()
                if c2 and c2.lower() not in c1.lower():
                    e1["cloze_text"] = (c1 + " " + c2).strip()

                cues1 = list(e1.get("cornell_cues", []))
                cues2 = e2.get("cornell_cues", [])
                for cue in cues2:
                    if cue and cue.strip().lower() not in {c.strip().lower() for c in cues1}:
                        cues1.append(cue)
                e1["cornell_cues"] = cues1

                if not e1.get("srs_tag") and e2.get("srs_tag"):
                    e1["srs_tag"] = e2.get("srs_tag")

                ana1 = e1.get("teacher_analogies", "").strip()
                ana2 = e2.get("teacher_analogies", "").strip()
                if ana2 and ana2.lower() not in ana1.lower():
                    e1["teacher_analogies"] = (ana1 + "\n\n" + ana2).strip()
                break
        if not is_dup:
            examples.append(e2)
            
    visuals = list(b1.get("visual_moments", []))
    seen_visuals = {(v.get("timestamp", "").strip(), v.get("type", "").strip().lower()) for v in visuals}
    for v in b2.get("visual_moments", []):
        ts = v.get("timestamp", "").strip()
        vt = v.get("type", "").strip().lower()
        if (ts, vt) not in seen_visuals:
            visuals.append(v)
            seen_visuals.add((ts, vt))
            
    def merge_lists(l1, l2):
        res = list(l1)
        seen = {item.strip().lower() for item in res if item}
        for item in l2:
            if item and item.strip().lower() not in seen:
                res.append(item)
                seen.add(item.strip().lower())
        return res
        
    quotes = merge_lists(b1.get("teacher_quotes", []), b2.get("teacher_quotes", []))
    traps = merge_lists(b1.get("traps", []), b2.get("traps", []))
    tricks = merge_lists(b1.get("tricks", []), b2.get("tricks", []))
    exercises = merge_lists(b1.get("exercise_questions", []), b2.get("exercise_questions", []))
    boundary_questions = merge_lists(b1.get("boundary_questions", []), b2.get("boundary_questions", []))
    student_notes = merge_lists(b1.get("student_notes", []), b2.get("student_notes", []))
    
    return {
        "title": title,
        "explanation": explanation,
        "concept_explanations": concept_explanations,
        "_chunk_start": chunk_start,
        "_chunk_end": chunk_end,
        "concepts": concepts,
        "examples": examples,
        "visual_moments": visuals,
        "teacher_quotes": quotes,
        "traps": traps,
        "tricks": tricks,
        "exercise_questions": exercises,
        "boundary_questions": boundary_questions,
        "student_notes": student_notes
    }

def consolidate_blocks_llm(blocks, slide_data):
    if not blocks:
        return []
    logger.info("Running Pass 1.5: Consolidating concept blocks...")
    
    light_blocks = []
    for idx, b in enumerate(blocks):
        light_blocks.append({
            "index": idx,
            "title": b.get("title", ""),
            "explanation": b.get("explanation", "")[:200]
        })
        
    prompt = f"""You are the Concept Block Consolidator. You MUST respond with ONLY valid JSON and nothing else. No explanations, no commentary — ONLY a raw JSON object.
    
    INPUT — Raw concept blocks:
    {json.dumps(light_blocks, indent=1)}
    
    SLIDE HEADINGS for alignment:
    {json.dumps([{"slide": s.get("slide_number"), "title": s.get("ocr_text","")[:100]} for s in slide_data], indent=1)}
    
    TASK: Aggressively merge redundant and overlapping blocks. If two blocks cover >50% overlapping concepts or the same topic area, MERGE them. 
    TARGET: Maximum 5-7 concept blocks for the entire lecture. Each block must have a UNIQUE focus — no two blocks should cover the same topic. Align titles with actual slide headings.
    CRITICAL: Err on the side of MERGING rather than keeping separate. Fewer, richer blocks are better than many thin, overlapping ones.
    
    OUTPUT FORMAT (respond with ONLY this JSON structure):
    {{
      "mappings": [
        {{
          "consolidated_title": "Slide-Aligned Title",
          "indices": [0, 2]
        }}
      ]
    }}"""
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        res = call_antigravity_chat(prompt)
        if res and isinstance(res, dict) and "mappings" in res:
            logger.info(f"Consolidation mapping succeeded on attempt {attempt+1}: {len(res['mappings'])} merge groups")
            
            consolidated = []
            merged_indices = set()
            
            # Perform merging in Python
            for group in res["mappings"]:
                indices = group.get("indices", [])
                title = group.get("consolidated_title", "")
                
                # Filter valid indices
                valid_indices = [idx for idx in indices if 0 <= idx < len(blocks)]
                if not valid_indices:
                    continue
                    
                # Merge all blocks in the group
                merged_block = blocks[valid_indices[0]]
                for idx in valid_indices[1:]:
                    merged_block = merge_two_blocks(merged_block, blocks[idx])
                
                # Override title
                merged_block["title"] = title
                consolidated.append(merged_block)
                merged_indices.update(valid_indices)
                
            # Add any raw blocks that were not merged
            for idx, b in enumerate(blocks):
                if idx not in merged_indices:
                    consolidated.append(b)
                    
            consolidated.sort(key=lambda x: x.get("_chunk_start") if x.get("_chunk_start") is not None else 0.0)
            return consolidated
            
        if attempt < max_retries:
            logger.warning(f"Consolidation mapping attempt {attempt+1} failed, retrying...")
            time.sleep(2 ** attempt)
            
    logger.warning("Failed to consolidate concept blocks using LLM mapping, falling back to deterministic consolidation.")
    return consolidate_blocks(blocks)

def parse_transcript(input_path, output_path, frame_manifest_path, lecture_title=None, min_block_duration=120):
    """Automatically segments and parses an SRT transcript into a concept block map."""
    logger.info(f"Starting transcript parsing for {input_path}")
    
    # Infer lecture title early if not provided
    if not lecture_title:
        base = os.path.basename(input_path)
        name_no_ext = os.path.splitext(base)[0]
        lecture_title = name_no_ext.replace('_', ' ').replace('-', ' ').title()
        
    # 1. Parse SRT
    entries = parse_srt(input_path)
    if not entries:
        logger.error("No transcript entries found to parse.")
        return False
        
    total_duration_sec = entries[-1]['end']
    logger.info(f"Total transcript entries: {len(entries)}. Duration: {seconds_to_timestamp(total_duration_sec)}")
    
    # Load slide and reference manifests if they exist
    slide_data = []
    if os.path.exists("slide_manifest.json"):
        try:
            with open("slide_manifest.json", "r", encoding="utf-8") as f:
                slide_data = json.load(f)
        except Exception:
            pass
            
    ref_data = []
    if os.path.exists("reference_manifest.json"):
        try:
            with open("reference_manifest.json", "r", encoding="utf-8") as f:
                ref_data = json.load(f)
        except Exception:
            pass
            
    # Fetch cross-lecture continuity context if applicable
    continuity_context = ""
    try:
        try:
            from scripts.retrieve_continuity import get_continuity_context
        except ImportError:
            from retrieve_continuity import get_continuity_context
        continuity_context = get_continuity_context(lecture_title)
    except Exception as continuity_err:
        logger.warning(f"Failed to fetch continuity context: {continuity_err}")

    # 2. Chunk transcript into overlapping 10-minute (600s) windows with 9.5-minute (570s) steps
    window_size = 600.0
    step_size = 570.0
    chunks = []
    
    current_start = 0.0
    while current_start < total_duration_sec:
        current_end = current_start + window_size
        chunk_entries = [e for e in entries if current_start <= e['start'] < current_end]
        if chunk_entries:
            chunks.append(chunk_entries)
        current_start += step_size
        
    total_chunks = len(chunks)
    
    # 3. Process each chunk
    all_blocks = []
    for i, chunk in enumerate(chunks):
        blocks = process_chunk(chunk, i+1, total_chunks, slide_data, continuity_context)
        all_blocks.extend(blocks)
        
    if not all_blocks:
        logger.error("Failed to extract any concept blocks from transcript.")
        return False
        
    # Apply structural passes
    all_blocks = consolidate_blocks_llm(all_blocks, slide_data)
    all_blocks = inject_reference_notes(all_blocks, ref_data)
    all_blocks = apply_linguistic_filter(all_blocks)
        
    # 4. Global normalization and formatting
    normalized_blocks = []
    block_index = 1
    
    # Track all visual timestamps for the frame manifest
    visual_timestamps = set()
    
    # Filter empty or malformed blocks
    for block in all_blocks:
        title = block.get("title") or ""
        if len(title.strip()) < 3 and not block.get("examples", []):
            continue
            
        block_id = f"CB{block_index}"
        block_index += 1
        
        # Calculate transcript_range_percent based on chunk boundaries to ensure proper coverage
        examples = block.get("examples", [])
        block_start = block.get("_chunk_start", 0.0)
        block_end = block.get("_chunk_end", total_duration_sec)
                
        block_start = max(0.0, block_start)
        block_end = min(total_duration_sec, block_end)
        
        start_pct = int((block_start / total_duration_sec) * 100)
        end_pct = int((block_end / total_duration_sec) * 100)
        if start_pct >= end_pct:
            end_pct = min(100, start_pct + 5)
            
        range_pct = [start_pct, end_pct]
        
        # Format timestamps in examples and visual moments
        formatted_examples = []
        for ex in examples:
            ts = ex.get("timestamp", "")
            sec = timestamp_to_seconds(ts)
            ts_formatted = seconds_to_timestamp(sec)
            item = {
                "timestamp": ts_formatted,
                "sentence": ex.get("sentence", ex.get("scenario_or_problem", "")),
                "rule": ex.get("rule", ex.get("core_principles", "")),
                "working": ex.get("working", ex.get("step_by_step_logic", ""))
            }
            if "student_notes" in ex:
                item["student_notes"] = ex["student_notes"]
            if "method2" in ex:
                item["method2"] = ex["method2"]
            if "cloze_text" in ex:
                item["cloze_text"] = ex["cloze_text"]
            if "cornell_cues" in ex:
                item["cornell_cues"] = ex["cornell_cues"]
            if "srs_tag" in ex:
                item["srs_tag"] = ex["srs_tag"]
            if "teacher_analogies" in ex:
                item["teacher_analogies"] = ex["teacher_analogies"]
            formatted_examples.append(item)
            if ts_formatted and ts_formatted != "00:00:00":
                visual_timestamps.add(ts_formatted)
            
        formatted_visuals = []
        for vis in block.get("visual_moments", []):
            ts = vis.get("timestamp", "")
            sec = timestamp_to_seconds(ts)
            ts_formatted = seconds_to_timestamp(sec)
            formatted_visuals.append({
                "timestamp": ts_formatted,
                "type": vis.get("type", "board"),
                "description": vis.get("description", "")
            })
            visual_timestamps.add(ts_formatted)
            
        # Clean up temporary keys
        block.pop("_chunk_start", None)
        block.pop("_chunk_end", None)
        
        block["block_id"] = block_id
        block["transcript_range_percent"] = range_pct
        block["examples"] = formatted_examples
        block["visual_moments"] = formatted_visuals
        
        normalized_blocks.append(block)
        
    # Clean any leftover Devanagari characters from normalized blocks recursively
    logger.info("Running Pass 4: Clean remaining Devanagari script characters...")
    normalized_blocks = clean_dict_fields(normalized_blocks)
        
    # Generate final structure
    final_data = {
        "lecture_title": lecture_title,
        "lecture_duration_minutes": int(total_duration_sec // 60),
        "total_srt_entries": len(entries),
        "blocks": normalized_blocks
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)
    logger.info(f"Saved concept block map to: {output_path}")
    
    # 5. Save the frame manifest file
    frame_manifest_data = {}
    for idx, ts in enumerate(sorted(list(visual_timestamps))):
        fname = f"frame_{idx+1:03d}.png"
        frame_manifest_data[fname] = {
            "timestamp": ts,
            "type": "board"
        }
    with open(frame_manifest_path, "w", encoding="utf-8") as f:
        json.dump(frame_manifest_data, f, indent=2)
    logger.info(f"Saved initial frame manifest to: {frame_manifest_path}")
    
    # 6. Verify density
    if verify_density:
        passed, report = verify_density(output_path, input_path)
        if not passed:
            logger.warning(f"⚠️ Density verification failed! Coverage: {report.get('total_coverage_pct')}%, Density: {report.get('example_density')}")
        else:
            logger.info("✅ Density verification passed successfully.")
            
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse transcript to concept block map.")
    parser.add_argument('--input', default='lecture-input/transcript.srt', help='Path to transcript SRT')
    parser.add_argument('--output', default='concept_block_map.json', help='Output JSON path')
    parser.add_argument('--frame-manifest', default='frame_manifest.json', help='Output frame manifest path')
    parser.add_argument('--lecture-title', help='Override lecture title')
    parser.add_argument('--min-block-duration', type=int, default=120, help='Minimum block duration in seconds')
    args = parser.parse_args()
    
    success = parse_transcript(args.input, args.output, args.frame_manifest, args.lecture_title, args.min_block_duration)
    sys.exit(0 if success else 1)

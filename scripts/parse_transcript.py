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
    cli_path = os.environ.get("ANTIGRAVITY_CLI_PATH") or shutil.which("antigravity")
    if not cli_path or not os.path.exists(cli_path):
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
            os.makedirs("logs", exist_ok=True)
            with open("logs/failed_raw_output.txt", "w", encoding="utf-8") as fe:
                fe.write(output)
            logger.error(f"All JSON parsing attempts failed. Saved raw output to logs/failed_raw_output.txt. Raw snippet: {output[:500]}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("Antigravity CLI call timed out (600s).")
        return None
    except Exception as e:
        logger.error(f"Failed to execute Antigravity CLI: {e}")
        return None

def call_antigravity_chat_raw(prompt):
    """Calls the antigravity chat CLI command and returns the raw output text."""
    cli_path = os.environ.get("ANTIGRAVITY_CLI_PATH") or shutil.which("antigravity")
    if not cli_path or not os.path.exists(cli_path):
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

def process_chunk(entries, chunk_index, total_chunks, slide_data, continuity_context="", audit_feedback_context=""):
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

    feedback_section = ""
    if audit_feedback_context:
        feedback_section = f"### AUDIT FEEDBACK FROM PREVIOUS RUN:\n{audit_feedback_context}\nEnsure you strictly fix these issues in this chunk.\n\n"

    prompt = f"""
You are the Transcript Mapping Specialist Subagent.
Analyze the following lecture transcript segment from {start_str} to {end_str}.
Your task is to extract all key teaching concepts, rules, formulas, examples, visual moments, traps, and exercises discussed in this segment. Synthesize verbose teacher explanations into concise, exam-ready study notes. Preserve all FACTS and RULES but express them EFFICIENTLY using bullet points and short paragraphs.

--- TRANSCRIPT SEGMENT ---
{transcript_text}
-------------------------

{slides_section}
{continuity_section}
{feedback_section}Based on this transcript, produce a JSON object with a single key "blocks", containing a list of concept blocks matching this exact schema.
CRITICAL JSON SYNTAX RULE: Double quotes (") must ONLY be used for JSON keys and string boundaries. Inside JSON string values themselves, you MUST use single quotes (e.g. 'the') and never unescaped double quotes.

{{
  "blocks": [
    {{
      "title": "Slide title or explicit lecture heading. Create descriptive sub-headings only if a slide covers multiple distinct sub-concepts.",
      "concepts": [
        {{
          "term": "Term, rule, or formula name",
          "definition": "Clear, concise point-wise definition or rule statement. Apply **bolding** to key terms."
        }}
      ],
      "examples": [
        {{
          "timestamp": "HH:MM:SS",
          "sentence": "The complete word problem, scenario, or equation discussed",
          "rule": "The specific rule applied (1 sentence max). Set to null if it's just a redundant re-statement of a concept already defined in the block.",
          "working": "Step-by-step solution in concise numbered steps.",
          "teacher_analogies": "Any real-world analogies used by the teacher to explain this example",
          "student_notes": "Key student notes, warnings, or intuition boxes for this example",
          "method2": "Alternative Method 2 (Without Formula or visual drawing) if discussed"
        }}
      ],
      "visual_moments": [
        {{
          "timestamp": "HH:MM:SS",
          "type": "board or slide",
          "slide_number": "Integer slide number if type is slide, else null",
          "description": "Short description of the content"
        }}
      ],
      "teacher_quotes": [
        "Maximum 2 most impactful teacher statements per block. Paraphrase into formal English."
      ],
      "teacher_cautions": [
        "ONLY if the teacher EXPLICITLY says 'be careful', 'common mistake', 'remember this shortcut', 'trap', or 'trick'. Otherwise this array MUST be empty. Max 1 per block."
      ],
      "exercise_questions": [
        "Homework, practice, or unsolved questions assigned or discussed"
      ]
    }}
  ]
}}

STRICT RULES:
1. DEEP EXTRACTION (TWO-PASS): Before outputting the JSON, use a `<think>` block to list out all raw insights, formulas, real-world analogies, and examples found in the chunk. Then build the JSON.
1b. HIGH-QUALITY EXAM NOTES: Preserve 100% of core rules, formulas, and worked examples, and write out detailed steps. Write concise, point-wise notes instead of long, verbose paragraphs. Do NOT add unnecessary fluff, conversational filler, or redundant explanations.
2. EXTRACT EVERYTHING: Extract EVERY SINGLE example problem and question discussed in the transcript segment. Group continuous back-to-back examples under a single visual moment if they belong to the same board state to avoid duplicate screenshots.
3. ENGLISH ENFORCEMENT: Write purely in English. Do NOT preserve the teacher's Hinglish/bilingual conversational filler, BUT YOU MUST PRESERVE the intuitive real-world analogies translated into clear English. 
4. BOLDING & MARKDOWN: Aggressively use **bolding** for key terms, definitions, and formulas. Use single asterisks (like *plays*) for italics. Ensure SQL keywords (`SELECT`, etc.) are in UPPERCASE and wrapped in `<codeinline>...</codeinline>` tags for Consolas styling. Code blocks should be wrapped in `<codeblock>...</codeblock>`.
5. TRANSCRIPT FIDELITY: Your primary source of truth is the verbal transcript, not the slides. Extract the teaching logic, examples, and key analogies concisely using bullet points or very short paragraphs. Do not write generic slide summaries or textbook-length essays.
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
8. PRESERVE ANALOGIES & SEQUENCE (CRITICAL): The user specifically complained that generated notes lacked the sequence, analogies, and detailed explanations as told in the lecture. You MUST capture the exact chronological flow, the teacher's unique real-world analogies, and the step-by-step reasoning. Do NOT generate standard rhetoric or generic textbook summaries; mirror the lecture's unique teaching style.
9. JSON FORMAT: Enclose your final JSON inside ```json ... ``` tags.
10. CONCEPT BLOCK CONSOLIDATION: You must strictly align all concept block titles with actual slide titles or explicit lecture headings. Do NOT invent arbitrary, custom, or extra concept block titles or categories that are not explicitly present in the lecture slides or transcript. Group related content under these primary topic blocks rather than creating tiny or custom-named blocks.
11. STRICT FIDELITY CONSTRAINT (NO HALLUCINATIONS / ALTERATIONS): You must ONLY extract concepts, formulas, rules, examples, and definitions that are explicitly taught or mentioned in the provided transcript segment. Do NOT invent, assume, or add any extra topics, theories, rules, or questions that were not discussed by the teacher, even if they are standard academic concepts. You must NOT alter the facts, formulas, or examples taught by the teacher. The notes must represent a 100% faithful reconstruction of the actual lecture segment, nothing more and nothing less.
"""
    
    # Retry loop — up to 5 attempts with exponential backoff (10s, 20s, 40s, 80s)
    MAX_ATTEMPTS = 5
    for attempt in range(MAX_ATTEMPTS):
        res = call_antigravity_chat(prompt)
        if res and isinstance(res, dict) and "blocks" in res:
            # Add segment start/end timestamps to each block's temporary metadata
            for block in res["blocks"]:
                block["_chunk_start"] = start_time
                block["_chunk_end"] = end_time
            return res["blocks"]
        logger.warning(f"Attempt {attempt+1}/{MAX_ATTEMPTS} failed to parse or return valid JSON. Retrying...")
        if attempt < MAX_ATTEMPTS - 1:
            backoff = 10 * (2 ** attempt)  # 10s, 20s, 40s, 80s
            logger.info(f"Waiting {backoff}s before retry...")
            time.sleep(backoff)
        
    # Non-fatal: skip this chunk with a warning; the pipeline continues with other chunks
    logger.warning(f"Chunk {chunk_index}/{total_chunks} skipped after {MAX_ATTEMPTS} failed attempts. " 
                   f"Transcript segment {start_str}-{end_str} will be missing from notes.")
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
            
            # Strict Match condition: Exact match of normalized titles to prevent concept jumbling
            is_match = (title_clean == existing_clean)
                    
            if is_match:
                matched_idx = idx
                break
                
        if matched_idx is None:
            # Create new block
            merged_block = {
                "title": title,
                "_chunk_start": block.get("_chunk_start"),
                "_chunk_end": block.get("_chunk_end"),
                "concepts": list(block.get("concepts", [])),
                "examples": list(block.get("examples", [])),
                "visual_moments": list(block.get("visual_moments", [])),
                "teacher_quotes": list(block.get("teacher_quotes", [])),
                "teacher_cautions": list(block.get("teacher_cautions", [])),
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
            merge_str_lists(existing["teacher_cautions"], block.get("teacher_cautions", []))
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

CONCEPT BLOCK TO UPDATE (built from the transcript mapping):
{json.dumps(block, indent=1)}

TASK:
Integrate, map, and correct the concept block contextually using the user's handwritten reference notes:
1. CROSS-CHECK AND CORRECT: Compare the reference notes against the mapped concepts. Check for any mismatches, incorrect terms, or omissions in the mapped concepts. Use the reference notes to correct and enrich the explanations.
2. SOURCE-ALIGNED INTEGRATION: Do NOT blindly copy-paste the notes. Align them logically with the flow of the lecture. Verify how the teacher actually explained the concept/rule in the lecture.
3. MATCH KEYS: Map the rules, examples, traps, tricks, student doubts, and warnings into their respective keys (e.g. concepts, examples, visual_moments, teacher_quotes, traps, tricks, student_notes, boundary_questions).
4. PROFESSIONAL STUDY NOTE TONE: Format the injected elements to match the academic, high-fidelity tone of the rest of the document (bold key terms, pastel highlights, step-by-step layout).

OUTPUT FORMAT (respond with ONLY this JSON):
{{
  ... updated concept block fields ...
}}"""
        res = call_antigravity_chat(prompt)
        if res and isinstance(res, dict):
            # Preserve internal block metadata keys
            for key, val in res.items():
                if val is not None:
                    if isinstance(val, (list, dict, str)) and not val:
                        # If key in res is empty (like an empty list []), do NOT overwrite
                        continue
                    block[key] = val
            if chunk_start is not None:
                block["_chunk_start"] = chunk_start
            if chunk_end is not None:
                block["_chunk_end"] = chunk_end
                
        updated_blocks.append(block)
    return updated_blocks


def apply_linguistic_filter(blocks, audit_feedback_context=""):
    if not blocks:
        return []
    logger.info("Running Pass 3: Post-Processing Linguistic Filter...")
    
    # Process blocks in small batches of 1-2 blocks to prevent token limit truncation and silent summarization
    batch_size = 1
    
    for idx in range(0, len(blocks), batch_size):
        batch = blocks[idx:idx+batch_size]
        input_blocks = [dict(b) for b in batch]
        
        feedback_instruction = ""
        if audit_feedback_context:
            feedback_instruction = f"URGENT AUDIT FAILURES TO FIX:\n{audit_feedback_context}\n"
            
        prompt = f"""You are the Post-Processing Linguistic Filter. You MUST respond with ONLY valid JSON and nothing else. No explanations, no commentary — ONLY a raw JSON object.

INPUT — Concept blocks:
{json.dumps(input_blocks, indent=1)}

{feedback_instruction}
TASK: Clean all text fields in the blocks to satisfy clear English. Rules:
1. STRICT DEVANAGARI BAN: Translate any Devanagari script (Hindi/Hinglish characters) to English or remove it.
2. HINGLISH CLEANUP: Translate Hinglish conversational filler (e.g. 'hai', 'toh', 'ki', 'bhi', 'aur') from explanations, workings, and definitions into clear English.
3. TEACHER QUOTES: Clean direct quotes (`teacher_quotes`) of Hinglish filler. DO NOT scrub the teacher's unique tone or quirky conversational analogies—simply make them readable in English.
4. NO SUMMARIZATION (CRITICAL): You must preserve 100% of the detail, formulas, examples, step-by-step workings, and explanations. Do not summarize, shorten, or simplify the explanation text. Only translate Devanagari and Hinglish filler to clear English while keeping the exact same depth and length of information.
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
                        for key in ["title", "explanation", "concepts", "examples", "teacher_quotes", "traps", "tricks", "student_notes", "method2"]:
                            if key in new_b:
                                new_val = new_b[key]
                                if new_val is not None:
                                    if isinstance(new_val, (list, dict, str)) and not new_val:
                                        continue
                                    orig_b[key] = new_val
                    success = True
                    break
    return blocks

def check_sentence_similarity(s1, s2):
    if not s1 or not s2:
        return 0.0
    w1 = set(re.findall(r'\b[a-z0-9_\-\+]{1,}\b', s1.lower()))
    w2 = set(re.findall(r'\b[a-z0-9_\-\+]{1,}\b', s2.lower()))
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / len(w1 | w2)

def merge_two_blocks(b1, b2, consolidated_title=None):
    title = consolidated_title or b1.get("title", "")
    
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
    concept_map = {str(c.get("term") or "").strip().lower(): c for c in concepts if c.get("term")}
    for c in b2.get("concepts", []):
        term = str(c.get("term") or "").strip().lower()
        if not term:
            continue
        if term not in concept_map:
            concepts.append(c)
            concept_map[term] = c
        else:
            existing_def = str(concept_map[term].get("definition") or "").strip()
            new_def = str(c.get("definition") or "").strip()
            if new_def and new_def.lower() not in existing_def.lower():
                concept_map[term]["definition"] = (existing_def + "\nAlso: " + new_def).strip()
            
    examples = list(b1.get("examples", []))
    for e2 in b2.get("examples", []):
        sent2 = e2.get("sentence", e2.get("scenario_or_problem", "")).strip()
        ts2 = timestamp_to_seconds(e2.get("timestamp", ""))
        is_dup = False
        for i, e1 in enumerate(examples):
            sent1 = e1.get("sentence", e1.get("scenario_or_problem", "")).strip()
            ts1 = timestamp_to_seconds(e1.get("timestamp", ""))
            
            # Timestamp delta check (> 5 mins / 300 seconds)
            if abs(ts1 - ts2) > 300:
                continue
                
            if not sent1 or not sent2:
                continue
                
            if sent1.lower() == sent2.lower() or check_sentence_similarity(sent1, sent2) >= 0.98:
                is_dup = True
                
                def safe_str(val):
                    return str(val).strip() if val is not None else ""

                w1 = safe_str(e1.get("working", e1.get("step_by_step_logic")))
                w2 = safe_str(e2.get("working", e2.get("step_by_step_logic")))
                if w2 and w2.lower() not in w1.lower():
                    e1["working"] = (w1 + "\n\n" + w2).strip()
                
                r1 = safe_str(e1.get("rule", e1.get("core_principles")))
                r2 = safe_str(e2.get("rule", e2.get("core_principles")))
                if r2 and r2.lower() not in r1.lower():
                    e1["rule"] = (r1 + " | " + r2).strip(" | ")
                
                sn1 = safe_str(e1.get("student_notes"))
                sn2 = safe_str(e2.get("student_notes"))
                if sn2 and sn2.lower() not in sn1.lower():
                    e1["student_notes"] = (sn1 + "\n\n" + sn2).strip()
                
                m1 = safe_str(e1.get("method2"))
                m2 = safe_str(e2.get("method2"))
                if m2 and m2.lower() not in m1.lower():
                    e1["method2"] = (m1 + "\n\n" + m2).strip()

                c1 = safe_str(e1.get("cloze_text"))
                c2 = safe_str(e2.get("cloze_text"))
                if c2 and c2.lower() not in c1.lower():
                    e1["cloze_text"] = (c1 + " " + c2).strip()

                cues1 = list(e1.get("cornell_cues", []))
                cues2 = e2.get("cornell_cues", [])
                for cue in cues2:
                    if cue and safe_str(cue).lower() not in {safe_str(c).lower() for c in cues1}:
                        cues1.append(cue)
                e1["cornell_cues"] = cues1

                if not e1.get("srs_tag") and e2.get("srs_tag"):
                    e1["srs_tag"] = e2.get("srs_tag")

                ana1 = safe_str(e1.get("teacher_analogies"))
                ana2 = safe_str(e2.get("teacher_analogies"))
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
            "title": b.get("title", "")
        })
        
    prompt = f"""You are the Concept Block Consolidator. You MUST respond with ONLY valid JSON and nothing else. No explanations, no commentary — ONLY a raw JSON object.
    
    INPUT — Raw concept blocks:
    {json.dumps(light_blocks, indent=1)}
    
    SLIDE HEADINGS for alignment:
    {json.dumps([{"slide": s.get("slide_number"), "title": s.get("ocr_text","")[:100]} for s in slide_data], indent=1)}
    
    TASK: Merge redundant and overlapping blocks. If two blocks cover the exact same concept or are truly redundant, MERGE them.
    TARGET: Maintain distinct main topics and separate sub-topics as independent blocks (e.g., different algorithms, methods, or protocols like FDM, TDM, and WDM must remain separate concept blocks). Align titles with actual slide headings.
    CRITICAL: Do NOT merge distinct sub-topics into a single generic block. Each main topic or distinct sub-topic must remain its own separate block to preserve chronological flow and detailed analogies. You MUST preserve the teacher's analogies and step-by-step sequences. Over-merging ruins the sequence of the notes.
    STRICT CONSTRAINT: You can ONLY merge contiguous (adjacent) blocks. Do NOT merge blocks that are separated by other unmerged blocks.
    
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

def synthesize_explanations(blocks):
    if not blocks:
        return []
    logger.info("Running Pass 1.6: Synthesizing verbose explanations...")
    for idx, block in enumerate(blocks):
        title = block.get("title", "")
        explanation = block.get("explanation", "")
        if len(explanation) > 4000:
            logger.info(f"Synthesizing explanation for '{title}' ({len(explanation)} chars)...")
            prompt = f"""You are the Note Explanation Synthesizer. Your goal is to rewrite the explanation for the concept block "{title}" to make it highly readable, like high-quality student study notes, without losing ANY detail.
            
            CRITICAL CONSTRAINTS:
            1. PRESERVE DETAIL: You MUST NOT shorten the explanation. Preserve 100% of the reasoning, mathematical formulas, equations, definitions, and core technical rules.
            2. DEDUPLICATION: Eliminate any redundant information, repeated descriptions, or summaries of other topics that are covered in other blocks.
            3. PRESERVE ANALOGIES (CRITICAL): Do NOT remove or summarize the teacher's real-world analogies; they must be preserved in full.
            4. FORMATTING: Use bolding and short paragraphs to make it readable.
            
            INPUT EXPLANATION:
            {explanation}
            
            OUTPUT: Respond with ONLY the rewritten explanation. No markdown wrappers other than standard formatting (e.g. bold, math). Do not wrap the output in json or backticks unless they are part of the formatting."""
            
            res = call_antigravity_chat_raw(prompt)
            if res and len(res.strip()) > 50:
                block["explanation"] = res.strip()
                logger.info(f"Synthesized explanation length: {len(block['explanation'])} chars.")
            else:
                logger.warning(f"Synthesis returned empty response. Keeping original explanation.")
    return blocks


def parse_transcript(input_path, output_path, frame_manifest_path, lecture_title=None, min_block_duration=120, audit_feedback_path=None):
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

    audit_feedback_context = ""
    if audit_feedback_path and os.path.exists(audit_feedback_path):
        try:
            with open(audit_feedback_path, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
                if feedback_data:
                    audit_feedback_context = "PREVIOUS AUDIT FAILED. FIX THESE ISSUES IN YOUR EXTRACTION:\n"
                    for gate, reasons in feedback_data.items():
                        for r in reasons:
                            audit_feedback_context += f"- Gate {gate}: {r}\n"
        except Exception as e:
            logger.warning(f"Could not load audit feedback: {e}")

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
        blocks = process_chunk(chunk, i+1, total_chunks, slide_data, continuity_context, audit_feedback_context)
        all_blocks.extend(blocks)
        
    if not all_blocks:
        logger.error("Failed to extract ANY concept blocks from transcript across all chunks. "
                     "This indicates a persistent API connectivity issue. Aborting pipeline.")
        return False
    
    # Count how many chunks had data vs were skipped
    successful_chunk_count = sum(1 for b in all_blocks if b)
    if successful_chunk_count == 0:
        logger.error("All chunk blocks are empty. Aborting.")
        return False
        
    # Apply structural passes
    all_blocks = consolidate_blocks_llm(all_blocks, slide_data)

    all_blocks = inject_reference_notes(all_blocks, ref_data)
    all_blocks = apply_linguistic_filter(all_blocks, audit_feedback_context)
        
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
            
            sentence_val = ex.get("sentence", ex.get("scenario_or_problem", "")).strip()
            working_val = ex.get("working", ex.get("step_by_step_logic", "")).strip()
            # Skip empty placeholder examples
            if not sentence_val and not working_val:
                continue
                
            item = {
                "timestamp": ts_formatted,
                "sentence": sentence_val,
                "rule": ex.get("rule", ex.get("core_principles", "")),
                "working": working_val
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
                "slide_number": vis.get("slide_number"),
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
    parser.add_argument('--audit-feedback', default=None, help='Path to audit feedback JSON')
    args = parser.parse_args()
    
    success = parse_transcript(args.input, args.output, args.frame_manifest, args.lecture_title, args.min_block_duration, args.audit_feedback)
    sys.exit(0 if success else 1)

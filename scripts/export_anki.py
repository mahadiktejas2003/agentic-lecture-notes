#!/usr/bin/env python3
"""Export concept_block_map.json into FSRS-optimized Anki flashcards.

Features:
  - 4-column output: Front | Back | Extra | Tags
  - Pipe ('|') separated to match Anki's Master Universal note type
  - Mixed-pattern architecture: Targeted Q&A, Simulated Cloze ([......]), True/False + Correction, Scenario, List/Enumeration, Worked Examples
  - Full sanitization (strips literal '|', replaces newlines with <br>)
  
Usage:
  python scripts/export_anki.py --input concept_block_map.json --output notes-output/anki_deck.csv
"""
import os
import json
import re
import csv
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# ---------------------------------------------------------------------------
# Helpers & Sanitizers
# ---------------------------------------------------------------------------

def clean_tags(text: str) -> str:
    """Strip HTML-like formatting tags but keep structural ones like b, i, u, sub, sup."""
    if not text:
        return ""
    # Strip custom tags like highlight/color, but preserve useful HTML tags
    text = re.sub(r'</?(highlight|color)[^>]*>', '', text)
    return text.strip()

def sanitize_field(text: str) -> str:
    """Strips pipe character and converts newlines to HTML <br> tags."""
    if not text:
        return ""
    # Remove literal pipes to prevent import parsing failures
    text = text.replace('|', ' ')
    # Clean whitespace and replace newlines with <br>
    text = text.strip()
    text = re.sub(r'\r?\n', '<br>', text)
    return text

def _sanitize_tag(s: str) -> str:
    """Make a string safe for an Anki tag (no spaces, no special chars)."""
    s = re.sub(r'[^a-zA-Z0-9_-]', '_', s)
    return re.sub(r'_+', '_', s).strip('_')[:50]

def make_simulated_cloze(term: str, definition: str) -> str | None:
    """Creates a Front field using simulated cloze [......] for a term."""
    if not term or not definition or len(definition) < 15:
        return None
    
    t_clean = term.strip()
    d_clean = definition.strip()
    
    # Case 1: Term appears in definition -> replace it
    pattern = re.compile(re.escape(t_clean), re.IGNORECASE)
    if pattern.search(d_clean):
        cloze_front = pattern.sub('[......]', d_clean, count=1)
        return cloze_front
        
    # Case 2: Standard fill-in format
    return f"{d_clean} is known as [......]."

# ---------------------------------------------------------------------------
# Core Exporter
# ---------------------------------------------------------------------------

def export_anki_cards(json_path: str, output_csv_path: str) -> int:
    """Read concept_block_map.json -> write pipe-delimited Anki CSV."""
    if not os.path.exists(json_path):
        logging.error(f"Concept block map not found at: {json_path}")
        return 0

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Normalize format (list vs dict)
    if isinstance(data, dict):
        blocks = data.get("blocks", data.get("concept_blocks", []))
        lecture_title = data.get("lecture_title", "")
    elif isinstance(data, list):
        blocks = data
        lecture_title = blocks[0].get("lecture_title", "") if blocks else ""
    else:
        logging.error("Unexpected JSON format in concept block map.")
        return 0

    lecture_tag = _sanitize_tag(lecture_title) if lecture_title else "DBMS"
    cards = []

    for block in blocks:
        block_id = block.get("block_id", "CB")
        title = block.get("title", "Lecture Section")
        block_tag = _sanitize_tag(title)
        
        # Tags: e.g. Subject::Topic::Subtopic (Anki hierarchy)
        base_tags = f"{lecture_tag}::{block_tag}"
        extra_context = f"Context: {lecture_title} \u2014 {title}"

        # 1. Concept Cards (Targeted Q&A and Simulated Cloze)
        for concept in block.get("concepts", []):
            term = clean_tags(concept.get("term", "")).strip()
            defn = clean_tags(concept.get("definition", "")).strip()
            if not term or not defn:
                continue
            
            # --- Card 1: Q&A format ---
            front_qa = f"Define: <b>{term}</b>"
            back_qa = f"<b>{defn}</b>"
            cards.append([
                sanitize_field(front_qa),
                sanitize_field(back_qa),
                sanitize_field(extra_context),
                f"{base_tags}::concept"
            ])
            
            # --- Card 2: Simulated Cloze format ---
            cloze_front = make_simulated_cloze(term, defn)
            if cloze_front:
                cloze_back = f"<b>{term}</b>"
                cards.append([
                    sanitize_field(cloze_front),
                    sanitize_field(cloze_back),
                    sanitize_field(extra_context),
                    f"{base_tags}::cloze"
                ])

        # 2. Concept Explanations
        for ce in block.get("concept_explanations", []):
            cname = clean_tags(ce.get("concept_name", "")).strip()
            cexpl = clean_tags(ce.get("detailed_explanation", "")).strip()
            if cname and cexpl:
                front_ce = f"Explain: <b>{cname}</b>"
                back_ce = f"<b>{cexpl}</b>"
                cards.append([
                    sanitize_field(front_ce),
                    sanitize_field(back_ce),
                    sanitize_field(extra_context),
                    f"{base_tags}::concept"
                ])

        # 3. Worked Examples (Math/Logic/Grammar)
        for ex in block.get("examples", []):
            sentence = clean_tags(ex.get("sentence", "")).strip()
            if not sentence:
                continue
            working = clean_tags(ex.get("working", "")).strip()
            answer = clean_tags(ex.get("answer", "")).strip()
            rule = clean_tags(ex.get("rule", "")).strip()
            student_note = clean_tags(ex.get("student_notes", "")).strip()

            front_ex = f"Q: {sentence}"
            
            back_ex_parts = []
            if rule:
                back_ex_parts.append(f"<b>Rule:</b> {rule}")
            if answer:
                back_ex_parts.append(f"<b>Answer:</b> <b>{answer}</b>")
            back_ex = "<br>".join(back_ex_parts)
            
            extra_ex_parts = []
            if working:
                extra_ex_parts.append(f"<b>Working:</b><br>{working}")
            if student_note:
                extra_ex_parts.append(f"<b>Student Doubt/Note:</b><br>{student_note}")
            extra_ex = "<br><br>".join(extra_ex_parts) if extra_ex_parts else extra_context
            
            cards.append([
                sanitize_field(front_ex),
                sanitize_field(back_ex),
                sanitize_field(extra_ex),
                f"{base_tags}::example"
            ])

        # 4. Traps & Common Misconceptions (True/False + Warnings)
        for trap in block.get("traps", []):
            trap_text = clean_tags(trap if isinstance(trap, str) else trap.get("text", "")).strip()
            if not trap_text:
                continue
            
            # --- Card 1: True/False + Correction ---
            front_tf = f"True or False: {trap_text}"
            back_tf = f"<b>False.</b><br>🚨 TRAP: This is a common misconception."
            cards.append([
                sanitize_field(front_tf),
                sanitize_field(back_tf),
                sanitize_field(extra_context),
                f"{base_tags}::trap"
            ])
            
            # --- Card 2: Trap warning ---
            front_warn = f"What is the common trap/misconception regarding {title}?"
            back_warn = f"🚨 TRAP:<br>{trap_text}"
            cards.append([
                sanitize_field(front_warn),
                sanitize_field(back_warn),
                sanitize_field(extra_context),
                f"{base_tags}::trap"
            ])

        # 5. Tricks & Shortcuts
        for trick in block.get("tricks", []):
            trick_text = clean_tags(trick if isinstance(trick, str) else trick.get("text", "")).strip()
            if trick_text:
                front_tr = f"What is the shortcut/trick for: {title}?"
                back_tr = f"💡 TRICK:<br>{trick_text}"
                cards.append([
                    sanitize_field(front_tr),
                    sanitize_field(back_tr),
                    sanitize_field(extra_context),
                    f"{base_tags}::trick"
                ])

    if not cards:
        logging.warning(f"No Anki cards could be generated from: {json_path}")
        return 0

    # Write pipe-delimited CSV
    os.makedirs(os.path.dirname(output_csv_path) or ".", exist_ok=True)
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f_out:
        # Use single pipe delimiter
        writer = csv.writer(f_out, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Front", "Back", "Extra", "Tags"])
        writer.writerows(cards)

    logging.info(f"✅ Anki FSRS export: {len(cards)} cards generated at {output_csv_path}")
    return len(cards)

# ---------------------------------------------------------------------------
# Main Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export concept block map to FSRS pipe-separated CSV.")
    parser.add_argument("--input", default="concept_block_map.json",
                        help="Path to concept_block_map.json")
    parser.add_argument("--output", default="notes-output/anki_deck.csv",
                        help="Path to output CSV file")
    args = parser.parse_args()

    count = export_anki_cards(args.input, args.output)
    if count == 0:
        exit(1)

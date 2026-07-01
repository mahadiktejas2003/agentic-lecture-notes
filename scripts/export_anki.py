#!/usr/bin/env python3
import os
import json
import re
import csv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def clean_xml_tags(text):
    """Removes HTML-like formatting tags (e.g., <b>, <i>) while leaving cloze tags intact or removing them based on context."""
    if not text:
        return ""
    # Strip basic tags
    text = re.sub(r'</?(b|i|u|color|highlight)[^>]*>', '', text)
    return text

def transcode_to_anki_cloze(text):
    """Transcodes <cloze answer="X" hint="Y">Z</cloze> tags into Anki's native {{c1::X::Y}} format."""
    if not text:
        return ""
    
    # We want to replace each <cloze answer="X" hint="Y">Z</cloze> with {{c1::X::Y}}
    # Or if answer is not specified, use the inner content Z: {{c1::Z::Y}}
    pattern = re.compile(r'<cloze\s+answer=["\']([^"\']*)["\']\s+hint=["\']([^"\']*)["\']>(.*?)</cloze>', re.IGNORECASE)
    def repl(match):
        answer = match.group(1).strip()
        hint = match.group(2).strip()
        content = match.group(3).strip()
        final_ans = answer if answer else content
        if hint:
            return f"{{{{c1::{final_ans}::{hint}}}}}"
        return f"{{{{c1::{final_ans}}}}}"
        
    text = pattern.sub(repl, text)
    
    # Fallback for simpler cloze tags <cloze>text</cloze>
    pattern_simple = re.compile(r'<cloze>(.*?)</cloze>', re.IGNORECASE)
    text = pattern_simple.sub(r"{{c1::\1}}", text)
    
    return text

def export_anki_cards(json_path, output_csv_path):
    """Parses concept_block_map.json and exports a tab-separated CSV file for Anki."""
    if not os.path.exists(json_path):
        logging.error(f"Concept block map not found at {json_path}")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        concept_blocks = json.load(f)
        
    anki_cards = []
    
    for block in concept_blocks:
        block_id = block.get("block_id", "CB")
        title = block.get("title", "Lecture Section")
        flow = block.get("flow", [])
        
        # Collect terms, examples, and clozes from the flow
        for idx, elem in enumerate(flow):
            el_type = elem.get("type")
            text = elem.get("text", "")
            
            # 1. Check for Cloze Deletions in Text
            if "<cloze" in text:
                clean_txt = clean_xml_tags(text)
                cloze_front = transcode_to_anki_cloze(clean_txt)
                # Anki Cloze notes only require the text in the first field (cloze formatting)
                # The second field can act as extra context (like the block title)
                anki_cards.append([
                    cloze_front,
                    f"Context: {block_id} - {title}",
                    f"lecture_{block_id.lower()} cloze"
                ])
                
            # 2. Extract Concepts/Definitions
            if el_type == "concept":
                term = elem.get("term", "")
                definition = elem.get("definition", "")
                if term and definition:
                    anki_cards.append([
                        f"Identify/Define: {term} (from {title})",
                        clean_xml_tags(definition),
                        f"lecture_{block_id.lower()} concept"
                    ])
                    
            # 3. Extract Examples / Worked Problems
            elif el_type == "example":
                examples = block.get("examples", [])
                ex_idx = elem.get("index")
                ex = None
                if ex_idx is not None and ex_idx < len(examples):
                    ex = examples[ex_idx]
                else:
                    target_sent = elem.get("sentence", "")
                    for e in examples:
                        if e.get("sentence", "").strip() == target_sent.strip():
                            ex = e
                            break
                if ex:
                    sentence = ex.get("sentence", "")
                    working = ex.get("working", "")
                    answer = ex.get("answer", "")
                    
                    if sentence:
                        front = f"Question: {clean_xml_tags(sentence)}"
                        back_parts = []
                        if working:
                            back_parts.append(f"Working:\n{clean_xml_tags(working)}")
                        if answer:
                            back_parts.append(f"Answer: {clean_xml_tags(answer)}")
                        
                        back = "\n\n".join(back_parts)
                        anki_cards.append([
                            front,
                            back,
                            f"lecture_{block_id.lower()} example"
                        ])

    # Write to tab-separated CSV
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
        # Front, Back, Tags
        writer.writerow(["#Front", "#Back", "#Tags"])  # Header prefixed with # for Anki compatibility
        for card in anki_cards:
            writer.writerow(card)
            
    logging.info(f"✅ Anki Export complete. Generated {len(anki_cards)} cards at: {output_csv_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export concept map blocks to Anki deck format.")
    parser.add_argument("--input", default="concept_block_map.json", help="Path to concept_block_map.json")
    parser.add_argument("--output", default="notes-output/anki_deck.csv", help="Path to output CSV file")
    args = parser.parse_args()
    
    export_anki_cards(args.input, args.output)

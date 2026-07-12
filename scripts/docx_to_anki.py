#!/usr/bin/env python3
"""Extract Anki flashcards directly from a generated LECTURE_NOTES .docx file.

Features:
  - 4-column output: Front | Back | Extra | Tags
  - Pipe ('|') separated to match Anki's Master Universal note type
  - Sanitization of pipes, conversion of newlines to HTML <br>
  - Generates both basic concept cards, clozes ([......]), T/F warnings, and worked examples.

Usage:
  python scripts/docx_to_anki.py --input notes-output/LECTURE_NOTES_XYZ.docx --output notes-output/XYZ_anki.csv
"""
import os
import re
import csv
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

try:
    from docx import Document
except ImportError:
    logging.error("python-docx not installed. Run: pip install python-docx")
    exit(1)

# ---------------------------------------------------------------------------
# Sanitization & Helpers
# ---------------------------------------------------------------------------

def _sanitize_tag(s: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9_-]', '_', s)
    return re.sub(r'_+', '_', s).strip('_')[:50]

def sanitize_field(text: str) -> str:
    """Strips pipes and formats newlines to <br>."""
    if not text:
        return ""
    text = text.replace('|', ' ')
    text = text.strip()
    text = re.sub(r'\r?\n', '<br>', text)
    return text

def _para_text(para) -> str:
    return para.text.strip()

def _is_heading(para) -> bool:
    style = para.style.name.lower() if para.style else ""
    return "heading" in style

def _heading_level(para) -> int:
    style = para.style.name.lower() if para.style else ""
    m = re.search(r'heading\s*(\d)', style)
    return int(m.group(1)) if m else 0

def _has_bold(para) -> bool:
    for run in para.runs:
        if run.text.strip():
            return bool(run.bold)
    return False

def _get_bold_prefix(para) -> tuple[str, str]:
    bold_parts = []
    rest_parts = []
    in_bold = True
    for run in para.runs:
        txt = run.text
        if run.bold and in_bold:
            bold_parts.append(txt)
        else:
            in_bold = False
            rest_parts.append(txt)
    return ("".join(bold_parts).strip().rstrip(":").rstrip("–").rstrip("-").strip(),
            "".join(rest_parts).strip())

def make_simulated_cloze(term: str, definition: str) -> str | None:
    """Creates a Front field using simulated cloze [......] for a term."""
    if not term or not definition or len(definition) < 15:
        return None
    
    t_clean = term.strip()
    d_clean = definition.strip()
    
    pattern = re.compile(re.escape(t_clean), re.IGNORECASE)
    if pattern.search(d_clean):
        cloze_front = pattern.sub('[......]', d_clean, count=1)
        return cloze_front
    return f"{d_clean} is known as [......]."

# ---------------------------------------------------------------------------
# Extraction Logic
# ---------------------------------------------------------------------------

def extract_cards_from_docx(docx_path: str) -> list[list[str]]:
    doc = Document(docx_path)
    
    basename = os.path.splitext(os.path.basename(docx_path))[0]
    basename = re.sub(r'^LECTURE_NOTES_', '', basename)
    basename = re.sub(r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$', '', basename)
    lecture_tag = _sanitize_tag(basename)
    
    cards = []
    current_h2 = "General"
    current_h3 = ""
    
    paragraphs = list(doc.paragraphs)
    i = 0
    
    while i < len(paragraphs):
        para = paragraphs[i]
        text = _para_text(para)
        
        if not text:
            i += 1
            continue
        
        if _is_heading(para):
            level = _heading_level(para)
            if level <= 2:
                current_h2 = text
                current_h3 = ""
            elif level == 3:
                current_h3 = text
            i += 1
            continue
        
        section_tag = _sanitize_tag(current_h3 or current_h2)
        tag = f"{lecture_tag}::{section_tag}"
        extra_context = f"Context: {basename} \u2014 {current_h3 or current_h2}"
        
        # 1. Concept definitions (bold term followed by description)
        if _has_bold(para):
            bold_part, rest = _get_bold_prefix(para)
            if bold_part and rest and len(rest) > 15:
                # Targeted Q&A Card
                cards.append([
                    sanitize_field(f"Define: <b>{bold_part}</b>"),
                    sanitize_field(rest),
                    sanitize_field(extra_context),
                    f"{tag}::concept"
                ])
                # Simulated Cloze Card
                cloze = make_simulated_cloze(bold_part, rest)
                if cloze:
                    cards.append([
                        sanitize_field(cloze),
                        sanitize_field(f"<b>{bold_part}</b>"),
                        sanitize_field(extra_context),
                        f"{tag}::cloze"
                    ])
                i += 1
                continue
        
        # 2. Worked Examples / Q&A blocks
        lower = text.lower()
        is_question = False
        if any(lower.startswith(p) for p in ['q.', 'q:', 'question', 'example', 'solve', 'find']):
            is_question = True
        elif re.match(r'^(q\.?\s*\d|example\s*\d|\d+[\.\)]\s)', lower):
            is_question = True
        
        if is_question:
            question = text
            answer_parts = []
            j = i + 1
            while j < len(paragraphs):
                next_para = paragraphs[j]
                next_text = _para_text(next_para)
                if not next_text:
                    j += 1
                    continue
                if _is_heading(next_para):
                    break
                nl = next_text.lower()
                if any(nl.startswith(p) for p in ['q.', 'q:', 'question']) or re.match(r'^(q\.?\s*\d|\d+[\.\)]\s)', nl):
                    break
                answer_parts.append(next_text)
                j += 1
                if len(answer_parts) >= 8:
                    break
            
            if answer_parts:
                ans_text = answer_parts[-1] if answer_parts else ""
                working_text = "\n".join(answer_parts[:-1]) if len(answer_parts) > 1 else ""
                
                cards.append([
                    sanitize_field(f"Q: {question}"),
                    sanitize_field(f"<b>Answer:</b> <b>{ans_text}</b>"),
                    sanitize_field(f"<b>Working:</b><br>{working_text}" if working_text else extra_context),
                    f"{tag}::example"
                ])
                i = j
                continue
        
        # 3. Key Rule / Warnings / Traps (contains ⭐ or warning indicators)
        if "⭐" in text or "[IMPORTANT]" in text.upper():
            clean = text.replace("⭐", "").replace("[IMPORTANT]", "").strip()
            if clean and len(clean) > 10:
                cards.append([
                    sanitize_field(f"True or False: {clean}"),
                    sanitize_field("<b>False.</b><br>🚨 TRAP: This is a common warning or rule violation."),
                    sanitize_field(extra_context),
                    f"{tag}::trap"
                ])
                cards.append([
                    sanitize_field(f"What is the key rule/warning regarding: {current_h3 or current_h2}?"),
                    sanitize_field(f"🚨 TRAP:<br>{clean}"),
                    sanitize_field(extra_context),
                    f"{tag}::trap"
                ])
                i += 1
                continue
                
        # 4. Bullet lists starting with • or - with bold prefix
        if (text.startswith("•") or text.startswith("-") or text.startswith("▸")) and _has_bold(para):
            bold_part, rest = _get_bold_prefix(para)
            if bold_part and rest and len(rest) > 10:
                cards.append([
                    sanitize_field(f"Define: <b>{bold_part}</b>"),
                    sanitize_field(rest),
                    sanitize_field(extra_context),
                    f"{tag}::concept"
                ])
                cloze = make_simulated_cloze(bold_part, rest)
                if cloze:
                    cards.append([
                        sanitize_field(cloze),
                        sanitize_field(f"<b>{bold_part}</b>"),
                        sanitize_field(extra_context),
                        f"{tag}::cloze"
                    ])
        
        i += 1
    
    return cards

def export_docx_to_anki(docx_path: str, output_csv: str) -> int:
    if not os.path.exists(docx_path):
        logging.error(f"DOCX not found: {docx_path}")
        return 0
    
    cards = extract_cards_from_docx(docx_path)
    if not cards:
        logging.warning(f"No cards extracted from: {docx_path}")
        return 0
    
    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        # Use single pipe delimiter
        writer = csv.writer(f, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Front", "Back", "Extra", "Tags"])
        writer.writerows(cards)
        
    logging.info(f"✅ DOCX Anki export: {len(cards)} cards generated at {output_csv}")
    return len(cards)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Anki cards from LECTURE_NOTES docx.")
    parser.add_argument("--input", required=True, help="Path to the docx file")
    parser.add_argument("--output", default=None, help="Output CSV path")
    args = parser.parse_args()
    
    out = args.output
    if not out:
        out = args.input.replace(".docx", "_anki.csv")
        
    count = export_docx_to_anki(args.input, out)
    if count == 0:
        exit(1)

#!/usr/bin/env python3
import os
import re
import sys
import logging
from docx import Document

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def parse_part_number(title):
    """
    Parses part number and base topic from lecture title.
    Returns (base_topic, part_number) or (None, None).
    """
    # Look for patterns like Part 2, Part-2, -2, _2, Day 2, day-2
    patterns = [
        r'(.*?)\s+Parts?\s*[-_]?\s*(\d+)',
        r'(.*?)\s*[-_]\s*(\d+)',
        r'(.*?)\s+Day\s*[-_]?\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            base = match.group(1).strip()
            part = int(match.group(2))
            # Clean up common lecture prefixes from base
            base_cleaned = re.sub(r'^(Lec|Lecture|Live)\s*[-_]?\s*\d+\s*[-_]?\s*', '', base, flags=re.IGNORECASE)
            base_cleaned = base_cleaned.strip().strip('-_')
            return base_cleaned, part
            
    return None, None

def find_previous_notes(base_topic, part, directory="notes-output"):
    """
    Finds the latest docx notes file for the previous part (part - 1).
    """
    if not os.path.exists(directory):
        return None
        
    prev_part = part - 1
    logging.info(f"Searching for previous part {prev_part} notes for topic '{base_topic}'...")
    
    # Tokenize base topic for flexible fuzzy/substring matching
    tokens = [t.lower() for t in re.split(r'[^a-zA-Z0-9]', base_topic) if len(t) > 2]
    if not tokens:
        tokens = [base_topic.lower()]
        
    best_file = None
    best_mtime = 0
    
    for f in os.listdir(directory):
        if not f.endswith(".docx") or not f.startswith("LECTURE_NOTES_"):
            continue
            
        f_lower = f.lower()
        
        # Check if file belongs to the previous part
        # Patterns like: -1, _1, Part 1, Part-1, Day 1
        part_patterns = [
            rf'[-_]{prev_part}[-_]',
            rf'part[-_]?{prev_part}',
            rf'day[-_]?{prev_part}',
            rf'_{prev_part}_'
        ]
        
        # If prev_part is 1, also allow the base topic name WITHOUT any part designation
        is_prev_part = False
        for pattern in part_patterns:
            if re.search(pattern, f_lower):
                is_prev_part = True
                break
                
        if prev_part == 1 and not is_prev_part:
            # If we're looking for Part 1, check if the file doesn't specify any part number
            # but matches the base topic
            if not re.search(r'[-_]\d+[-_]|part[-_]?\d+|day[-_]?\d+', f_lower):
                is_prev_part = True
                
        if not is_prev_part:
            continue
            
        # Match topic tokens
        match_count = sum(1 for token in tokens if token in f_lower)
        if match_count >= min(2, len(tokens)):
            path = os.path.join(directory, f)
            mtime = os.path.getmtime(path)
            if mtime > best_mtime:
                best_mtime = mtime
                best_file = path
                
    return best_file

def extract_glossary_from_docx(file_path):
    """
    Extracts headings, key terms and definitions from a generated docx file.
    Returns a markdown-formatted glossary.
    """
    if not file_path or not os.path.exists(file_path):
        return ""
        
    logging.info(f"Extracting glossary from previous notes: {file_path}")
    try:
        doc = Document(file_path)
    except Exception as e:
        logging.error(f"Failed to open previous docx file: {e}")
        return ""
        
    blocks = []
    current_block = None
    
    for p in doc.paragraphs:
        style = p.style.name
        text = p.text.strip()
        if not text:
            continue
            
        if style.startswith('Heading 2') or style == 'Heading 2':
            if current_block:
                blocks.append(current_block)
            current_block = {
                "title": text,
                "concepts": []
            }
        elif style.startswith('Heading 3') or style == 'Heading 3':
            pass  # We can skip key concept subheadings
        elif current_block is not None:
            # Look for term: definition pattern
            # For key concepts: bold term followed by definition text
            # Inside generate_docx, bold terms are often formatted as bold runs in the paragraph
            bold_text = "".join([run.text for run in p.runs if run.bold])
            if bold_text and len(bold_text) > 3 and ":" in text:
                parts = text.split(":", 1)
                term = parts[0].strip()
                defn = parts[1].strip()
                if len(term) < 50 and len(defn) > 10:
                    current_block["concepts"].append((term, defn))
            elif ":" in text and len(text.split(":", 1)[0]) < 30 and len(text.split(":", 1)[1]) > 10:
                parts = text.split(":", 1)
                current_block["concepts"].append((parts[0].strip(), parts[1].strip()))
                
    if current_block:
        blocks.append(current_block)
        
    # Format as markdown context block
    if not blocks:
        return ""
        
    markdown_lines = ["\n### CONTEXT FROM PREVIOUS PART:\n"]
    for b in blocks:
        markdown_lines.append(f"#### Topic: {b['title']}")
        if b['concepts']:
            for term, defn in b['concepts'][:5]:  # limit to top 5 key concepts per block to avoid token bloat
                markdown_lines.append(f"- **{term}**: {defn}")
        else:
            markdown_lines.append("- (No explicit glossary definitions extracted; see concept block title above)")
        markdown_lines.append("")
        
    return "\n".join(markdown_lines)

def get_continuity_context(lecture_title):
    """
    Main entry point. Automatically retrieves context from previous part notes.
    """
    if not lecture_title:
        return ""
        
    base_topic, part = parse_part_number(lecture_title)
    if not base_topic or not part or part <= 1:
        logging.info(f"Lecture '{lecture_title}' does not seem to be a sequential part (Part > 1). Skipping continuity retrieval.")
        return ""
        
    prev_file = find_previous_notes(base_topic, part)
    if prev_file:
        logging.info(f"Found previous notes at: {prev_file}")
        return extract_glossary_from_docx(prev_file)
    else:
        logging.warning(f"No previous notes found for topic '{base_topic}' (Part {part-1})")
        return ""

if __name__ == "__main__":
    title = sys.argv[1] if len(sys.argv) > 1 else ""
    if title:
        context = get_continuity_context(title)
        print(context)
    else:
        print("Usage: retrieve_continuity.py <lecture_title>")

#!/usr/bin/env python3
import os, json, argparse, re, glob
import sys
import logging
from docx import Document

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

def is_logo_frame(text):
    if not text:
        return False
    text_lower = text.lower()
    if "gate smashers" in text_lower or "gate smasher" in text_lower:
        words = re.findall(r'\b\w+\b', text_lower)
        if len(words) < 25 or "subscribe" in text_lower or "join" in text_lower or "follow" in text_lower:
            return True
    return False

def are_ocr_texts_similar(text1, text2, threshold=0.48):
    if not text1 or not text2:
        return False
    # Extract unique words with length >= 4
    w1 = set(re.findall(r'\b[a-z]{4,}\b', text1.lower()))
    w2 = set(re.findall(r'\b[a-z]{4,}\b', text2.lower()))
    
    if not w1 or not w2:
        return False
        
    common = w1 & w2
    ratio = len(common) / min(len(w1), len(w2))
    return ratio > threshold

def are_rules_similar(r1, r2, threshold=0.50):
    if not r1 or not r2:
        return False
    w1 = set(re.findall(r'\b[a-z]{4,}\b', r1.lower()))
    w2 = set(re.findall(r'\b[a-z]{4,}\b', r2.lower()))
    
    if not w1 or not w2:
        return False
        
    common = w1 & w2
    ratio = len(common) / min(len(w1), len(w2))
    return ratio > threshold


# Helper Functions (unchanged)
def add_revision_box(doc, bullets, rule=None):
    parts = ['[⚡ Quick Rev]'] + [f'• {b}' for b in bullets]
    if rule:
        parts.append(f'Rule: {rule}')
    text = '\n'.join(parts)
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(9)
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="D6EAF8" w:val="clear"/>')
    p._p.get_or_add_pPr().append(shading)
    return p

def add_trap(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(f'🚨 TRAP: {text}')
    run.bold = True
    run.font.size = Pt(10)
    return p

def add_trick(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(f'💡 TRICK: {text}')
    run.bold = True
    run.font.size = Pt(10)
    return p

def add_quote(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(f'📝 QUOTE: "{text}"')
    run.italic = True
    run.font.size = Pt(10)
    return p

def add_correction(doc, wrong, correct):
    p = doc.add_paragraph()
    run_wrong = p.add_run(wrong)
    run_wrong.font.strike = True
    p.add_run(' → ')
    run_correct = p.add_run(correct)
    run_correct.bold = True
    return p

def add_styled_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(9)
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="2C3E50" w:val="clear"/>')
        cell._element.get_or_add_tcPr().append(shading)
    for ri, row_data in enumerate(rows):
        for ci, value in enumerate(row_data):
            cell = table.rows[ri + 1].cells[ci]
            cell.text = str(value)
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
            if ri % 2 == 1:
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F3F4" w:val="clear"/>')
                cell._element.get_or_add_tcPr().append(shading)
    return table

def add_image_if_exists(doc, path, width=Inches(4.5)):
    if os.path.exists(path):
        doc.add_picture(path, width=width)
        return True
    return False

def add_shaded_formula(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="EAECEE" w:val="clear"/>')
    p._p.get_or_add_pPr().append(shading)
    return p

def get_vm_image_path(vm, block_id, slides, timestamp_to_frame, frames):
    ts = vm.get('timestamp', '').rstrip('*')
    v_type = vm.get('type', 'board')
    
    img_path = None
    frame_fname = None
    if v_type == 'slide':
        slide_num = vm.get('slide_number')
        if slide_num and slides:
            for s in slides:
                if s.get('slide_number') == slide_num:
                    img_path = s.get('image_path')
                    break
    else:
        if ts and ts in timestamp_to_frame:
            frame_fname = timestamp_to_frame[ts]
            img_path = os.path.join('screenshots', frame_fname)
        else:
            fallback_name = f"{block_id}_{ts.replace(':', '')}.jpg"
            img_path = f"screenshots/{fallback_name}"
            if fallback_name in frames:
                frame_fname = fallback_name
            elif f"{fallback_name}*" in frames:
                frame_fname = f"{fallback_name}*"
    return img_path, frame_fname

def insert_image_for_vm(doc, vm, block_id, slides, timestamp_to_frame, frames, inserted_filenames, inserted_ocrs):
    img_path, frame_fname = get_vm_image_path(vm, block_id, slides, timestamp_to_frame, frames)
    if img_path and os.path.exists(img_path):
        current_ocr = ""
        if frame_fname and frame_fname in frames:
            current_ocr = frames[frame_fname].get('ocr_text', '')
        
        if not current_ocr.strip():
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(img_path)
                current_ocr = pytesseract.image_to_string(img).strip()
                logging.info(f"Generated on-the-fly OCR for {img_path}: {current_ocr[:50]}...")
            except Exception as e:
                logging.warning(f"Could not perform on-the-fly OCR on {img_path}: {e}")
        
        is_duplicate = os.path.basename(img_path) in inserted_filenames
        is_slide = "slides" in img_path or "slide_" in os.path.basename(img_path)
        if current_ocr.strip() and is_slide:
            is_duplicate = is_duplicate or any(
                are_ocr_texts_similar(current_ocr, prev_ocr, threshold=0.98)
                for prev_ocr, prev_is_slide in inserted_ocrs
                if prev_is_slide == is_slide
            )
        
        if is_duplicate or is_logo_frame(current_ocr):
            logging.info(f"Skipping duplicate or logo slide image: {frame_fname or img_path}")
            return False
        else:
            if add_image_if_exists(doc, img_path):
                inserted_filenames.add(os.path.basename(img_path))
                if current_ocr.strip():
                    inserted_ocrs.append((current_ocr, is_slide))
                return True
    return False

def build_document(concept_map_path, frame_manifest_path, slide_manifest_path, output_path):
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    # Load manifests
    if not os.path.exists(concept_map_path):
        logging.error(f"Error: Concept block map not found at {concept_map_path}")
        return False, None

    with open(concept_map_path, 'r', encoding='utf-8') as f:
        concept_blocks = json.load(f)

    # Guard against empty concept_blocks list
    if not concept_blocks or not isinstance(concept_blocks, list) or len(concept_blocks) == 0:
        logging.warning("Warning: Concept block map is empty. Generating minimal document.")
        concept_blocks = []

    frames = {}
    if frame_manifest_path and os.path.exists(frame_manifest_path):
        with open(frame_manifest_path, 'r', encoding='utf-8') as f:
            frames = json.load(f)

    slides = []
    if slide_manifest_path and os.path.exists(slide_manifest_path):
        with open(slide_manifest_path, 'r', encoding='utf-8') as f:
            slides = json.load(f)

    # SEMANTIC COHERENCE CHECK: Warn if concept blocks and frames appear mismatched
    if concept_blocks and frames:
        # Extract keywords from concept block titles
        import re
        concept_keywords = set()
        for block in concept_blocks[:3]:  # Check first few blocks
            title = block.get('title', '').lower()
            words = re.findall(r'\b[a-z]{4,}\b', title)  # Words 4+ chars
            concept_keywords.update(words)
        
        # Extract keywords from frame OCR text
        frame_keywords = set()
        for fname, info in list(frames.items())[:10]:  # Check first 10 frames
            ocr = info.get('ocr_text', '').lower()
            words = re.findall(r'\b[a-z]{4,}\b', ocr)
            frame_keywords.update(words)
        
        # Check for overlap
        common = concept_keywords & frame_keywords
        overlap_ratio = len(common) / max(len(concept_keywords), 1)
        
        if overlap_ratio < 0.15:  # Less than 15% keyword overlap
            logging.warning(f"⚠️  SEMANTIC COHERENCE WARNING: Concept blocks and frames may be from different lectures!")
            logging.warning(f"   Concept keywords: {list(concept_keywords)[:10]}")
            logging.warning(f"   Frame keywords: {list(frame_keywords)[:10]}")
            logging.warning(f"   Overlap ratio: {overlap_ratio:.2f} (expected > 0.15)")

    # Build a lookup from timestamp to frame filename
    timestamp_to_frame = {}
    for filename, info in frames.items():
        ts = info.get('timestamp')
        if ts:
            ts_clean = ts.rstrip('*')
            timestamp_to_frame[ts_clean] = filename

    # Title
    lecture_title = "Lecture Reconstruction Notes"
    # Check if the manifest provides a dedicated lecture title
    if concept_blocks and isinstance(concept_blocks, list) and len(concept_blocks) > 0:
        if "lecture_title" in concept_blocks[0]:
            lecture_title = concept_blocks[0]["lecture_title"]
        else:
            # Fallback: use first block's title only if it doesn't look like a question range
            first_title = concept_blocks[0].get('title', '')
            if first_title and not re.match(r'^.*\(Questions?\s*\d+', first_title):
                lecture_title = first_title
    doc.add_heading(lecture_title, 0)

    # Section 1: Lecture Flow Outline
    doc.add_heading("Section 1: Lecture Flow Outline", level=1)
    for block in concept_blocks:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(block.get('title', 'Untitled Concept Block'))
        run.bold = True
    doc.add_paragraph()

    # Section 2: Detailed Concept Blocks
    doc.add_heading("Section 2: Detailed Concept Blocks", level=1)

    inserted_ocrs = []
    inserted_filenames = set()
    for block in concept_blocks:
        block_id = block.get('block_id', 'CB')
        title = block.get('title', 'Untitled Concept')
        doc.add_heading(f"{block_id}: {title}", level=2)

        # Teacher's explanation text
        explanation = block.get('explanation', '')
        if explanation:
            doc.add_paragraph(explanation)
        else:
            p = doc.add_paragraph()
            p.add_run("(No detailed explanation provided in the source.)").italic = True

        # Table data rendering
        table_data = block.get('table')
        if table_data:
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            if headers and rows:
                table_title = table_data.get('title', 'Reference Table')
                doc.add_heading(table_title, level=3)
                add_styled_table(doc, headers, rows)
                doc.add_paragraph()

        # Key Concepts and Definitions
        concepts = block.get('concepts', [])
        if concepts:
            doc.add_heading("Key Concepts & Definitions:", level=3)
            for item in concepts:
                p_c = doc.add_paragraph(style='List Bullet')
                p_c.add_run(item.get('term', '') + ": ").bold = True
                p_c.add_run(item.get('definition', ''))

        # Examples & Illustrations
        examples = block.get('examples', [])
        seen_rules_in_block = []
        inserted_vm_indices = set()
        visual_moments = block.get('visual_moments', [])

        if examples:
            doc.add_heading("Examples & Illustrations:", level=3)
            for idx, ex in enumerate(examples):
                p_q = doc.add_paragraph()
                sentence = ex.get('sentence', 'Example')
                is_question = sentence.endswith('?') or sentence.startswith(('Q:', 'Explain', 'Describe', 'Why', 'How', 'What', 'Define', 'List'))
                
                pref = "Q: " if is_question else "Example: "
                p_q.add_run(pref).bold = True
                p_q.add_run(sentence)

                rule = ex.get('rule', '')
                is_redundant_rule = False
                if rule:
                    is_redundant_rule = any(are_rules_similar(rule, prev) for prev in seen_rules_in_block)

                if rule and not is_redundant_rule:
                    p_rule = doc.add_paragraph()
                    label = "Applicable Rule: " if is_question else "Key Concept: "
                    p_rule.add_run(label).bold = True
                    p_rule.add_run(rule)
                    seen_rules_in_block.append(rule)

                working_text = ex.get('working', '')
                if working_text:
                    label_work = "Explanation/Working:" if is_question else "Explanation:"
                    doc.add_paragraph(label_work).runs[0].bold = True
                    p_work = doc.add_paragraph()
                    p_work.add_run(working_text)

                # Answer extraction: if working contains "->", take the part after last "->"
                ans_text = working_text.split("->")[-1].strip() if "->" in working_text else (working_text.split("=")[-1].strip() if "=" in working_text else "")
                if ans_text and is_question:
                    p_ans = doc.add_paragraph()
                    p_ans.add_run("Answer: ").bold = True
                    p_ans.add_run(ans_text)

                # Place corresponding visual moment inline right under the example (1-to-1 mapping by index)
                if idx < len(visual_moments):
                    vm = visual_moments[idx]
                    success_inserted = insert_image_for_vm(doc, vm, block_id, slides, timestamp_to_frame, frames, inserted_filenames, inserted_ocrs)
                    if success_inserted:
                        inserted_vm_indices.add(idx)

        # Important Points / Teacher's Emphasis
        important_points = block.get('important_points', [])
        if important_points:
            doc.add_heading("Key Highlights (⭐ Teacher's Emphasis):", level=3)
            for item in important_points:
                p_i = doc.add_paragraph()
                p_i.add_run("⭐ ").bold = True
                p_i.add_run(item)

        # Exercise Questions
        exercises = block.get('exercise_questions', [])
        if exercises:
            # Only print the “Exercise Questions:” heading if there is at least one real question text
            real_exercises = [eq for eq in exercises if isinstance(eq, str) and eq.strip()]
            if real_exercises:
                p = doc.add_paragraph()
                p.add_run("Exercise Questions:").bold = True
                for eq in real_exercises:
                    doc.add_paragraph(eq, style='List Bullet')

        # Visual Moments & Images (Leftovers)
        leftover_moments = [vm for i, vm in enumerate(visual_moments) if i not in inserted_vm_indices]
        for vm in leftover_moments:
            insert_image_for_vm(doc, vm, block_id, slides, timestamp_to_frame, frames, inserted_filenames, inserted_ocrs)

        # Quotes, Traps, Tricks
        for q in block.get('teacher_quotes', []):
            add_quote(doc, q)
        for t in block.get('traps', []):
            add_trap(doc, t)
        for tr in block.get('tricks', []):
            add_trick(doc, tr)

        # Revision Box at the end (Optional - only if defined or if we have traps/revisions)
        if block.get('revision_box', False):
            rev_bullets = []
            if block.get('transcript_range_percent'):
                rev_bullets.append(f"Transcript range: {block['transcript_range_percent'][0]}% – {block['transcript_range_percent'][1]}%")
            if block.get('traps'):
                rev_bullets.append(f"Key trap: {block['traps'][0]}")
            for bullet in block.get('revision_bullets', []):
                rev_bullets.append(bullet)
            if not rev_bullets:
                rev_bullets.append("Refer to full notes for details.")
            add_revision_box(doc, rev_bullets, rule=block.get('title', ''))

        doc.add_paragraph()

    # Load profile
    profile = {}
    if os.path.exists("lecture_profile.json"):
        try:
            with open("lecture_profile.json", "r", encoding="utf-8") as f:
                profile = json.load(f)
        except Exception as e:
            logging.warning(f"Could not load lecture_profile.json: {e}")

    # Section 3: Rules, Formulas & Exam Traps
    all_traps = []
    all_tricks = []
    for block in concept_blocks:
        for trap in block.get('traps', []):
            all_traps.append((trap, block.get('title', '')))
        for trick in block.get('tricks', []):
            all_tricks.append((trick, block.get('title', '')))
            
    if (all_traps or all_tricks) and profile.get("generate_theoretical_theory", True):
        doc.add_heading("Section 3: Rules, Formulas & Exam Traps", level=1)
        for trap, btitle in all_traps:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run("🚨 ").bold = True
            p.add_run(f"From {btitle}: {trap}")
        for trick, btitle in all_tricks:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run("💡 ").bold = True
            p.add_run(f"From {btitle}: {trick}")

    # Section 4: Final Revision Points
    points_added = 0
    temp_p_runs = []
    for block in concept_blocks:
        title = block.get('title', '')
        examples = block.get('examples', [])
        if isinstance(examples, list) and len(examples) > 0:
            rule = examples[0].get('rule', '')
            if rule:
                temp_p_runs.append((title, rule))
                points_added += 1
    if points_added > 0 and profile.get("generate_worked_examples", True):
        doc.add_heading("Section 4: Final Revision Points", level=1)
        for title, rule in temp_p_runs:
            doc.add_paragraph(f"• {title}: {rule}", style='List Bullet')

    import datetime
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the list of inserted image filenames for the audit tool
    try:
        with open("inserted_images.json", "w", encoding="utf-8") as f:
            json.dump(list(inserted_filenames), f, indent=2)
        logging.info(f"Saved {len(inserted_filenames)} inserted image names to inserted_images.json")
    except Exception as e:
        logging.warning(f"Could not save inserted_images.json: {e}")

    doc.save(output_path)
    logging.info(f"Notes document generated successfully at: {output_path}")

    archive_path = None
    # Generate a unique, timestamped, and sanitized lecture-specific archived copy to prevent overwriting
    try:
        sanitized_title = re.sub(r'[^a-zA-Z0-9_-]', '_', lecture_title)
        sanitized_title = re.sub(r'_+', '_', sanitized_title).strip('_')
        current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        archive_name = f"LECTURE_NOTES_{sanitized_title}_{current_date}.docx"
        archive_path = os.path.join(os.path.dirname(output_path), archive_name)
        doc.save(archive_path)
        logging.info(f"Archived unique copy saved successfully at: {archive_path}")
    except Exception as e:
        logging.warning(f"Warning: Could not save archived unique copy: {e}")

    return True, archive_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate Word document notes from sub-agent manifests.")
    parser.add_argument('--concept-map', default='concept_block_map.json')
    parser.add_argument('--frame-manifest', default='frame_manifest.json')
    parser.add_argument('--slide-manifest', default='slide_manifest.json')
    parser.add_argument('--output', default='notes-output/LECTURE_NOTES.docx')
    args = parser.parse_args()
    success, archive_path = build_document(args.concept_map, args.frame_manifest, args.slide_manifest, args.output)
    import sys
    sys.exit(0 if success else 1)

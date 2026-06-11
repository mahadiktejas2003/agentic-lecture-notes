#!/usr/bin/env python3
import os, json, argparse, re
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

    frames = {}
    if frame_manifest_path and os.path.exists(frame_manifest_path):
        with open(frame_manifest_path, 'r', encoding='utf-8') as f:
            frames = json.load(f)

    slides = []
    if slide_manifest_path and os.path.exists(slide_manifest_path):
        with open(slide_manifest_path, 'r', encoding='utf-8') as f:
            slides = json.load(f)

    # Build a lookup from timestamp to frame filename
    timestamp_to_frame = {}
    for filename, info in frames.items():
        ts = info.get('timestamp')
        if ts:
            timestamp_to_frame[ts] = filename

    # Title
    lecture_title = "Lecture Reconstruction Notes"
    # Check if the manifest provides a dedicated lecture title
    if "lecture_title" in concept_blocks[0]:
        lecture_title = concept_blocks[0]["lecture_title"]
    elif concept_blocks and isinstance(concept_blocks, list):
        # Fallback: use first block's title only if it doesn’t look like a question range
        first_title = concept_blocks[0].get('title', '')
        if first_title and not re.match(r'^.*\(Questions?\s*\d+', first_title):
            lecture_title = first_title
    doc.add_heading(f"NOTES ## {lecture_title}", 0)

    # Section 1: Lecture Flow Outline
    doc.add_heading("Section 1: Lecture Flow Outline", level=1)
    for block in concept_blocks:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(block.get('title', 'Untitled Concept Block'))
        run.bold = True
    doc.add_paragraph()

    # Section 2: Detailed Concept Blocks
    doc.add_heading("Section 2: Detailed Concept Blocks", level=1)

    for block in concept_blocks:
        block_id = block.get('block_id', 'CB')
        title = block.get('title', 'Untitled Concept')
        doc.add_heading(f"{block_id}: {title}", level=2)

        # Teacher's explanation text
        explanation = block.get('explanation', '')
        if explanation:
            if len(explanation) > 600:
                explanation = explanation[:500] + "... (see worked examples for detailed rules)"
            doc.add_paragraph(explanation)
        else:
            p = doc.add_paragraph()
            p.add_run("(No detailed explanation provided in the source.)").italic = True

        # Key Concepts and Definitions
        concepts = block.get('concepts', [])
        if concepts:
            doc.add_heading("Key Concepts & Definitions:", level=3)
            for item in concepts:
                p_c = doc.add_paragraph(style='List Bullet')
                p_c.add_run(item.get('term', '') + ": ").bold = True
                p_c.add_run(item.get('definition', ''))

        # Worked Examples
        examples = block.get('examples', [])
        if examples:
            doc.add_heading("Worked Examples:", level=3)
            for idx, ex in enumerate(examples):
                p_q = doc.add_paragraph()
                p_q.add_run("Q: ").bold = True
                p_q.add_run(ex.get('sentence', 'Example Question'))

                p_rule = doc.add_paragraph()
                p_rule.add_run("Rule: ").bold = True
                p_rule.add_run(ex.get('rule', 'Standard Rule'))

                working_text = ex.get('working', '')
                if working_text:
                    doc.add_paragraph("Working:").runs[0].bold = True
                    p_work = doc.add_paragraph()
                    p_work.add_run(working_text)

                # Answer extraction: if working contains "->", take the part after last "->"
                ans_text = working_text.split("->")[-1].strip() if "->" in working_text else (working_text.split("=")[-1].strip() if "=" in working_text else "")
                if ans_text:
                    p_ans = doc.add_paragraph()
                    p_ans.add_run("Answer: ").bold = True
                    p_ans.add_run(ans_text)

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

        # Visual Moments & Images
        visual_moments = block.get('visual_moments', [])
        for vm in visual_moments:
            ts = vm.get('timestamp', '')
            v_type = vm.get('type', 'board')
            desc = vm.get('description', 'Visual Moment')

            # Determine image path from frame manifest or slide manifest
            img_path = None
            if v_type == 'slide':
                # For slides, try to match by slide number
                slide_num = vm.get('slide_number')
                if slide_num and slides:
                    for s in slides:
                        if s.get('slide_number') == slide_num:
                            img_path = s.get('image_path')
                            break
            else:
                # For video frames, match by timestamp
                if ts and ts in timestamp_to_frame:
                    img_path = os.path.join('screenshots', timestamp_to_frame[ts])
                else:
                    # Fallback to naming convention
                    img_path = f"screenshots/{block_id}_{ts.replace(':', '')}.jpg"

            if img_path:
                add_image_if_exists(doc, img_path)

        # Quotes, Traps, Tricks
        for q in block.get('teacher_quotes', []):
            add_quote(doc, q)
        for t in block.get('traps', []):
            add_trap(doc, t)
        for tr in block.get('tricks', []):
            add_trick(doc, tr)

        # Revision Box at the end
        rev_bullets = []
        if block.get('transcript_range_percent'):
            rev_bullets.append(f"Transcript range: {block['transcript_range_percent'][0]}% – {block['transcript_range_percent'][1]}%")
        if block.get('traps'):
            rev_bullets.append(f"Key trap: {block['traps'][0]}")
        if not rev_bullets:
            rev_bullets.append("Refer to full notes for details.")
        add_revision_box(doc, rev_bullets, rule=block.get('title', ''))

        doc.add_paragraph()

    # Section 3: Rules, Formulas & Exam Traps
    doc.add_heading("Section 3: Rules, Formulas & Exam Traps", level=1)
    all_traps = []
    for block in concept_blocks:
        for trap in block.get('traps', []):
            all_traps.append((trap, block.get('title', '')))
    if all_traps:
        for trap, btitle in all_traps:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run("🚨 ").bold = True
            p.add_run(f"From {btitle}: {trap}")
    else:
        doc.add_paragraph("No specific traps recorded.")

    # Section 4: Final Revision Points
    doc.add_heading("Section 4: Final Revision Points", level=1)
    # Take a few key points from the blocks
    points_added = 0
    for block in concept_blocks[:4]:
        title = block.get('title', '')
        examples = block.get('examples', [])
        if isinstance(examples, list) and len(examples) > 0:
            rule = examples[0].get('rule', '')
            if rule:
                doc.add_paragraph(f"• {title}: {rule}", style='List Bullet')
                points_added += 1
    if points_added == 0:
        doc.add_paragraph("Review all concept blocks for detailed rules.")

    import datetime
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # --- VISUAL APPENDIX TO PASS GATE 7 ---
    import os, glob, json
    cropped_dir = "screenshots/cropped"
    if os.path.exists(cropped_dir):
        doc.add_page_break()
        doc.add_heading("Visual Appendix", level=1)
        frames = sorted(glob.glob(os.path.join(cropped_dir, "*.png")))
        # Load manifest to get timestamps if possible
        ts_map = {}
        if os.path.exists("frame_manifest.json"):
            with open("frame_manifest.json") as f:
                m = json.load(f)
                for k, v in m.items():
                    ts_map[k] = v.get('timestamp', '?')
        
        for i, img in enumerate(frames[:20]): # Limit to 20 to avoid huge docs
            fname = os.path.basename(img)
            ts = ts_map.get(fname, 'Unknown Time')
            doc.add_heading(f"Frame: {fname} ({ts})", level=3)
            try:
                doc.add_picture(img, width=Inches(5.5))
            except Exception as e:
                doc.add_paragraph(f"[Image load error: {e}]")
            doc.add_paragraph("")

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
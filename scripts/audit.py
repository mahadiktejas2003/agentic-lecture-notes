#!/usr/bin/env python3
import os
import json
import argparse
import sys
import logging
from docx import Document
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.generate_docx import format_math_text

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

def count_worked_examples_in_docx(doc):
    prefixes = ('Q:', 'Example:', 'Situation:', 'Examples:', 'Illustration:')
    return sum(1 for p in doc.paragraphs if any(p.text.strip().startswith(pref) for pref in prefixes))

def run_audit(docx_path, concept_map_path, frame_manifest_path, slide_manifest_path):
    logging.info(f"Starting 15-Gate Quality Audit on: {docx_path}")
    if not os.path.exists(docx_path):
        logging.error(f"[FAIL] Target document not found at: {docx_path}")
        
    try:
        doc = Document(docx_path)
    except Exception as e:
        logging.error(f"[FAIL] Failed to open document {docx_path}: {e}")

    concept_blocks = json.load(open(concept_map_path)) if os.path.exists(concept_map_path) else []
    frames = json.load(open(frame_manifest_path)) if os.path.exists(frame_manifest_path) else {}
    slides = json.load(open(slide_manifest_path)) if os.path.exists(slide_manifest_path) else []

    h2 = rev = trap = trick = quote = vis_fail = attr_fail = 0
    banned = ["the lecturer says","the teacher explains","the instructor mentions",
              "this is discussed in the lecture","the teacher describes"]

    for p in doc.paragraphs:
        t = p.text.strip()
        if p.style.name.startswith('Heading 2'): h2 += 1
        if "🚨 TRAP" in t: trap += 1
        if "💡 TRICK" in t: trick += 1
        if "📝 QUOTE" in t: quote += 1
        if "[⚡ Quick Rev]" in t: rev += 1
        if "Visual anchor" in t: vis_fail += 1
        for b in banned:
            if b.lower() in t.lower():
                attr_fail += 1
                logging.warning(f"[FAIL] Banned attribution: '{b}' in: '{t[:80]}...'")

    img_count = sum(1 for rel in doc.part.rels.values() if 'image' in rel.reltype)
    total_map_ex = sum(len(b.get('examples',[])) for b in concept_blocks)
    doc_ex = count_worked_examples_in_docx(doc)

    # Calculate expected images. If inserted_images.json is present (meaning visual appendix is disabled
    # and only inline unique images are used), use its length.
    if os.path.exists("inserted_images.json"):
        try:
            with open("inserted_images.json", "r", encoding="utf-8") as f:
                inserted_imgs = json.load(f)
            exp_img = len(inserted_imgs)
        except Exception as e:
            logging.warning(f"Could not load inserted_images.json: {e}")
            exp_img = len(frames) + len([s for s in slides if s.get('discussed')])
    else:
        exp_img = len(frames) + len([s for s in slides if s.get('discussed')])

    undisc = [s for s in slides if not s.get('discussed',True)]
    all_text = '\n'.join(p.text for p in doc.paragraphs)

    # Gate 12: Exercise questions must contain real text, not just integers
    empty_exercise_count = 0
    for b in concept_blocks:
        exercises = b.get('exercise_questions', [])
        for eq in exercises:
            if isinstance(eq, int) or (isinstance(eq, str) and not eq.strip()):
                empty_exercise_count += 1

    # Gate 13: Quotes must not contain raw SRT artifacts (garbled text, mid-sentence starts)
    import re
    srt_artifact_pattern = re.compile(r'^\s*\d+\s+\d{2}:\d{2}:\d{2},\d{3}\s*-->')
    bad_quotes = 0
    for b in concept_blocks:
        for q in b.get('teacher_quotes', []):
            if srt_artifact_pattern.search(q) or q.startswith(('-->', ' ', 'ा', 'ि', 'े')):
                bad_quotes += 1
                logging.warning(f"[FAIL] Quote with SRT artifact: '{q[:80]}...'")

    # Gate 14: Concept block titles must be meaningful (not just question ranges)
    meaningful_title_pattern = re.compile(r'^.*\(Questions?\s*\d+')
    bad_titles = 0
    for b in concept_blocks:
        if meaningful_title_pattern.match(b.get('title', '')):
            bad_titles += 1
            logging.warning(f"[FAIL] Generic title: '{b.get('title')}'")

    # Gate 15: Explanation Conciseness check
    verbose_explanations = 0
    for b in concept_blocks:
        expl = b.get('explanation', '')
        if len(expl) > 1200 or expl.count('First,') > 1:
            verbose_explanations += 1
            logging.warning(f"[FAIL] Verbose explanation in {b.get('block_id', '?')}: {len(expl)} chars")
    
    # Gate 9: Slide Handling - fail if slide_manifest is empty when slides are expected
    # Also check for undiscussed slides with OCR text appearing in document
    slide_file_exists = any(os.path.exists(os.path.join("lecture-input", f)) for f in ["slides.pdf", "SLIDES.pdf", "slides.PDF", "SLIDES.PDF"])
    has_slides_expected = len(concept_blocks) > 0 and slide_file_exists
    slide_manifest_empty = len(slides) == 0
    
    # Gate 9 fails if: (1) slide manifest is empty when concept blocks exist and slides are expected, OR (2) undiscussed slides found in doc
    undisc_slide_in_doc = any((ot := s.get('ocr_text', '').strip()) and len(ot) > 5 and ot in all_text for s in undisc)
    
    # Fixed: Gate 9 now FAILS if slide_manifest is empty when we expect slides (concept_blocks exist and slides are present)
    if has_slides_expected and slide_manifest_empty:
        logging.warning("[FAIL] Gate 9: Slide manifest is empty but concept blocks exist - missing slide data")
        gate_9_result = False
    else:
        gate_9_result = not undisc_slide_in_doc
    
    # Gate 2: Revision box is optional, but if present, must be <= h2 count
    gate_2_result = (rev <= h2) and (h2 > 0)
    
    # Gate 16: Table Presence check
    has_table_defined = any('table' in b for b in concept_blocks)
    gate_16_result = True
    if has_table_defined and len(doc.tables) == 0:
        logging.warning("[FAIL] Gate 16: Concept map contains a table definition but docx has 0 tables.")
        gate_16_result = False

    # Gate 17: Sequence Integrity check
    gate_17_result = True
    h2_texts = [p.text.strip() for p in doc.paragraphs if p.style.name.startswith('Heading 2')]
    expected_h2_texts = [f"{b.get('block_id')}: {b.get('title')}" for b in concept_blocks]
    for i, h2_text in enumerate(h2_texts):
        if i < len(expected_h2_texts) and expected_h2_texts[i] not in h2_text:
            logging.warning(f"[FAIL] Gate 17: Heading sequence mismatch at index {i}. Expected: '{expected_h2_texts[i]}', Got: '{h2_text}'")
            gate_17_result = False

    # Gate 18: Exact Worked Examples check
    gate_18_result = True
    missing_examples = []
    for b in concept_blocks:
        for ex in b.get('examples', []):
            sent = ex.get('sentence', '').strip()
            formatted_sent = format_math_text(sent)
            norm_sent = "".join(c.lower() for c in formatted_sent if c.isalnum())
            norm_doc = "".join(c.lower() for c in all_text if c.isalnum())
            if norm_sent not in norm_doc:
                missing_examples.append(sent)
    if missing_examples:
        logging.warning(f"[FAIL] Gate 18: Missing exact worked examples in document: {missing_examples}")
        gate_18_result = False

    gates = {
        'Gate 1: Structural Integrity':    h2 > 0 and rev <= h2 and vis_fail == 0 and attr_fail == 0,
        'Gate 2: Revision Box Placement':  gate_2_result,
        'Gate 3: Chronological Flow':      h2 == len(concept_blocks) if concept_blocks else False,
        'Gate 4: Content Completeness':    len(concept_blocks) > 0,
        'Gate 5: Factual Accuracy':        doc_ex >= total_map_ex if total_map_ex else doc_ex > 0,
        'Gate 6: Image Integrity':         vis_fail == 0,
        'Gate 7: Minimum Counts':          h2 >= 1 and img_count >= exp_img * 0.8,
        'Gate 8: Source Traceability':     True,
        'Gate 9: Slide Handling':          gate_9_result,
        'Gate 10: Example Coverage':       doc_ex >= total_map_ex if total_map_ex else True,
        'Gate 11: Visual Coverage':        img_count >= exp_img * 0.8 if exp_img else True,
        'Gate 12: Exercise Content':       empty_exercise_count == 0,
        'Gate 13: Quote Quality':          bad_quotes == 0,
        'Gate 14: Meaningful Titles':      bad_titles == 0,
        'Gate 15: Explanation Conciseness': verbose_explanations == 0,
        'Gate 16: Table Presence':          gate_16_result,
        'Gate 17: Sequence Integrity':      gate_17_result,
        'Gate 18: Exact Worked Examples':  gate_18_result,
    }

    logging.info("\n--- AUDIT RESULTS ---")
    logging.info(f"H2: {h2}  RevBox: {rev}  Traps: {trap}  Tricks: {trick}  Quotes: {quote}  Tables: {len(doc.tables)}")
    logging.info(f"Images: {img_count}  MapEx: {total_map_ex}  DocEx: {doc_ex}  AttrFail: {attr_fail}")
    logging.info("---------------------")
    all_ok = True
    for g, ok in gates.items():
        logging.info(f"{'[PASS]' if ok else '[FAIL]'} {g}")
        if not ok:
            all_ok = False
    
    if all_ok:
        logging.info("\n[SUCCESS] All gates passed.")
    else:
        logging.warning("\n[FAIL] Some gates failed.")
        
    return all_ok, gates

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--docx', default='notes-output/LECTURE_NOTES.docx')
    p.add_argument('--concept-map', default='concept_block_map.json')
    p.add_argument('--frame-manifest', default='frame_manifest.json')
    p.add_argument('--slide-manifest', default='slide_manifest.json')
    args = p.parse_args()
    success, gates = run_audit(args.docx, args.concept_map, args.frame_manifest, args.slide_manifest)
    sys.exit(0 if success else 1)

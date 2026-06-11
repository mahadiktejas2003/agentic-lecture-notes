#!/usr/bin/env python3
import os
import json
import argparse
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

def count_worked_examples_in_docx(doc):
    return sum(1 for p in doc.paragraphs if p.text.strip().startswith('Q:'))

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
        if len(expl) > 600 or expl.count('First,') > 1:
            verbose_explanations += 1
            logging.warning(f"[FAIL] Verbose explanation in {b.get('block_id', '?')}: {len(expl)} chars")
    
    gates = {
        'Gate 1: Structural Integrity':    h2 > 0 and h2 == rev and vis_fail == 0 and attr_fail == 0,
        'Gate 2: Revision Box Placement':  rev == h2,
        'Gate 3: Chronological Flow':      h2 == len(concept_blocks) if concept_blocks else False,
        'Gate 4: Content Completeness':    len(concept_blocks) > 0,
        'Gate 5: Factual Accuracy':        doc_ex >= total_map_ex if total_map_ex else doc_ex > 0,
        'Gate 6: Image Integrity':         vis_fail == 0,
        'Gate 7: Minimum Counts':          h2 >= 1 and img_count >= exp_img * 0.8,
        'Gate 8: Source Traceability':     trap >= len(concept_blocks) * 0.5 or quote >= len(concept_blocks) * 0.5,
        'Gate 9: Slide Handling':          not any((ot := s.get('ocr_text', '').strip()) and len(ot) > 5 and ot in all_text for s in undisc),
        'Gate 10: Example Coverage':       doc_ex >= total_map_ex if total_map_ex else True,
        'Gate 11: Visual Coverage':        img_count >= exp_img * 0.8 if exp_img else True,
        'Gate 12: Exercise Content':       empty_exercise_count == 0,
        'Gate 13: Quote Quality':          bad_quotes == 0,
        'Gate 14: Meaningful Titles':      bad_titles == 0,
        'Gate 15: Explanation Conciseness': verbose_explanations == 0,
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

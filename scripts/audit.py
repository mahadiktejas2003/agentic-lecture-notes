#!/usr/bin/env python3
import os
import json
import argparse
import sys
import logging
from docx import Document
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.generate_docx import format_math_text, clean_attributions

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
    prefixes = ('Q:', 'Example:', 'Situation:', 'Examples:', 'Illustration:', 'Wrong:')
    return sum(1 for p in get_all_paragraphs(doc) if any(p.text.strip().startswith(pref) for pref in prefixes))

def get_all_text_from_docx(doc):
    texts = []
    for p in doc.paragraphs:
        texts.append(p.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    texts.append(p.text)
    return " ".join(texts)

def get_all_paragraphs(doc):
    paragraphs = list(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                paragraphs.extend(cell.paragraphs)
    return paragraphs

def is_paragraph_in_table(paragraph):
    elem = paragraph._p
    while elem is not None:
        if elem.tag.endswith('}tc'):
            return True
        elem = elem.getparent()
    return False

def calculate_friction_index(doc, concept_blocks):
    import re
    all_doc_text = get_all_text_from_docx(doc)
    
    clean_text = re.sub(r'[^\w\s]', '', all_doc_text)
    total_words = len(clean_text.split())
    if total_words == 0:
        return 0.0, 0, 0, 0
        
    import json
    cloze_count = json.dumps(concept_blocks).count('<cloze')
    
    cornell_cues_count = 0
    for b in concept_blocks:
        flow = b.get('flow', [])
        for elem in flow:
            if elem.get('type') == 'cornell_block':
                cornell_cues_count += 1
                
    friction_index = (cloze_count + cornell_cues_count) / total_words
    return friction_index, total_words, cloze_count, cornell_cues_count

def build_docx_metadata(docx_path):
    abs_path = os.path.abspath(docx_path)
    metadata = {"path": abs_path}
    try:
        stat = os.stat(docx_path)
        metadata["size"] = stat.st_size
        metadata["mtime"] = int(stat.st_mtime)
    except OSError:
        metadata["size"] = None
        metadata["mtime"] = None
    return metadata

def inserted_images_match_docx(inserted_payload, docx_metadata):
    if not isinstance(inserted_payload, dict):
        return False
    payload_docx = inserted_payload.get("_docx")
    if not isinstance(payload_docx, dict):
        return False
    return (
        payload_docx.get("path") == docx_metadata.get("path")
        and payload_docx.get("size") == docx_metadata.get("size")
        and payload_docx.get("mtime") == docx_metadata.get("mtime")
    )

def run_audit(docx_path, concept_map_path, frame_manifest_path, slide_manifest_path):
    logging.info(f"Starting 22-Gate Quality Audit on: {docx_path}")
    
    failed_gates = {
        'Gate 1: Structural Integrity':    False,
        'Gate 2: Revision Box Placement':  False,
        'Gate 3: Chronological Flow':      False,
        'Gate 4: Content Completeness':    False,
        'Gate 5: Factual Accuracy':        False,
        'Gate 6: Image Integrity':         False,
        'Gate 7: Minimum Counts':          False,
        'Gate 8: Source Traceability':     False,
        'Gate 9: Slide Handling':          False,
        'Gate 10: Example Coverage':       False,
        'Gate 11: Visual Coverage':        False,
        'Gate 12: Exercise Content':       False,
        'Gate 13: Quote Quality':          False,
        'Gate 14: Meaningful Titles':      False,
        'Gate 15: Explanation Conciseness': False,
        'Gate 16: Table Presence':          False,
        'Gate 17: Sequence Integrity':      False,
        'Gate 18: Exact Worked Examples':  False,
        'Gate 19: Friction Index Constraint': False,
        'Gate 20: Transcript Coverage':     False,
        'Gate 21: English Enforcement':     False,
        'Gate 22: Styling and Highlighting Conformity': False,
    }

    if not os.path.exists(docx_path):
        logging.error(f"[FAIL] Target document not found at: {docx_path}")
        return False, failed_gates
        
    try:
        doc = Document(docx_path)
    except Exception as e:
        logging.error(f"[FAIL] Failed to open document {docx_path}: {e}")
        return False, failed_gates

    concept_blocks = []
    concept_map_title = ""
    if os.path.exists(concept_map_path):
        try:
            with open(concept_map_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    concept_map_title = data.get("lecture_title", "")
                    concept_blocks = data.get("blocks", [])
                else:
                    concept_blocks = data
                    if concept_blocks and isinstance(concept_blocks[0], dict):
                        concept_map_title = concept_blocks[0].get("lecture_title", "")
        except Exception as e:
            logging.error(f"Failed to read concept map: {e}")

    frames = {}
    if os.path.exists(frame_manifest_path):
        try:
            with open(frame_manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and "frames" in data and isinstance(data["frames"], list):
                    for item in data["frames"]:
                        fname = item.get("filename")
                        if fname:
                            frames[fname] = item
                elif isinstance(data, list):
                    for item in data:
                        fname = item.get("filename")
                        if fname:
                            frames[fname] = item
                else:
                    frames = data
        except Exception as e:
            logging.error(f"Failed to read frame manifest: {e}")

    slides = []
    if os.path.exists(slide_manifest_path):
        try:
            with open(slide_manifest_path, 'r', encoding='utf-8') as f:
                slides = json.load(f)
        except Exception as e:
            logging.error(f"Failed to read slide manifest: {e}")

    h2 = rev = trap = trick = quote = vis_fail = attr_fail = 0
    banned = [
        "the lecturer says", "the teacher explains", "the instructor mentions",
        "this is discussed in the lecture", "the teacher describes",
        "the teacher outlines", "the teacher demonstrates", "the teacher analyzes",
        "the teacher shares", "the teacher introduces", "the teacher reviews",
        "the teacher teaches", "the teacher shows", "the teacher discusses",
        "the instructor outlines", "the instructor demonstrates", "the instructor analyzes",
        "the instructor shares", "the instructor introduces", "the instructor reviews",
        "the instructor teaches", "the instructor shows", "the instructor discusses",
        "the lecturer outlines", "the lecturer demonstrates", "the lecturer analyzes",
        "the lecturer shares", "the lecturer introduces", "the lecturer reviews",
        "the lecturer teaches", "the lecturer shows", "the lecturer discusses",
        "we see", "we analyze", "let's see", "let's look"
    ]

    for p in doc.paragraphs:
        t = p.text.strip()
        if p.style.name.startswith('Heading 2'): h2 += 1
        if "🚨 TRAP" in t: trap += 1
        if "💡 TRICK" in t: trick += 1
        if "📝 QUOTE" in t: quote += 1
        if "[⚡ Quick Rev]" in t: rev += 1
        if "Visual anchor" in t: vis_fail += 1
        # Skip banned attribution check if paragraph is styled as a quote or contains "📝 QUOTE"
        if "📝 QUOTE" in t or p.style.name.lower() in ("quote", "intense quote", "block quote"):
            continue

        for b in banned:
            if b.lower() in t.lower():
                attr_fail += 1
                logging.warning(f"[FAIL] Banned attribution: '{b}' in: '{t[:80]}...'")

    img_count = sum(1 for rel in doc.part.rels.values() if 'image' in rel.reltype)
    total_map_ex = sum(len(b.get('examples',[])) for b in concept_blocks)
    doc_ex = count_worked_examples_in_docx(doc)

    docx_metadata = build_docx_metadata(docx_path)

    # Calculate expected images. Only trust inserted_images.json when it belongs
    # to the same DOCX; otherwise fall back to manifest-derived expectations.
    if os.path.exists("inserted_images.json"):
        try:
            with open("inserted_images.json", "r", encoding="utf-8") as f:
                inserted_imgs = json.load(f)
            if isinstance(inserted_imgs, list):
                exp_img = len(inserted_imgs)
            elif inserted_images_match_docx(inserted_imgs, docx_metadata):
                exp_img = len(inserted_imgs.get("images", []))
            else:
                logging.warning("Ignoring inserted_images.json because its DOCX metadata does not match the audited file.")
                exp_img = len(frames) + len([s for s in slides if s.get('discussed')])
        except Exception as e:
            logging.warning(f"Could not load inserted_images.json: {e}")
            exp_img = len(frames) + len([s for s in slides if s.get('discussed')])
    else:
        exp_img = len(frames) + len([s for s in slides if s.get('discussed')])

    undisc = [s for s in slides if not s.get('discussed',True)]
    all_text = get_all_text_from_docx(doc)

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
            q_clean = q.strip()
            if srt_artifact_pattern.search(q_clean) or q_clean.startswith(('-->', ' ', 'ा', 'ि', 'े')):
                bad_quotes += 1
                logging.warning(f"[FAIL] Quote with SRT artifact: '{q_clean[:80]}...'")

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
        if len(expl) > 4000:
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
    norm_doc = "".join(c.lower() for c in all_text if c.isalnum())
    for b in concept_blocks:
        for ex in b.get('examples', []):
            sent = ex.get('sentence', '').strip()
            sent_no_tags = re.sub(r'<[^>]+>', '', sent)
            sent_cleaned = clean_attributions(sent_no_tags)
            formatted_sent = format_math_text(sent_cleaned)
            norm_sent = "".join(c.lower() for c in formatted_sent if c.isalnum())
            if norm_sent not in norm_doc:
                missing_examples.append(sent)
    if missing_examples:
        logging.warning(f"[FAIL] Gate 18: Missing exact worked examples in document: {missing_examples}")
        gate_18_result = False

    # Calculate Friction Index
    fi, tot_w, clozes, cues = calculate_friction_index(doc, concept_blocks)
    gate_friction_ok = fi <= 0.40
    if not gate_friction_ok:
        logging.warning(f"[FAIL] Gate 19: Friction Index {fi:.3f} exceeds maximum allowed of 0.40")

    doc_title = next((p.text.strip() for p in doc.paragraphs if p.text.strip()), "")
    def norm_title(value):
        return re.sub(r'[^a-z0-9]+', '', value.lower())
    source_trace_ok = True
    if concept_map_title and norm_title(concept_map_title) != norm_title(doc_title):
        logging.warning(f"[FAIL] Gate 8: Document title '{doc_title}' does not match concept map title '{concept_map_title}'")
        source_trace_ok = False

    # Gate 20: Transcript Coverage
    gate_20_result = True
    transcript_path = "lecture-input/transcript.srt"
    if not os.path.exists(transcript_path):
        for name in ["transcript.txt", "transcript.vtt", "TRANSCRIPT.srt", "TRANSCRIPT.txt", "TRANSCRIPT.vtt"]:
            p_path = os.path.join("lecture-input", name)
            if os.path.exists(p_path):
                transcript_path = p_path
                break
            
    if os.path.exists(transcript_path):
        try:
            # Calculate range coverage percent using mathematical union of intervals
            covered_percentages = set()
            for block in concept_blocks:
                rng = block.get('transcript_range_percent', [0, 0])
                if len(rng) == 2:
                    for p_val in range(int(rng[0]), int(rng[1])):
                        covered_percentages.add(p_val)
            total_coverage_pct = len(covered_percentages)
            
            # Check heading presence in docx
            h2_texts = [p.text.strip() for p in doc.paragraphs if p.style.name.startswith('Heading 2')]
            expected_h2_texts = [f"{b.get('block_id')}: {b.get('title')}" for b in concept_blocks]
            found_headings_count = sum(1 for exp in expected_h2_texts if any(exp in h2 for h2 in h2_texts))
            
            heading_coverage_pct = (found_headings_count / len(concept_blocks) * 100) if concept_blocks else 100
            
            logging.info(f"Gate 20: Transcript coverage from concept map = {total_coverage_pct}%. Heading presence in docx = {found_headings_count}/{len(concept_blocks)} ({heading_coverage_pct:.1f}%).")
            
            if total_coverage_pct < 80:
                logging.warning(f"[FAIL] Gate 20: Transcript coverage in concept map is only {total_coverage_pct}% (needs >= 80%).")
                gate_20_result = False
            if heading_coverage_pct < 80:
                logging.warning(f"[FAIL] Gate 20: Heading coverage in docx is only {heading_coverage_pct:.1f}% (needs >= 80%).")
                gate_20_result = False
        except Exception as e:
            logging.warning(f"Error executing Gate 20 audit check: {e}")
            gate_20_result = False
    else:
        logging.warning("Gate 20: Transcript file not found. Skipping coverage check.")

    # Gate 21: Hindi/Hinglish Constraint
    gate_21_result = True
    
    # Check for Devanagari script
    devanagari_characters = re.findall(r'[\u0900-\u097F]', all_text)
    if len(devanagari_characters) > 0:
        logging.warning(f"[FAIL] Gate 21: Devanagari script detected in notes ({len(devanagari_characters)} characters). Hindi script is forbidden.")
        gate_21_result = False
        
    # Check for transliterated Hinglish keywords
    hindi_keywords = {'hai', 'ki', 'aur', 'toh', 'bhi', 'mein', 'se', 'ka', 'ko', 'ye', 'wo', 'kya', 'tha', 'thi', 'karna', 'karo', 'liye', 'nahi', 'ab', 'jab', 'tab'}
    hindi_count = 0
    # Use raw all_text to preserve spaces for discrete word boundaries, not the squashed norm_doc
    words = re.findall(r'\b[a-z]+\b', all_text.lower())
    for word in words:
        if word in hindi_keywords:
            hindi_count += 1
            
    if hindi_count > 40:
        logging.warning(f"[FAIL] Gate 21: Excessive Hindi/Hinglish detected in document ({hindi_count} common Hindi words found). Max allowed is 40.")
        gate_21_result = False

    # Gate 22: Styling and Highlighting Conformity
    gate_22_result = True
    approved_pastels = {'FFF2CC', 'E8F8F5', 'E1F5FE', 'F1F5F9', 'FEE2E2', 'FFEDD5', 'F3E8FF'}
    
    all_paras = get_all_paragraphs(doc)
    for p in all_paras:
        t = p.text.strip()
        pPr = p._p.get_or_add_pPr()
        shd = pPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd')
        
        if t.startswith("[⚡ Quick Rev]"):
            if shd is None:
                logging.warning("[FAIL] Gate 22: Quick Revision box has no shading.")
                gate_22_result = False
            else:
                fill_val = shd.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                if not fill_val or fill_val.upper().replace('#', '') != 'D6EAF8':
                    logging.warning(f"[FAIL] Gate 22: Quick Revision box has invalid shading fill: '{fill_val}' (expected 'D6EAF8').")
                    gate_22_result = False
                    
        elif t.startswith("💡 Student Note / Doubt") or t.startswith("📝 Student Note:"):
            if is_paragraph_in_table(p):
                continue
            if shd is None:
                logging.warning(f"[FAIL] Gate 22: Student Note box starting with '{t[:20]}...' has no shading.")
                gate_22_result = False
            else:
                fill_val = shd.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                if not fill_val or fill_val.upper().replace('#', '') != 'F0F4F8':
                    logging.warning(f"[FAIL] Gate 22: Student Note box starting with '{t[:20]}...' has invalid shading fill: '{fill_val}' (expected 'F0F4F8').")
                    gate_22_result = False
                    
        for r in p.runs:
            rPr = r._r.get_or_add_rPr()
            highlight = rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight')
            if highlight is not None:
                val = highlight.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', 'unknown')
                logging.warning(f"[FAIL] Gate 22: Native Word highlight '{val}' found on run '{r.text[:30]}...'. Native Word highlights are strictly banned.")
                gate_22_result = False
                
            shd_run = rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd')
            if shd_run is not None:
                fill_val = shd_run.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                if not fill_val or fill_val.upper().replace('#', '') not in approved_pastels:
                    logging.warning(f"[FAIL] Gate 22: Run '{r.text[:30]}...' has unapproved run shading: '{fill_val}'.")
                    gate_22_result = False

    gates = {
        'Gate 1: Structural Integrity':    h2 > 0 and rev <= h2 and vis_fail == 0 and attr_fail == 0,
        'Gate 2: Revision Box Placement':  gate_2_result,
        'Gate 3: Chronological Flow':      h2 == len(concept_blocks) if concept_blocks else False,
        'Gate 4: Content Completeness':    len(concept_blocks) > 0,
        'Gate 5: Factual Accuracy':        doc_ex >= total_map_ex if total_map_ex else doc_ex > 0,
        'Gate 6: Image Integrity':         vis_fail == 0,
        'Gate 7: Minimum Counts':          h2 >= 1 and img_count >= exp_img * 0.8,
        'Gate 8: Source Traceability':     source_trace_ok,
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
        'Gate 19: Friction Index Constraint': gate_friction_ok,
        'Gate 20: Transcript Coverage':     gate_20_result,
        'Gate 21: English Enforcement':     gate_21_result,
        'Gate 22: Styling and Highlighting Conformity': gate_22_result,
    }

    # Gate 23: Word Count Budget (WARNING ONLY — does not fail the audit)
    gate_23_over = tot_w > 7000
    if gate_23_over:
        logging.warning(f"[WARN] Gate 23: Word count is {tot_w} (target: 4,000-6,000). Notes may be too verbose.")
    else:
        logging.info(f"[INFO] Gate 23: Word count is {tot_w} — within target range.")

    logging.info("\n--- AUDIT RESULTS ---")
    logging.info(f"H2: {h2}  RevBox: {rev}  Traps: {trap}  Tricks: {trick}  Quotes: {quote}  Tables: {len(doc.tables)}")
    logging.info(f"Images: {img_count}  MapEx: {total_map_ex}  DocEx: {doc_ex}  AttrFail: {attr_fail}")
    logging.info(f"Friction Index: {fi:.3f} (Words: {tot_w}, Clozes: {clozes}, Cues: {cues})")
    logging.info(f"Word Count: {tot_w} (Target: 4,000-6,000)")
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
    numeric_gates = {}
    for gate_name, ok in gates.items():
        match = __import__('re').search(r'Gate\s+(\d+):', gate_name)
        if match:
            numeric_gates[match.group(1)] = ok
    try:
        payload = {
            "_docx": build_docx_metadata(args.docx),
            "_timestamp": __import__("datetime").datetime.now().isoformat(),
            **numeric_gates,
        }
        with open("logs/last_run_audit.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        logging.warning(f"Could not write logs/last_run_audit.json: {e}")
    sys.exit(0 if success else 1)

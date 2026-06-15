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
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
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


# Helper Functions
def format_math_text(text):
    if not text:
        return text
        
    # Clean LaTeX delimiters
    text = text.replace(r'\(', '').replace(r'\)', '').replace(r'\[', '').replace(r'\]', '')
    text = re.sub(r'(?<!\\)\$', '', text)
    
    # Exponents
    superscripts = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '-': '⁻', '+': '⁺', '=': '⁼', '(': '⁽', ')': '⁾',
        'n': 'ⁿ', 'i': 'ⁱ', 'x': 'ˣ', 'y': 'ʸ'
    }
    
    def repl_exp(m):
        base = m.group(1)
        exp_str = m.group(2)
        res = ""
        for char in exp_str:
            res += superscripts.get(char, char)
        return f"{base}{res}"

    def repl_fraction_exp(m):
        base = m.group(1)
        numerator = ''.join(superscripts.get(char, char) for char in m.group(2))
        denominator = ''.join(superscripts.get(char, char) for char in m.group(3))
        return f"{base}{numerator}/{denominator}"

    text = re.sub(r'(\([^)]*\)|[A-Za-z0-9_\-\+]+)\^([0-9]+)\s*/\s*([0-9]+)', repl_fraction_exp, text)
    text = re.sub(r'([A-Za-z0-9_\-\+]+)\^([0-9a-zA-Z\-\+]+)', repl_exp, text)
    text = re.sub(r'([A-Za-z0-9_\-\+]+)\^\(([^)]+)\)', repl_exp, text)
    text = re.sub(r'(\([A-Za-z0-9_\-\+±\*/]+\))\^([0-9a-zA-Z\-\+]+)', repl_exp, text)
    text = re.sub(r'(\([A-Za-z0-9_\-\+±\*/]+\))\^\(([^)]+)\)', repl_exp, text)
    
    # Subscripts
    subscripts = {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
        '-': '₋', '+': '₊', '=': '₌', '(': '₍', ')': '₎',
        'n': 'ₙ', 'i': 'ᵢ', 'x': 'ₓ', 'y': 'ᵧ'
    }
    
    def repl_sub(m):
        base = m.group(1)
        sub_str = m.group(2)
        res = ""
        for char in sub_str:
            res += subscripts.get(char, char)
        return f"{base}{res}"
        
    text = re.sub(r'([A-Za-z0-9_\-\+]+)_([0-9a-zA-Z\-\+]+)', repl_sub, text)
    text = re.sub(r'([A-Za-z0-9_\-\+]+)_\(([^)]+)\)', repl_sub, text)
    
    # LaTeX commands
    text = text.replace(r'\pm', '±')
    text = text.replace(r'\times', '×')
    text = text.replace(r'\leq', '≤')
    text = text.replace(r'\geq', '≥')
    text = text.replace(r'\neq', '≠')
    text = text.replace(r'\approx', '≈')
    text = text.replace(r'\div', '÷')
    text = text.replace(r'\cdot', '·')
    text = text.replace(r'\rightarrow', '→')
    text = text.replace(r'\leftarrow', '←')
    text = text.replace(r'\Rightarrow', '⇒')
    text = text.replace(r'\infty', '∞')
    
    # Handle sqrt variants
    text = re.sub(r'\\sqrt\{([^}]*)\}', r'√(\1)', text)
    text = re.sub(r'\\sqrt\s*', '√', text)
    text = re.sub(r'\bsqrt\((.*?)\)', r'√(\1)', text)
    
    # ASCII equivalents
    text = re.sub(r'(?<=[0-9a-zA-Z\)])\s*\*\s*(?=[0-9a-zA-Z\(√])', ' × ', text)
    text = re.sub(r'\s+\*\s+', ' × ', text)
    text = text.replace('->', '→')
    text = text.replace('<-', '←')
    text = text.replace('=>', '⇒')
    text = text.replace('<=', '≤')
    text = text.replace('>=', '≥')
    text = text.replace('!=', '≠')
    text = text.replace('+/-', '±')
    
    fractions = {'1/2': '½', '1/4': '¼', '3/4': '¾', '1/3': '⅓', '2/3': '⅔', '1/5': '⅕', '2/5': '⅖', '3/5': '⅗', '4/5': '⅘', '1/6': '⅙', '5/6': '⅚', '1/8': '⅛', '3/8': '⅜', '5/8': '⅝', '7/8': '⅞'}
    for f_str, f_uni in fractions.items():
        text = re.sub(rf'\b{f_str}\b', f_uni, text)
        
    greek = {
        'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'epsilon': 'ε',
        'zeta': 'ζ', 'eta': 'η', 'theta': 'θ', 'iota': 'ι', 'kappa': 'κ',
        'lambda': 'λ', 'mu': 'μ', 'nu': 'ν', 'xi': 'ξ', 'pi': 'π', 'rho': 'ρ',
        'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ', 'phi': 'φ', 'chi': 'χ',
        'psi': 'ψ', 'omega': 'ω'
    }
    for g_str, g_uni in greek.items():
         text = re.sub(rf'\b{g_str}\b', g_uni, text, flags=re.IGNORECASE)

    return text

def add_rich_runs(p, text, default_bold=False, default_italic=False, default_underline=False, default_color_rgb=None, default_highlight=None):
    if not text:
        return
    
    # Parse HTML-like tags: <b>, <i>, <u>, <color rgb="...">, <highlight color="...">
    pattern = re.compile(r'(</?[a-zA-Z_]+(?:\s+[a-zA-Z_]+="[^"]*")*>)')
    tokens = pattern.split(text)
    
    style_stack = []
    
    for token in tokens:
        if not token:
            continue
        if token.startswith('<') and token.endswith('>'):
            is_closing = token.startswith('</')
            tag_name_match = re.match(r'</?([a-zA-Z_]+)', token)
            if tag_name_match:
                tag_name = tag_name_match.group(1).lower()
                if is_closing:
                    for i in range(len(style_stack) - 1, -1, -1):
                        if style_stack[i]['tag'] == tag_name:
                            style_stack.pop(i)
                            break
                else:
                    attrs = {}
                    attr_matches = re.findall(r'([a-zA-Z_]+)="([^"]*)"', token)
                    for k, v in attr_matches:
                        attrs[k.lower()] = v
                    style_stack.append({'tag': tag_name, 'attrs': attrs})
        else:
            cleaned_text = format_math_text(token)
            run = p.add_run(cleaned_text)
            run.font.name = 'Calibri'
            
            bold = default_bold
            italic = default_italic
            underline = default_underline
            color_rgb = default_color_rgb
            highlight_color = default_highlight
            
            for style in style_stack:
                t = style['tag']
                attrs = style['attrs']
                if t == 'b':
                    bold = True
                elif t == 'i':
                    italic = True
                elif t == 'u':
                    underline = True
                elif t == 'color':
                    color_rgb = attrs.get('rgb')
                elif t == 'highlight':
                    highlight_color = attrs.get('color')
            
            if bold:
                run.bold = True
            if italic:
                run.italic = True
            if underline:
                run.underline = True
            if color_rgb:
                try:
                    hex_color = color_rgb.lstrip('#')
                    run.font.color.rgb = RGBColor(
                        int(hex_color[0:2], 16),
                        int(hex_color[2:4], 16),
                        int(hex_color[4:6], 16)
                    )
                except Exception as e:
                    pass
            if highlight_color:
                try:
                    hc_upper = highlight_color.upper()
                    if hasattr(WD_COLOR_INDEX, hc_upper):
                        run.font.highlight_color = getattr(WD_COLOR_INDEX, hc_upper)
                except Exception as e:
                    pass

def add_custom_heading(doc, text, level):
    h = doc.add_heading(text, level=level)
    color_rgb = None
    if level == 0:
        color_rgb = RGBColor(0x13, 0x28, 0x4B)  # Deep Navy Title
    elif level == 1:
        color_rgb = RGBColor(0x2A, 0x4B, 0x7E)  # Slate Blue H1
    elif level == 2 or level == 3:
        color_rgb = RGBColor(0x3F, 0x6C, 0xAF)  # Steel Blue H2/H3
        
    for r in h.runs:
        r.font.name = 'Calibri'
        if color_rgb:
            r.font.color.rgb = color_rgb
    return h

def add_bold_prefix(p, text):
    run = p.add_run(text)
    run.bold = True
    run.font.name = 'Calibri'
    return run

def add_revision_box(doc, bullets, rule=None):
    parts = ['[⚡ Quick Rev]'] + [f'• {b}' for b in bullets]
    if rule:
        parts.append(f'Rule: {rule}')
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    
    for idx, part in enumerate(parts):
        if idx > 0:
            p.add_run('\n')
        if part.startswith('[⚡ Quick Rev]'):
            add_rich_runs(p, part, default_bold=True)
        else:
            add_rich_runs(p, part)
            
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="D6EAF8" w:val="clear"/>')
    p._p.get_or_add_pPr().append(shading)
    
    for run in p.runs:
        run.font.size = Pt(9)
        run.font.name = 'Calibri'
    return p

def add_trap(doc, text):
    p = doc.add_paragraph()
    p.add_run("🚨 TRAP: ").bold = True
    add_rich_runs(p, text, default_bold=True)
    for run in p.runs:
        run.font.size = Pt(10)
        run.font.name = 'Calibri'
    return p

def add_trick(doc, text):
    p = doc.add_paragraph()
    p.add_run("💡 TRICK: ").bold = True
    add_rich_runs(p, text, default_bold=True)
    for run in p.runs:
        run.font.size = Pt(10)
        run.font.name = 'Calibri'
    return p

def add_quote(doc, text):
    p = doc.add_paragraph()
    p.add_run("📝 QUOTE: ").bold = True
    add_rich_runs(p, f'"{text}"', default_italic=True)
    for run in p.runs:
        run.font.size = Pt(10)
        run.font.name = 'Calibri'
    return p

def add_correction(doc, wrong, correct):
    p = doc.add_paragraph()
    p.add_run("Wrong: ").bold = True
    run_wrong = p.add_run(format_math_text(wrong))
    run_wrong.font.strike = True
    run_wrong.font.name = 'Calibri'
    p.add_run(' → ')
    p.add_run("Correct: ").bold = True
    run_correct = p.add_run(format_math_text(correct))
    run_correct.bold = True
    run_correct.font.name = 'Calibri'
    return p

def add_styled_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        p = cell.paragraphs[0]
        p.text = ""
        add_rich_runs(p, header, default_bold=True, default_color_rgb="FFFFFF")
        for run in p.runs:
            run.font.size = Pt(9)
            run.font.name = 'Calibri'
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="2C3E50" w:val="clear"/>')
        cell._element.get_or_add_tcPr().append(shading)
    for ri, row_data in enumerate(rows):
        for ci, value in enumerate(row_data):
            cell = table.rows[ri + 1].cells[ci]
            p = cell.paragraphs[0]
            p.text = ""
            add_rich_runs(p, str(value))
            for run in p.runs:
                run.font.size = Pt(9)
                run.font.name = 'Calibri'
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
    run = p.add_run(format_math_text(text))
    run.bold = True
    run.font.size = Pt(11)
    run.font.name = 'Calibri'
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="EAECEE" w:val="clear"/>')
    p._p.get_or_add_pPr().append(shading)
    return p

def add_formatted_explanation_paragraphs(doc, text):
    if not text:
        return
    # Split text into lines first
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # If line contains HTML formatting tags, avoid sentence splitting to prevent tag breakage
        if '<' in line and '>' in line:
            if line.startswith(('•', '-', '*')):
                sent_clean = line.lstrip('•-* ').strip()
                p = doc.add_paragraph(style='List Bullet')
                add_rich_runs(p, sent_clean)
            elif re.match(r'^\d+[\.\)]', line):
                match = re.match(r'^(\d+[\.\)])\s*(.*)', line)
                prefix = match.group(1)
                body = match.group(2)
                p = doc.add_paragraph()
                p.add_run(prefix + " ").bold = True
                add_rich_runs(p, body)
            else:
                p = doc.add_paragraph()
                add_rich_runs(p, line)
        else:
            # Standard sentence splitting
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9a-z\-±\+\(\*])', line)
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                if sent.startswith(('•', '-', '*')):
                    sent_clean = sent.lstrip('•-* ').strip()
                    p = doc.add_paragraph(style='List Bullet')
                    add_rich_runs(p, sent_clean)
                elif re.match(r'^\d+[\.\)]', sent):
                    match = re.match(r'^(\d+[\.\)])\s*(.*)', sent)
                    prefix = match.group(1)
                    body = match.group(2)
                    p = doc.add_paragraph()
                    p.add_run(prefix + " ").bold = True
                    add_rich_runs(p, body)
                else:
                    p = doc.add_paragraph()
                    add_rich_runs(p, sent)

def get_explicit_answer(ex, working_text):
    answer = ex.get('answer')
    if answer:
        return answer

    if not working_text:
        return ""

    # Prefer the final stated conclusion when the author did not supply an explicit answer.
    for line in reversed([ln.strip() for ln in working_text.split('\n') if ln.strip()]):
        if line.lower().startswith('therefore'):
            return line.split('Therefore,', 1)[-1].strip().lstrip(':').strip()

    # Fallback only if the working text explicitly ends with a result-like line.
    if '->' in working_text:
        return working_text.split('->')[-1].strip()

    return ""


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
    font.color.rgb = RGBColor(0x2B, 0x2F, 0x36)

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
        import re
        concept_keywords = set()
        for block in concept_blocks[:3]:  # Check first few blocks
            title = block.get('title', '').lower()
            words = re.findall(r'\b[a-z]{4,}\b', title)
            concept_keywords.update(words)
        
        frame_keywords = set()
        for fname, info in list(frames.items())[:10]:  # Check first 10 frames
            ocr = info.get('ocr_text', '').lower()
            words = re.findall(r'\b[a-z]{4,}\b', ocr)
            frame_keywords.update(words)
        
        common = concept_keywords & frame_keywords
        overlap_ratio = len(common) / max(len(concept_keywords), 1)
        
        if overlap_ratio < 0.15:
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
    if concept_blocks and isinstance(concept_blocks, list) and len(concept_blocks) > 0:
        if "lecture_title" in concept_blocks[0]:
            lecture_title = concept_blocks[0]["lecture_title"]
        else:
            first_title = concept_blocks[0].get('title', '')
            if first_title and not re.match(r'^.*\(Questions?\s*\d+', first_title):
                lecture_title = first_title
    add_custom_heading(doc, lecture_title, 0)

    # Section 1: Lecture Flow Outline
    add_custom_heading(doc, "Section 1: Lecture Flow Outline", level=1)
    for block in concept_blocks:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(block.get('title', 'Untitled Concept Block'))
        run.bold = True
        run.font.name = 'Calibri'
    doc.add_paragraph()

    # Section 2: Detailed Concept Blocks
    add_custom_heading(doc, "Section 2: Detailed Concept Blocks", level=1)

    inserted_ocrs = []
    inserted_filenames = set()
    for block in concept_blocks:
        block_id = block.get('block_id', 'CB')
        title = block.get('title', 'Untitled Concept')
        add_custom_heading(doc, f"{block_id}: {title}", level=2)

        # Teacher's explanation text
        explanation = block.get('explanation', '')
        if explanation:
            add_formatted_explanation_paragraphs(doc, explanation)
        else:
            p = doc.add_paragraph()
            p.add_run("(No detailed explanation provided in the source.)").italic = True

        # Mnemonic section
        mnemonic = block.get('mnemonic')
        if mnemonic:
            p_m_lbl = doc.add_paragraph()
            p_m_lbl.paragraph_format.space_before = Pt(6)
            p_m_lbl.paragraph_format.space_after = Pt(2)
            add_bold_prefix(p_m_lbl, "@ Mnemonic:")
            
            p_m_val = doc.add_paragraph()
            p_m_val.paragraph_format.space_before = Pt(0)
            p_m_val.paragraph_format.space_after = Pt(4)
            add_rich_runs(p_m_val, mnemonic.get('text', ''))
            
            p_bd_lbl = doc.add_paragraph()
            p_bd_lbl.paragraph_format.space_before = Pt(4)
            p_bd_lbl.paragraph_format.space_after = Pt(2)
            add_bold_prefix(p_bd_lbl, "The Breakdown:")
            
            for item in mnemonic.get('breakdown', []):
                p_item = doc.add_paragraph()
                p_item.paragraph_format.space_before = Pt(0)
                p_item.paragraph_format.space_after = Pt(2)
                add_rich_runs(p_item, item)
                
            p_sp_lbl = doc.add_paragraph()
            p_sp_lbl.paragraph_format.space_before = Pt(4)
            p_sp_lbl.paragraph_format.space_after = Pt(2)
            add_bold_prefix(p_sp_lbl, "The \"Specialized\" Trio (The remaining 3):")
            
            for item in mnemonic.get('specialized', []):
                p_item = doc.add_paragraph()
                p_item.paragraph_format.space_before = Pt(0)
                p_item.paragraph_format.space_after = Pt(2)
                add_rich_runs(p_item, item)
            doc.add_paragraph()

        # Table data rendering
        table_data = block.get('table')
        if table_data:
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            if headers and rows:
                table_title = table_data.get('title', 'Reference Table')
                add_custom_heading(doc, table_title, level=3)
                add_styled_table(doc, headers, rows)
                doc.add_paragraph()

        # Key Concepts and Definitions
        concepts = block.get('concepts', [])
        if concepts:
            add_custom_heading(doc, "Key Concepts & Definitions:", level=3)
            for item in concepts:
                p_c = doc.add_paragraph(style='List Bullet')
                add_bold_prefix(p_c, item.get('term', '') + ": ")
                add_rich_runs(p_c, item.get('definition', ''))

        # Exam Imp section
        exam_imp = block.get('exam_imp', [])
        if exam_imp:
            p_head = doc.add_paragraph()
            p_head.paragraph_format.space_before = Pt(6)
            p_head.paragraph_format.space_after = Pt(2)
            run_head = p_head.add_run("EXAM IMP:")
            run_head.bold = True
            run_head.underline = True
            run_head.font.size = Pt(10)
            run_head.font.color.rgb = RGBColor(0x00, 0x70, 0xC0)
            run_head.font.name = 'Calibri'
            
            for item in exam_imp:
                p_item = doc.add_paragraph()
                p_item.paragraph_format.space_before = Pt(0)
                p_item.paragraph_format.space_after = Pt(3)
                add_rich_runs(p_item, item)
            doc.add_paragraph()

        # Examples & Illustrations
        examples = block.get('examples', [])
        seen_rules_in_block = []
        inserted_vm_indices = set()
        visual_moments = block.get('visual_moments', [])

        if examples:
            solved_examples = [ex for ex in examples if not ex.get('is_homework')]
            hw_examples = [ex for ex in examples if ex.get('is_homework')]

            if solved_examples:
                add_custom_heading(doc, "Examples & Illustrations:", level=3)
                for idx, ex in enumerate(solved_examples):
                    p_q = doc.add_paragraph()
                    sentence = ex.get('sentence', 'Example')
                    is_question = sentence.endswith('?') or sentence.startswith(('Q:', 'Explain', 'Describe', 'Why', 'How', 'What', 'Define', 'List', 'Solve', 'Calculate', 'Find', 'Determine', 'Evaluate', 'Compare', 'Verify'))
                    
                    pref = "Q: " if is_question else "Example: "
                    add_bold_prefix(p_q, pref)
                    add_rich_runs(p_q, sentence)

                    rule = ex.get('rule', '')
                    is_redundant_rule = False
                    if rule:
                        is_redundant_rule = any(are_rules_similar(rule, prev) for prev in seen_rules_in_block)

                    if rule and not is_redundant_rule:
                        p_rule = doc.add_paragraph()
                        label = "Applicable Rule: " if is_question else "Key Concept: "
                        add_bold_prefix(p_rule, label)
                        add_rich_runs(p_rule, rule)
                        seen_rules_in_block.append(rule)

                    working_text = ex.get('working', '')
                    if working_text:
                        label_work = "Explanation/Working:" if is_question else "Explanation:"
                        p_work_lbl = doc.add_paragraph()
                        add_bold_prefix(p_work_lbl, label_work)
                        add_formatted_explanation_paragraphs(doc, working_text)

                    ans_text = get_explicit_answer(ex, working_text)
                    if ans_text and is_question:
                        p_ans = doc.add_paragraph()
                        add_bold_prefix(p_ans, "Answer: ")
                        add_rich_runs(p_ans, ans_text)

                    # Place corresponding visual moment inline right under the example
                    if idx < len(visual_moments):
                        vm = visual_moments[idx]
                        success_inserted = insert_image_for_vm(doc, vm, block_id, slides, timestamp_to_frame, frames, inserted_filenames, inserted_ocrs)
                        if success_inserted:
                            inserted_vm_indices.add(idx)

            if hw_examples:
                add_custom_heading(doc, "Homework Questions (HW Que): Try:", level=3)
                for idx, ex in enumerate(hw_examples):
                    p_q = doc.add_paragraph()
                    sentence = ex.get('sentence', 'Example')
                    add_bold_prefix(p_q, "Q: ")
                    add_rich_runs(p_q, sentence)

                    rule = ex.get('rule', '')
                    if rule:
                        p_rule = doc.add_paragraph()
                        add_bold_prefix(p_rule, "Concept: ")
                        add_rich_runs(p_rule, rule)

                    working_text = ex.get('working', '')
                    if working_text:
                        p_work_lbl = doc.add_paragraph()
                        add_bold_prefix(p_work_lbl, "Working/Solution: ")
                        add_formatted_explanation_paragraphs(doc, working_text)

                    ans_text = get_explicit_answer(ex, working_text)
                    if ans_text:
                        p_ans = doc.add_paragraph()
                        add_bold_prefix(p_ans, "Answer: ")
                        add_rich_runs(p_ans, ans_text)

        # Important Points / Teacher's Emphasis
        important_points = block.get('important_points', [])
        if important_points:
            add_custom_heading(doc, "Key Highlights (⭐ Teacher's Emphasis):", level=3)
            for item in important_points:
                p_i = doc.add_paragraph()
                add_bold_prefix(p_i, "⭐ ")
                add_rich_runs(p_i, item)

        # Exercise Questions
        exercises = block.get('exercise_questions', [])
        if exercises:
            real_exercises = [eq for eq in exercises if isinstance(eq, str) and eq.strip()]
            if real_exercises:
                p = doc.add_paragraph()
                add_bold_prefix(p, "Exercise Questions:")
                for eq in real_exercises:
                    p_ex = doc.add_paragraph(style='List Bullet')
                    add_rich_runs(p_ex, eq)

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

        # Revision boxes are required by the note style contract.
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
        add_custom_heading(doc, "Section 3: Rules, Formulas & Exam Traps", level=1)
        for trap, btitle in all_traps:
            p = doc.add_paragraph(style='List Bullet')
            add_bold_prefix(p, "🚨 ")
            add_rich_runs(p, f"From <b>{btitle}</b>: {trap}")
        for trick, btitle in all_tricks:
            p = doc.add_paragraph(style='List Bullet')
            add_bold_prefix(p, "💡 ")
            add_rich_runs(p, f"From <b>{btitle}</b>: {trick}")

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
        add_custom_heading(doc, "Section 4: Final Revision Points", level=1)
        for title, rule in temp_p_runs:
            p = doc.add_paragraph(style='List Bullet')
            add_rich_runs(p, f"<b>{title}</b>: {rule}")

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

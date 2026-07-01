#!/usr/bin/env python3
import os
import sys
import json
import re
import fitz
from PIL import Image

try:
    from pdf2image import convert_from_path
    import pytesseract
except ImportError:
    print("Dependencies not met. Ensure pdf2image and pytesseract are installed in venv.")
    sys.exit(1)

def parse_srt(srt_path):
    if not os.path.exists(srt_path):
        return []
    segments = []
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split by double newlines or similar to get blocks
        blocks = re.split(r'\n\s*\n', content.strip())
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                time_line = lines[1]
                text = " ".join(lines[2:])
                match = re.search(r'(\d{2}:\d{2}:\d{2})', time_line)
                if match:
                    ts = match.group(1)
                    segments.append({"timestamp": ts, "text": text.lower()})
    except Exception as e:
        print(f"Error parsing SRT: {e}")
    return segments

def match_slide_to_transcript(ocr_text, srt_segments):
    if not srt_segments or not ocr_text.strip():
        return "00:00:00", False
        
    # Extract unique words of length >= 3 from slide OCR
    words = set(re.findall(r'\b[a-z0-9_\-\+]{3,}\b', ocr_text.lower()))
    stop_words = {"about", "above", "after", "again", "against", "along", "could", "would", "should", "their", "there", "these", "those", "which", "where", "under"}
    words = words - stop_words
    
    # fallback to shorter words/math variables if no words match
    if not words:
        words = set(re.findall(r'\b[a-z0-9_\-\+]{1,2}\b', ocr_text.lower()))
        words = words - stop_words
        
    if not words:
        return "00:00:00", False
        
    best_ts = "00:00:00"
    best_score = 0
    total_matches = 0
    
    for seg in srt_segments:
        seg_text = seg["text"]
        matches = sum(1 for w in words if w in seg_text)
        total_matches += matches
        if matches > best_score:
            best_score = matches
            best_ts = seg["timestamp"]
            
    # Adjust matches threshold: if total words is 3 or less, require at least 1 match; otherwise require 2 matches.
    required_matches = 1 if len(words) <= 3 else 2
    discussed = total_matches >= required_matches
    return best_ts, discussed

def find_transcript_path() -> str:
    default_path = "lecture-input/transcript.srt"
    if os.path.exists(default_path):
        return default_path
    for name in ["transcript.txt", "transcript.vtt", "TRANSCRIPT.srt", "TRANSCRIPT.txt", "TRANSCRIPT.vtt"]:
        p = os.path.join("lecture-input", name)
        if os.path.exists(p):
            return p
    return default_path

def process_pdf(pdf_path, output_dir, manifest_path, srt_segments):
    if not os.path.exists(pdf_path):
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return

    os.makedirs(output_dir, exist_ok=True)
    print(f"Converting PDF {pdf_path} to images in {output_dir}...")
    try:
        pages = convert_from_path(pdf_path)
    except Exception as e:
        print(f"Error converting PDF {pdf_path}: {e}")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return
        
    manifest = []
    prefix = "slide" if "slide" in manifest_path else "ref"
    
    for idx, page in enumerate(pages):
        img_filename = f"{prefix}_{idx+1:03d}.png"
        img_path = os.path.join(output_dir, img_filename)
        page.save(img_path, "PNG")
        print(f"Saved {prefix}: {img_path}")
        
        # OCR text
        ocr_text = ""
        try:
            ocr_text = pytesseract.image_to_string(img_path)
            clean_text = ocr_text[:50].replace('\n', ' ')
            print(f"OCR {prefix} {idx+1}: {clean_text}...")
        except Exception as e:
            print(f"OCR failed for {prefix} {idx+1}: {e}")
            ocr_text = "OCR failed or tesseract not found"
            
        # Also extract digital text from PDF page if available
        dig_text = ""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            if idx < len(doc):
                dig_text = doc[idx].get_text().strip()
            doc.close()
        except Exception as e:
            print(f"Digital text extraction failed for page {idx+1}: {e}")

        # Combine digital text layer and OCR text
        combined_text = ocr_text
        if dig_text:
            combined_text = f"{dig_text}\n\n[OCR/Visual Text]:\n{ocr_text}"
            
        discussed_at, discussed = match_slide_to_transcript(combined_text, srt_segments)
            
        manifest.append({
            "slide_number": idx + 1,
            "image_path": img_path,
            "ocr_text": combined_text.strip(),
            "discussed_at": discussed_at,
            "discussed": discussed
        })
        
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Completed parsing for {pdf_path}. Generated {manifest_path} with {len(manifest)} pages.")

def extract_embedded_screenshots(pdf_path, output_dir="reference_screenshots", manifest_path="embedded_manifest.json"):
    print(f"Extracting embedded screenshots from {pdf_path}...")
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    
    xref_to_pages = {}
    for i in range(len(doc)):
        page = doc[i]
        for img in page.get_images(full=True):
            xref = img[0]
            rects = page.get_image_rects(xref)
            if any(r.intersects(page.rect) for r in rects):
                if xref not in xref_to_pages:
                    xref_to_pages[xref] = []
                xref_to_pages[xref].append(i + 1)
    
    screenshots = []
    count = 0
    for xref, page_nums in sorted(xref_to_pages.items(), key=lambda x: x[1][0] if x[1] else 999):
        try:
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            w, h = base_image["width"], base_image["height"]
            
            # Filter out small UI elements or strokes (assume screenshots are > 400x100)
            if w > 400 and h > 100:
                count += 1
                img_name = f"ss_{count:03d}.{image_ext}"
                img_path = os.path.join(output_dir, img_name)
                
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
                
                # Run OCR to map the text
                ocr_text = ""
                try:
                    ocr_text = pytesseract.image_to_string(Image.open(img_path)).strip()
                except Exception:
                    pass

                for page_num in page_nums:
                    screenshots.append({
                        "image_path": img_path,
                        "ocr_text": ocr_text,
                        "width": w,
                        "height": h,
                        "page_number": page_num
                    })
        except Exception as e:
            print(f"Error extracting xref {xref}: {e}")
            
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(screenshots, f, indent=2)
    print(f"Extracted {count} embedded screenshots to {manifest_path}")
    doc.close()

def write_empty_manifest(manifest_path):
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump([], f)

def main():
    # 1. Check for PPTX slides and print a conversion warning
    pptx_path = "lecture-input/SLIDES.pptx"
    for name in ["slides.pptx", "SLIDES.PPTX", "slides.PPTX", "Slides.pptx"]:
        p = os.path.join("lecture-input", name)
        if os.path.exists(p):
            pptx_path = p
            break
    if os.path.exists(pptx_path):
        print(f"⚠️ Warning: Found PowerPoint slide deck at {pptx_path}.")
        print("Note: Image extraction is only supported for PDF slide decks. Please convert your slides to PDF and upload as SLIDES.pdf for visual mapping support.")

    srt_path = find_transcript_path()
    srt_segments = parse_srt(srt_path)

    # 2. Case-insensitive PDF slide deck path check
    pdf_path = "lecture-input/SLIDES.pdf"
    for name in ["slides.pdf", "SLIDES.PDF", "slides.PDF", "Slides.pdf"]:
        p = os.path.join("lecture-input", name)
        if os.path.exists(p):
            pdf_path = p
            break
            
    # 3. Process slides
    if os.path.exists(pdf_path):
        process_pdf(pdf_path, "slides", "slide_manifest.json", srt_segments)
    else:
        if os.path.exists("slides"):
            import shutil
            try:
                shutil.rmtree("slides")
                print("Cleared stale slides directory.")
            except Exception as e:
                print(f"Warning: Failed to clear stale slides directory: {e}")
        with open("slide_manifest.json", "w", encoding="utf-8") as f:
            json.dump([], f)
            
    # 4. Case-insensitive REFERENCE NOTES path check
    ref_path = "lecture-input/REFERENCE_NOTES.pdf"
    for name in ["reference_notes.pdf", "REFERENCE_NOTES.PDF", "reference_notes.PDF", "Reference_Notes.pdf"]:
        p = os.path.join("lecture-input", name)
        if os.path.exists(p):
            ref_path = p
            break
            
    # 5. Process reference notes
    if os.path.exists(ref_path):
        process_pdf(ref_path, "reference_pages", "reference_manifest.json", srt_segments)
        extract_embedded_screenshots(ref_path)
    else:
        txt_path = "lecture-input/REFERENCE_NOTES.txt"
        for name in ["reference_notes.txt", "REFERENCE_NOTES.TXT", "reference_notes.TXT", "Reference_Notes.txt"]:
            p = os.path.join("lecture-input", name)
            if os.path.exists(p):
                txt_path = p
                break
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                txt_content = f.read()
            manifest = [{
                "slide_number": 1,
                "image_path": "",
                "ocr_text": txt_content.strip(),
                "discussed_at": None,
                "discussed": False
            }]
            with open("reference_manifest.json", "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            print(f"Generated reference_manifest.json from text notes: {txt_path}")
            write_empty_manifest("embedded_manifest.json")
        else:
            # Clear stale reference folders
            import shutil
            for folder in ["reference_pages", "reference_screenshots"]:
                if os.path.exists(folder):
                    try:
                        shutil.rmtree(folder)
                        print(f"Cleared stale folder: {folder}")
                    except Exception as e:
                        print(f"Warning: Failed to clear stale folder {folder}: {e}")
            write_empty_manifest("reference_manifest.json")
            write_empty_manifest("embedded_manifest.json")
            print("No reference notes found. Reset reference_manifest.json and embedded_manifest.json.")



if __name__ == '__main__':
    main()

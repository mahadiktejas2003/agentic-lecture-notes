#!/usr/bin/env python3
import os
import sys
import json
import re

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
        
    # Extract unique words of length >= 5 from slide OCR
    words = set(re.findall(r'\b[a-z]{5,}\b', ocr_text.lower()))
    stop_words = {"about", "above", "after", "again", "against", "along", "could", "would", "should", "their", "there", "these", "those", "which", "where", "under"}
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
            
    discussed = total_matches >= 2
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

    # 2. Case-insensitive PDF slide deck path check
    pdf_path = "lecture-input/SLIDES.pdf"
    for name in ["slides.pdf", "SLIDES.PDF", "slides.PDF", "Slides.pdf"]:
        p = os.path.join("lecture-input", name)
        if os.path.exists(p):
            pdf_path = p
            break

    srt_path = find_transcript_path()
    output_dir = "slides"
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(pdf_path):
        print(f"Error: Slide PDF not found at {pdf_path}")
        # Write an empty slide manifest as fallback
        with open("slide_manifest.json", "w", encoding="utf-8") as f:
            json.dump([], f)
        sys.exit(0)
        
    print(f"Converting PDF {pdf_path} to images...")
    try:
        pages = convert_from_path(pdf_path)
    except Exception as e:
        print(f"Error converting PDF: {e}")
        # Write empty slide manifest as fallback
        with open("slide_manifest.json", "w", encoding="utf-8") as f:
            json.dump([], f)
        sys.exit(0)
        
    srt_segments = parse_srt(srt_path)
    manifest = []
    
    for idx, page in enumerate(pages):
        img_filename = f"slide_{idx+1:03d}.png"
        img_path = os.path.join(output_dir, img_filename)
        page.save(img_path, "PNG")
        print(f"Saved slide: {img_path}")
        
        # OCR text
        ocr_text = ""
        try:
            ocr_text = pytesseract.image_to_string(img_path)
            clean_text = ocr_text[:50].replace('\n', ' ')
            print(f"OCR Slide {idx+1}: {clean_text}...")
        except Exception as e:
            print(f"OCR failed for slide {idx+1}: {e}")
            ocr_text = "OCR failed or tesseract not found"
            
        discussed_at, discussed = match_slide_to_transcript(ocr_text, srt_segments)
            
        manifest.append({
            "slide_number": idx + 1,
            "image_path": img_path,
            "ocr_text": ocr_text.strip(),
            "discussed_at": discussed_at,
            "discussed": discussed
        })
        
    with open("slide_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Completed slide parsing. Generated slide_manifest.json with {len(manifest)} slides.")

if __name__ == '__main__':
    main()
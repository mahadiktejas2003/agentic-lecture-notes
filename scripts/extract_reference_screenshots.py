import argparse
import fitz
import os
import json
import pytesseract
from PIL import Image

def extract_screenshots(pdf_path, output_dir, manifest_path):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    
    xref_to_page = {}
    for i in range(len(doc)):
        page = doc[i]
        for img in page.get_images(full=True):
            xref = img[0]
            if xref not in xref_to_page:
                xref_to_page[xref] = i + 1  # 1-indexed page number
    
    screenshots = []
    count = 0
    for xref, page_num in sorted(xref_to_page.items(), key=lambda x: x[1]):
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
                ocr_text = pytesseract.image_to_string(Image.open(img_path)).strip()
                screenshots.append({
                    "image_path": img_path,
                    "ocr_text": ocr_text,
                    "width": w,
                    "height": h,
                    "page_number": page_num
                })
                print(f"Extracted {img_name} from page {page_num} ({w}x{h}) - OCR length: {len(ocr_text)}")
        except Exception as e:
            print(f"Error extracting xref {xref}: {e}")
            
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(screenshots, f, indent=2)
    doc.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract embedded screenshots from reference notes PDF")
    parser.add_argument("--pdf", default="lecture-input/REFERENCE_NOTES.pdf", help="Path to reference notes PDF")
    parser.add_argument("--output-dir", default="reference_screenshots", help="Directory for extracted images")
    parser.add_argument("--manifest", default="embedded_manifest.json", help="Output manifest path")
    args = parser.parse_args()
    extract_screenshots(args.pdf, args.output_dir, args.manifest)

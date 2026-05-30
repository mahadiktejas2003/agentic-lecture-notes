---
name: slide-parsing
description: Converts slide decks to images, OCRs text, cross‑references with transcript.
---

# Slide Parsing Skill

## Tools
- `run_shell_command`
- `read_file`
- `write_file`

## Execution

1. Convert slides:
   - `.pptx`:
     ```bash
     python3 -c "from pptx import Presentation; prs=Presentation('lecture-input/SLIDES.pptx'); [slide.export(f'slides/slide_{i+1:03d}.png') for i,slide in enumerate(prs.slides)]"
     ```
   - `.pdf`:
     ```bash
     python3 -c "from pdf2image import convert_from_path; [img.save(f'slides/slide_{i+1:03d}.png') for i,img in enumerate(convert_from_path('lecture-input/SLIDES.pdf'))]"
     ```

2. OCR each slide:
   ```bash
   python3 -c "import pytesseract; print(pytesseract.image_to_string('slides/slide_001.png'))"
   ```

3. Cross‑reference transcript; map slides to timestamps.

4. Write `slide_manifest.json`:
```json
[{"slide_number":1,"image_path":"slides/slide_001.png","ocr_text":"...","discussed_at":"00:04:00","discussed":true}]
```

## Deliverable
`slide_manifest.json`

import os
import json
import pytesseract
from PIL import Image

manifest = []
screenshots_dir = 'screenshots'
for filename in sorted(os.listdir(screenshots_dir)):
    if filename.endswith('.png') or filename.endswith('.jpg'):
        filepath = os.path.join(screenshots_dir, filename)
        try:
            text = pytesseract.image_to_string(Image.open(filepath), lang='eng+hin').strip()
            manifest.append({
                "frame_path": filepath,
                "timestamp": 0.0,
                "ocr_text": text
            })
            print(f"OCRed {filename}")
        except Exception as e:
            print(f"Error on {filename}: {e}")

with open('frame_manifest.json', 'w') as f:
    json.dump(manifest, f, indent=4)
print("Saved frame_manifest.json")

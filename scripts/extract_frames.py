#!/usr/bin/env python3
import os, subprocess, json, logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_frames():
    video = "lecture-input/LECTURE.mp4"
    output_dir = "screenshots"
    os.makedirs(output_dir, exist_ok=True)
    if not os.path.exists(video):
        logger.error("❌ Video not found at %s", video)
        return
    cmd = f'ffmpeg -i "{video}" -vf "select=eq(n\,0)+eq(mod(n\,300)\,0)" -vsync vfr "{output_dir}/frame_%03d.png"'
    subprocess.run(cmd, shell=True, check=True)
    manifest = {}
    try:
        import pytesseract
        from PIL import Image
        for fname in sorted(os.listdir(output_dir)):
            if fname.endswith('.png'):
                fpath = os.path.join(output_dir, fname)
                img = Image.open(fpath)
                try: text = pytesseract.image_to_string(img, lang='eng+hin')
                except: text = pytesseract.image_to_string(img, lang='eng')
                manifest[fname] = {"timestamp": "00:00:00", "ocr_text": text.strip(), "type": "board"}
    except ImportError:
        logger.error("⚠️ pytesseract not installed. OCR will be empty.")
        for fname in sorted(os.listdir(output_dir)):
            if fname.endswith('.png'): manifest[fname] = {"timestamp": "00:00:00", "ocr_text": "", "type": "board"}
    with open("frame_manifest.json", 'w') as f: json.dump(manifest, f, indent=2)
    logger.info(f"✅ Saved {len(manifest)} frames")

if __name__ == "__main__": extract_frames()

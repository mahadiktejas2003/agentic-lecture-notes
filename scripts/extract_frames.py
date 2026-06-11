#!/usr/bin/env python3
import os, sys, json, subprocess, argparse, re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Failed to get duration: {e}")
        return 0.0

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

def extract_frames(video_path, output_dir, timestamps=None):
    """Extract frames based on timestamps or default sampling."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Clear output_dir first to prevent leakage from previous runs
    for f in os.listdir(output_dir):
        fp = os.path.join(output_dir, f)
        if os.path.isfile(fp) and f.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                os.remove(fp)
            except Exception as e:
                logger.warning(f"Failed to clear old frame file {f}: {e}")
                
    manifest = {}
    
    # Load or calculate timestamps
    if not timestamps:
        duration = get_video_duration(video_path)
        if duration <= 0:
            logger.warning("Could not determine duration. Using default sampling.")
            # Fallback: every 300 frames approx
            cmd = ['ffmpeg', '-i', video_path, '-vf', r'select=eq(n\,0)+not(mod(n\,300))', 
                   '-vsync', 'vfr', f'{output_dir}/frame_%03d.png']
            subprocess.run(cmd, check=True)
            # Generate manifest with calculated timestamps based on frame position
            frame_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
            # Estimate timestamp assuming 30fps and every 300 frames = 10 seconds apart
            for i, fname in enumerate(frame_files):
                estimated_seconds = i * 10  # 10 seconds between frames
                ts = f"{estimated_seconds//3600}:{(estimated_seconds%3600)//60:02d}:{estimated_seconds%60:02d}"
                out_path = os.path.join(output_dir, fname)
                try:
                    import pytesseract
                    from PIL import Image
                    img = Image.open(out_path)
                    ocr_text = pytesseract.image_to_string(img).strip()
                except ImportError:
                    ocr_text = "OCR unavailable"
                if is_logo_frame(ocr_text):
                    logger.info(f"Skipping logo/intro frame: {fname}")
                    try:
                        os.remove(out_path)
                    except:
                        pass
                    continue
                manifest[fname] = {"timestamp": ts, "ocr_text": ocr_text, "type": "board"}
        else:
            # Default: sample every 60 seconds
            timestamps = [f"{int(t)//3600}:{(int(t)%3600)//60:02d}:{int(t)%60:02d}" 
                          for t in range(0, int(duration), 60)]

    if timestamps:
        # Extract specific timestamps
        for i, ts in enumerate(timestamps):
            # Convert HH:MM:SS to seconds for ffmpeg
            parts = list(map(int, ts.split(':')))
            seconds = parts[0]*3600 + parts[1]*60 + parts[2]
            
            fname = f"frame_{i+1:03d}.png"
            out_path = os.path.join(output_dir, fname)
            
            cmd = ['ffmpeg', '-ss', str(seconds), '-i', video_path, '-vframes', '1', '-y', out_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(out_path):
                # Perform OCR immediately
                try:
                    import pytesseract
                    from PIL import Image
                    img = Image.open(out_path)
                    ocr_text = pytesseract.image_to_string(img).strip()
                except ImportError:
                    ocr_text = "OCR unavailable"
                
                if is_logo_frame(ocr_text):
                    logger.info(f"Skipping logo/intro frame: {fname} (detected branding content)")
                    try:
                        os.remove(out_path)
                    except:
                        pass
                    continue
                
                manifest[fname] = {
                    "timestamp": ts,
                    "ocr_text": ocr_text,
                    "type": "board"
                }
                logger.info(f"Extracted {fname} at {ts}")
            else:
                logger.warning(f"Failed to extract frame at {ts}")

    # Deduplicate manifest based on OCR similarity
    unique_manifest = {}
    
    for fname in sorted(manifest.keys()):
        info = manifest[fname]
        current_ocr = info.get('ocr_text', '')
        
        is_duplicate = False
        for unique_fname, unique_info in unique_manifest.items():
            if are_ocr_texts_similar(current_ocr, unique_info.get('ocr_text', ''), threshold=0.48):
                is_duplicate = True
                break
                
        if is_duplicate:
            logger.info(f"Removing duplicate frame: {fname} at {info['timestamp']} (similar to an existing frame)")
            try:
                os.remove(os.path.join(output_dir, fname))
            except Exception as e:
                logger.warning(f"Failed to remove duplicate file {fname}: {e}")
        else:
            unique_manifest[fname] = info

    with open('frame_manifest.json', 'w') as f:
        json.dump(unique_manifest, f, indent=2)
    logger.info(f"✅ Saved {len(unique_manifest)} unique frames (removed {len(manifest) - len(unique_manifest)} duplicates).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from video")
    parser.add_argument('--video', required=True, help="Path to video file")
    parser.add_argument('--output-dir', default='screenshots', help="Output directory")
    parser.add_argument('--timestamps', nargs='*', help="List of timestamps (HH:MM:SS)")
    args = parser.parse_args()
    
    extract_frames(args.video, args.output_dir, args.timestamps)

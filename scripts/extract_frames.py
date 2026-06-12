#!/usr/bin/env python3
import os, sys, json, subprocess, argparse, re, shutil
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
            base_seconds = parts[0]*3600 + parts[1]*60 + parts[2]
            
            fname = f"frame_{i+1:03d}.png"
            out_path = os.path.join(output_dir, fname)
            
            # Search strictly before or at the target timestamp to avoid capturing the next slide
            candidates = [
                max(0, base_seconds - 10),
                max(0, base_seconds - 7),
                max(0, base_seconds - 4),
                max(0, base_seconds - 2),
                base_seconds
            ]
            
            best_ocr_text = ""
            best_word_count = -1
            best_candidate_path = None
            
            temp_paths = []
            
            for c_idx, sec in enumerate(candidates):
                temp_fname = f"temp_frame_{i+1:03d}_c{c_idx}.png"
                temp_path = os.path.join(output_dir, temp_fname)
                
                cmd = ['ffmpeg', '-ss', str(sec), '-i', video_path, '-vframes', '1', '-y', temp_path]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if os.path.exists(temp_path):
                    temp_paths.append(temp_path)
                    
                    ocr_text = ""
                    try:
                        import pytesseract
                        from PIL import Image
                        img = Image.open(temp_path)
                        ocr_text = pytesseract.image_to_string(img).strip()
                    except Exception as e:
                        logger.warning(f"OCR failed for candidate {sec}s: {e}")
                        ocr_text = ""
                        
                    # Count words of length >= 3
                    words = [w for w in re.findall(r'\b\w{3,}\b', ocr_text.lower())]
                    word_count = len(words)
                    
                    logger.info(f"Candidate frame at {sec}s yielded {word_count} words.")
                    
                    if word_count > best_word_count:
                        best_word_count = word_count
                        best_ocr_text = ocr_text
                        best_candidate_path = temp_path
            
            if best_candidate_path and os.path.exists(best_candidate_path):
                # Filter out logo frames
                if is_logo_frame(best_ocr_text):
                    logger.info(f"Skipping logo/intro frame: {fname} (detected branding content)")
                    # Clean up all candidate temp files
                    for p in temp_paths:
                        try:
                            os.remove(p)
                        except:
                            pass
                    continue
                
                shutil.copy(best_candidate_path, out_path)
                
                manifest[fname] = {
                    "timestamp": ts,
                    "ocr_text": best_ocr_text,
                    "type": "board"
                }
                logger.info(f"Selected best candidate for {fname} yielding {best_word_count} words.")
            else:
                logger.warning(f"Failed to extract any candidate frames at {ts}")
                
            # Clean up all candidate temp files
            for p in temp_paths:
                try:
                    os.remove(p)
                except:
                    pass

    # Helper to parse seconds from HH:MM:SS
    def get_seconds(ts):
        parts = list(map(int, ts.split(':')))
        return parts[0]*3600 + parts[1]*60 + parts[2]

    # Deduplicate manifest based on OCR similarity within a local time window
    unique_manifest = {}
    
    if timestamps:
        unique_manifest = manifest
        logger.info("Bypassing OCR-based deduplication because specific timestamps were requested.")
    else:
        for fname in sorted(manifest.keys()):
            info = manifest[fname]
            current_ocr = info.get('ocr_text', '')
            current_sec = get_seconds(info['timestamp'])
            
            is_duplicate = False
            for unique_fname, unique_info in unique_manifest.items():
                unique_sec = get_seconds(unique_info['timestamp'])
                # Only deduplicate if the frames are within 120 seconds of each other
                if abs(current_sec - unique_sec) <= 120:
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
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from video")
    parser.add_argument('--video', required=True, help="Path to video file")
    parser.add_argument('--output-dir', default='screenshots', help="Output directory")
    parser.add_argument('--timestamps', nargs='*', help="List of timestamps (HH:MM:SS)")
    args = parser.parse_args()
    
    extract_frames(args.video, args.output_dir, args.timestamps)

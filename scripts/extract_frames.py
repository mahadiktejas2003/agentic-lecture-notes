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

def extract_frames(video_path, output_dir, timestamps=None):
    """Extract frames based on timestamps or default sampling."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Load or calculate timestamps
    if not timestamps:
        duration = get_video_duration(video_path)
        if duration <= 0:
            logger.warning("Could not determine duration. Using default sampling.")
            # Fallback: every 300 frames approx
            cmd = ['ffmpeg', '-i', video_path, '-vf', r'select=eq(n\,0)+not(mod(n\,300))', 
                   '-vsync', 'vfr', f'{output_dir}/frame_%03d.png']
            subprocess.run(cmd, check=True)
            # Generate dummy manifest if no timestamps
            manifest = {}
            for f in sorted(os.listdir(output_dir)):
                if f.endswith('.png'):
                    manifest[f] = {"timestamp": "00:00:00", "ocr_text": "", "type": "board"}
            with open('frame_manifest.json', 'w') as f: json.dump(manifest, f, indent=2)
            return

        # Default: sample every 60 seconds
        timestamps = [f"{int(t)//3600}:{(int(t)%3600)//60:02d}:{int(t)%60:02d}" 
                      for t in range(0, int(duration), 60)]

    manifest = {}
    
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
            
            manifest[fname] = {
                "timestamp": ts,
                "ocr_text": ocr_text,
                "type": "board"
            }
            logger.info(f"Extracted {fname} at {ts}")
        else:
            logger.warning(f"Failed to extract frame at {ts}")

    with open('frame_manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"✅ Saved {len(manifest)} frames with real timestamps.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from video")
    parser.add_argument('--video', required=True, help="Path to video file")
    parser.add_argument('--output-dir', default='screenshots', help="Output directory")
    parser.add_argument('--timestamps', nargs='*', help="List of timestamps (HH:MM:SS)")
    args = parser.parse_args()
    
    extract_frames(args.video, args.output_dir, args.timestamps)

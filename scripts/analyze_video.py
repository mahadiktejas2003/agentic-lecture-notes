#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import shutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.crop_frames import crop_content
import pytesseract

def find_video_path() -> str:
    default_path = "lecture-input/LECTURE.mp4"
    if os.path.exists(default_path):
        return default_path
    for ext in ['.mp4', '.mkv', '.avi', '.webm', '.mov']:
        for name in ['LECTURE', 'video', 'lecture', 'VIDEO']:
            p = os.path.join("lecture-input", f"{name}{ext}")
            if os.path.exists(p):
                return p
    if os.path.exists("lecture-input"):
        for f in os.listdir("lecture-input"):
            if any(f.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.webm', '.mov']):
                return os.path.join("lecture-input", f)
    return default_path

def analyze():
    video_path = find_video_path()
    temp_dir = "temp_screenshots"
    os.makedirs(temp_dir, exist_ok=True)
    
    print("Extracting frames every 10 seconds...")
    # Extract 1 frame every 10 seconds
    cmd = [
        "ffmpeg", "-i", video_path, "-vf", "fps=1/10",
        os.path.join(temp_dir, "frame_%04d.jpg"), "-y"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    files = sorted([f for f in os.listdir(temp_dir) if f.endswith(".jpg")])
    print(f"Extracted {len(files)} frames. Running crop and OCR...")
    
    results = []
    for f in files:
        filepath = os.path.join(temp_dir, f)
        # Calculate timestamp: frame_0001.jpg is at 5s (middle of 0-10s interval depending on ffmpeg behavior, or 10s. Let's calculate exactly based on ffmpeg's fps filter)
        # Actually fps=1/10 outputs frame at t = 5, 15, 25, 35, etc. or t = 0, 10, 20...
        # Let's verify by checking frame timestamps if possible, or just estimate. 
        # Typically fps=1/10 outputs at 10 * (index - 0.5) or 10 * index.
        # Let's get the frame time using ffprobe or estimate as: (index - 0.5) * 10 or similar.
        # Wait, a safer way to get the exact timestamp of each output frame is using ffprobe or by extracting individually.
        # But we can just estimate: frame_0001 is at ~5s, frame_0002 is at ~15s, etc.
        # Let's run crop_content
        crop_content(filepath)
        
        # Run OCR
        try:
            text = pytesseract.image_to_string(filepath, lang="eng").strip()
        except Exception as e:
            text = f"OCR Error: {e}"
            
        index = int(f.split("_")[1].split(".")[0])
        approx_sec = (index - 0.5) * 10
        
        # Format approx_sec to HH:MM:SS
        h = int(approx_sec // 3600)
        m = int((approx_sec % 3600) // 60)
        s = int(approx_sec % 60)
        timestamp_str = f"{h:02d}:{m:02d}:{s:02d}"
        
        print(f"Frame {f} at approx {timestamp_str} (sec {approx_sec}):")
        cleaned_text = " ".join(text.split())
        print(f"  OCR: {cleaned_text[:120]}")
        
        results.append({
            "filename": f,
            "approx_sec": approx_sec,
            "timestamp": timestamp_str,
            "ocr_text": text
        })
        
    with open("temp_analysis.json", "w") as out:
        json.dump(results, out, indent=2)
        
    # Clean up temp_dir
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    analyze()

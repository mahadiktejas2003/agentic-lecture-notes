#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import argparse

def extract_frames(video_path, timestamps, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at: {video_path}")
        return False
        
    print(f"Extracting {len(timestamps)} frames from {video_path}...")
    manifest = {}
    
    for idx, ts in enumerate(timestamps):
        filename = f"CB{idx+1}_1.jpg"
        filepath = os.path.join(output_dir, filename)
        
        # ffmpeg frame extraction command
        cmd = [
            'ffmpeg', '-ss', ts, '-i', video_path,
            '-vframes', '1', '-update', '1', '-q:v', '2',
            filepath, '-y'
        ]
        
        try:
            print(f"Running ffmpeg for timestamp {ts} -> {filepath}")
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            # Auto-crop placeholder or simulation
            # (In production, the pillow crop code from SKILL.md runs here)
            
            manifest[filename] = {
                "timestamp": ts,
                "ocr_text": "extracted frame OCR placeholder text",
                "type": "board"
            }
        except subprocess.CalledProcessError as e:
            print(f"Error extracting frame at {ts}: {e}")
            
    with open('frame_manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        
    print("Completed frame extraction. frame_manifest.json generated.")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract frames at visual moment timestamps.")
    parser.add_argument('--video', default='lecture-input/LECTURE.mp4', help='Input video file')
    parser.add_argument('--timestamps', nargs='+', default=['00:03:30', '00:10:15'], help='List of timestamps to extract (e.g. 00:03:30)')
    parser.add_argument('--output-dir', default='screenshots', help='Directory to save frames')
    
    args = parser.parse_args()
    extract_frames(args.video, args.timestamps, args.output_dir)

import json
import os
import sys

def convert_soundscribe_to_srt(manifest_path, srt_path):
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    chunks = data.get("chunks", [])
    srt_lines = []
    
    # Sort chunks by startSample
    chunks = sorted(chunks, key=lambda x: x.get("startSample", 0))
    
    for i, chunk in enumerate(chunks):
        start_sample = chunk.get("startSample", 0)
        end_sample = chunk.get("endSample", 0)
        text = chunk.get("transcript", "").strip()
        
        start_sec = start_sample / 16000.0
        end_sec = end_sample / 16000.0
        
        def to_srt_time(sec):
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            ms = int(round((sec % 1) * 1000))
            if ms >= 1000:
                ms = 999
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            
        start_time_str = to_srt_time(start_sec)
        end_time_str = to_srt_time(end_sec)
        
        srt_lines.append(str(i + 1))
        srt_lines.append(f"{start_time_str} --> {end_time_str}")
        srt_lines.append(text)
        srt_lines.append("")
        
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(srt_lines))
        
    print(f"Successfully converted {manifest_path} to {srt_path} ({len(chunks)} Chunks)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python soundscribe_to_srt.py <manifest_json> <output_srt>")
        sys.exit(1)
    convert_soundscribe_to_srt(sys.argv[1], sys.argv[2])

import json
import os
import sys

def convert_soundscribe_to_srt(manifest_path, srt_path):
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading or parsing SoundScribe manifest {manifest_path}: {e}")
        return False
        
    sample_rate = float(data.get("sampleRate", data.get("samplerate", 16000.0)))
    if sample_rate <= 0:
        sample_rate = 16000.0

    srt_lines = []
    
    chunks = data.get("chunks", data.get("subtitles", data.get("segments", [])))
    if isinstance(data, list):
        chunks = data

    # Sort chunks by startSample
    chunks = sorted(chunks, key=lambda x: x.get("startSample", 0) if isinstance(x, dict) else 0)

    
    # Filter out empty or whitespace-only chunks
    valid_chunks = []
    for chunk in chunks:
        if chunk.get("transcript", "").strip():
            valid_chunks.append(chunk)
            
    for i, chunk in enumerate(valid_chunks):
        start_sample = chunk.get("startSample", 0)
        end_sample = chunk.get("endSample", 0)
        text = chunk.get("transcript", "").strip()
        
        start_sec = start_sample / sample_rate
        end_sec = end_sample / sample_rate
        
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

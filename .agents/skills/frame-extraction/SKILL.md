---
name: frame-extraction
description: Extracts frames from lecture videos at every visual moment, crops to content, and OCRs handwriting.
---

# Frame Extraction Skill

## Tools
- `run_shell_command` – ffprobe, ffmpeg, Python
- `read_file` – transcript
- `write_file` – manifest

## Execution

1. Get video duration:
   ```bash
   ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "lecture-input/LECTURE.mp4"
   ```

2. Read transcript with `read_file`. Scan the full text and build a list of visual moments BEFORE extracting any frames. Detect cues like:
   - "look at the board", "write this down", "as you can see" → type `board`
   - "next slide", "slide number", "on the screen" → type `slide`
   For each cue, estimate the timestamp from the transcript (SRT/VTT timestamps, or percentage of transcript × duration). Store as a list: `[(timestamp, type, description), ...]`.

3. For each visual moment in the list from Step 2, extract a frame:
   ```bash
   ffmpeg -ss [TIMESTAMP] -i "lecture-input/LECTURE.mp4" -vframes 1 -update 1 -q:v 2 "screenshots/CB{N}_{M}.jpg" -y
   ```

4. Crop all extracted frames to remove black bars and irrelevant borders:
   ```bash
   source venv/bin/activate && python3 scripts/crop_frames.py
   ```

5. OCR each cropped frame:
   ```bash
   source venv/bin/activate && python3 -c "
   import pytesseract, os, json
   for f in sorted(os.listdir('screenshots')):
       if f.endswith('.jpg'):
           text = pytesseract.image_to_string(os.path.join('screenshots', f), lang='eng+hin')
           print(f'{f}: {text[:100]}...')
   "
   ```

6. Write `frame_manifest.json` using `write_file`. Every extracted frame must have an entry. Manifest must NOT be empty.

## Hardened Specifications for Frame Extraction:
1. **Windowed Candidate Search**:
   - For every visual moment timestamp $T$, extract 5 candidates at `[T-8s, T-5s, T-2s, T, T+2s]`.
   - Run OCR and select the candidate with the **maximum alphanumeric word count**.
2. **Local Deduplication Limit (120s)**:
   - When checking for duplicates, only compare the current frame's OCR against previously accepted unique frames if their timestamps are within **120 seconds** of each other.
3. **Solved-State Timestamps**:
   - Always target timestamps towards the **end** of each question explanation (right before the next segment starts) so that the teacher's final vector drawings, scribbling, and solved state are captured.
4. **Branding Filter**:
   - Discard any frame whose OCR contains "Gate Smashers" or similar branding text with sparse content (word count < 25 or containing subscription/social cues).

## Deliverable
`frame_manifest.json`

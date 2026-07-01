#!/usr/bin/env python3
import os
import sys
import shutil
import re
from pathlib import Path

def get_words(name):
    # Extract lowercase alphanumeric words of length >= 3
    words = set(re.findall(r'\b[a-z0-9]{3,}\b', name.lower()))
    # Remove common noise words
    noise = {"and", "the", "for", "with", "this", "that", "from", "copy", "transcript", "notes", "slides", "reference", "class", "lecture", "day"}
    return words - noise

def find_lecture_group(downloads_path=None):
    downloads = Path(downloads_path) if downloads_path else Path(os.environ.get("DOWNLOADS_DIR", Path.home() / "Downloads"))
    if not downloads.exists():
        print(f"Downloads directory {downloads} does not exist.")
        return None

    # Get all mp4, srt, and pdf files
    mp4_files = sorted(downloads.glob("*.mp4"), key=os.path.getmtime, reverse=True)
    srt_files = sorted(downloads.glob("*.srt"), key=os.path.getmtime, reverse=True)
    pdf_files = sorted(downloads.glob("*.pdf"), key=os.path.getmtime, reverse=True)

    if not mp4_files and not srt_files:
        print("No lecture MP4 or SRT files found in Downloads.")
        return None

    # Pivot on the latest media/transcript file
    pivot_file = mp4_files[0] if mp4_files else srt_files[0]
    pivot_name = pivot_file.stem
    pivot_words = get_words(pivot_name)
    
    print(f"Pivot file: {pivot_file.name}")
    print(f"Pivot keywords: {pivot_words}")

    # Group files that match the pivot words
    group = {
        "mp4": None,
        "srt": None,
        "pdfs": []
    }

    # Match MP4
    for f in mp4_files:
        if f == pivot_file or (get_words(f.stem) & pivot_words):
            group["mp4"] = f
            break

    # Match SRT
    for f in srt_files:
        if f == pivot_file or (get_words(f.stem) & pivot_words):
            group["srt"] = f
            break

    # Match PDFs (collect all matching PDFs, as there might be both Slides and Notes)
    for f in pdf_files:
        # Check if the PDF overlaps significantly with the pivot keywords
        overlap = get_words(f.stem) & pivot_words
        if len(overlap) >= 2 or (pivot_words and f.stem.lower() in pivot_name.lower()) or (f.stem.lower() in pivot_name.lower()):
            group["pdfs"].append(f)

    return group

def ingest(downloads_path=None, workspace_path=None):
    if not workspace_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace = Path(os.path.abspath(os.path.join(script_dir, "..")))
    else:
        workspace = Path(workspace_path)
    input_dir = workspace / "lecture-input"
    input_dir.mkdir(parents=True, exist_ok=True)

    group = find_lecture_group(downloads_path)
    if not group:
        return False

    print("\n--- Detected Ingestion Group ---")
    print(f"MP4:  {group['mp4'].name if group['mp4'] else 'None'}")
    print(f"SRT:  {group['srt'].name if group['srt'] else 'None'}")
    print(f"PDFs: {[f.name for f in group['pdfs']]}")
    print("--------------------------------\n")

    # Clean up old files in lecture-input/
    for item in input_dir.iterdir():
        if item.is_file() and item.name != ".gitkeep":
            item.unlink()

    # Copy MP4
    if group["mp4"]:
        dest = input_dir / "LECTURE.mp4"
        shutil.copy(group["mp4"], dest)
        print(f"Copied MP4 to {dest.relative_to(workspace)}")

    # Copy SRT
    if group["srt"]:
        dest = input_dir / "transcript.srt"
        shutil.copy(group["srt"], dest)
        print(f"Copied SRT to {dest.relative_to(workspace)}")

    # Save original lecture title
    original_title = None
    if group["mp4"]:
        original_title = group["mp4"].stem
    elif group["srt"]:
        original_title = group["srt"].stem

    if original_title:
        # Clean title slightly: replace multiple dashes or underscores with a single space
        cleaned_title = re.sub(r'[-_]+', ' ', original_title).strip()
        # Capitalize nicely if it was all lowercase, but keep mixed case
        if cleaned_title.islower():
            cleaned_title = cleaned_title.title()
        
        title_file = input_dir / "lecture_title.txt"
        with open(title_file, "w", encoding="utf-8") as f:
            f.write(cleaned_title)
        print(f"Saved original lecture title to {title_file.relative_to(workspace)}")

    # Copy and classify PDFs
    copied_slides = False
    copied_reference = False
    for pdf in group["pdfs"]:
        name_lower = pdf.name.lower()
        if "note" in name_lower or "reference" in name_lower or "handwritten" in name_lower:
            if not copied_reference:
                dest = input_dir / "REFERENCE_NOTES.pdf"
                shutil.copy(pdf, dest)
                print(f"Copied Reference Note to {dest.relative_to(workspace)}")
                copied_reference = True
        else:
            if not copied_slides:
                dest = input_dir / "SLIDES.pdf"
                shutil.copy(pdf, dest)
                print(f"Copied Slide Deck to {dest.relative_to(workspace)}")
                copied_slides = True

    print("\nIngestion completed successfully.")
    return True

if __name__ == "__main__":
    success = ingest()
    sys.exit(0 if success else 1)

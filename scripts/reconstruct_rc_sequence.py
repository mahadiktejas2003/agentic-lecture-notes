#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys

# Define the two Reading Comprehension lectures
lectures = [
    {
        "id": "Live-15",
        "title": "Live-15 English Introduction to Reading Comprehension",
        "video": "/Users/tejasmahadik/Downloads/Live-15 English Introduction to Reading Comprehension .mp4",
        "reference_pdf": "/Users/tejasmahadik/Downloads/Lec 15 Intro to R.C. -Created. by TEjas.pdf",
        "soundscribe_manifest": "/Users/tejasmahadik/SoundScribe/Live-15 English Introduction to Reading Comprehension _transcript.soundscribejob/manifest.json",
        "safe_name": "Live-15_Introduction_to_Reading_Comprehension"
    },
    {
        "id": "Live-16",
        "title": "Live-16 English Sample RC Passage and discussion",
        "video": "/Users/tejasmahadik/Downloads/Live-16 English Sample RC Passage and discussion.mp4",
        "reference_pdf": "/Users/tejasmahadik/Downloads/Lec-16 Sample RC Passage and discussion - Tejas created.pdf",
        "soundscribe_manifest": "/Users/tejasmahadik/SoundScribe/Live-16 English Sample RC Passage and discussion_transcript.soundscribejob/manifest.json",
        "safe_name": "Live-16_Sample_RC_Passage_and_discussion"
    }
]

def run_cmd(cmd):
    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"Command failed with exit code {res.returncode}")
        sys.exit(res.returncode)

def main():
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(workspace)
    os.makedirs("lecture-input", exist_ok=True)
    os.makedirs("notes-output", exist_ok=True)

    start_index = 0
    if len(sys.argv) > 1:
        try:
            start_index = int(sys.argv[1])
            print(f"Resuming queue from index {start_index}")
        except ValueError:
            pass

    for i in range(start_index, len(lectures)):
        lec = lectures[i]
        print(f"\n==========================================")
        print(f"STARTING RECONSTRUCTION FOR: {lec['title']}")
        print(f"==========================================\n")

        # 1. Clean workspace cache files and old inputs
        print("Cleaning workspace cache files and input directory...")
        for f in ["concept_block_map.json", "frame_manifest.json", "slide_manifest.json", "reference_manifest.json", "embedded_manifest.json", "inserted_images.json"]:
            if os.path.exists(f):
                os.remove(f)
                print(f"Removed cache: {f}")

        # Clear inputs in lecture-input
        for item in os.listdir("lecture-input"):
            fp = os.path.join("lecture-input", item)
            if os.path.isfile(fp) and not item.startswith("."):
                os.remove(fp)
                print(f"Cleared input file: {item}")
        
        # Clear stale reference folders if they exist
        for folder in ["reference_pages", "reference_screenshots", "screenshots", "slides"]:
            if os.path.exists(folder):
                try:
                    shutil.rmtree(folder)
                    print(f"Cleared stale directory: {folder}")
                except Exception as e:
                    print(f"Warning: Failed to clear stale directory {folder}: {e}")

        # 2. Stage new source files
        print(f"Copying video: {lec['video']}")
        shutil.copy2(lec["video"], "lecture-input/LECTURE.mp4")

        print(f"Copying reference PDF: {lec['reference_pdf']}")
        shutil.copy2(lec["reference_pdf"], "lecture-input/REFERENCE_NOTES.pdf")

        # Save title
        with open("lecture-input/lecture_title.txt", "w", encoding="utf-8") as f:
            f.write(lec["title"])

        # 3. Convert SoundScribe manifest to SRT
        print(f"Converting SoundScribe: {lec['soundscribe_manifest']}")
        run_cmd([
            "venv/bin/python", "scripts/soundscribe_to_srt.py",
            lec["soundscribe_manifest"], "lecture-input/transcript.srt"
        ])

        # 4. Run orchestrator
        print("Running LangGraph orchestrator...")
        run_cmd(["venv/bin/python", "scripts/langgraph_orchestrator.py"])

        # 5. Run audit check
        print("Auditing notes...")
        run_cmd(["venv/bin/python", "scripts/audit.py", "--docx", "notes-output/LECTURE_NOTES.docx"])

        # 6. Copy output files to distinct names
        print("Copying final outputs to distinct files...")
        notes_dest = f"notes-output/{lec['safe_name']}_NOTES.docx"
        short_note_dest = f"notes-output/{lec['safe_name']}_SHORTNOTE.md"

        if os.path.exists("notes-output/LECTURE_NOTES.docx"):
            shutil.copy2("notes-output/LECTURE_NOTES.docx", notes_dest)
            print(f"Saved: {notes_dest}")
        else:
            print("Error: notes-output/LECTURE_NOTES.docx was not generated!")
            sys.exit(1)

        if os.path.exists("notes-output/LECTURE_SHORTNOTE.md"):
            shutil.copy2("notes-output/LECTURE_SHORTNOTE.md", short_note_dest)
            print(f"Saved: {short_note_dest}")
        else:
            print("Warning: notes-output/LECTURE_SHORTNOTE.md was not generated!")

        print(f"\n==========================================")
        print(f"SUCCESSFULLY FINISHED: {lec['title']}")
        print(f"==========================================\n")

if __name__ == "__main__":
    main()

import os
import shutil
import subprocess
import sys

lectures = [
    {
        "id": "Lec-7",
        "title": "Lec-7 - One to One Relationship Partial",
        "video": "/Users/tejasmahadik/Downloads/Lec-7 One to one Relationship Partial .mp4",
        "soundscribe": "/Users/tejasmahadik/SoundScribe/Lec-7 One to one Relationship Partial _transcript.soundscribejob/manifest.json"
    },
    {
        "id": "Lec-8",
        "title": "Lec-8 - One to One (Total) Relationship",
        "video": "/Users/tejasmahadik/Downloads/Lec-8 One to One (Total) Relationship.mp4",
        "soundscribe": "/Users/tejasmahadik/SoundScribe/Lec-8 One to One (Total) Relationship_transcript.soundscribejob/manifest.json"
    },
    {
        "id": "Lec-9",
        "title": "Lec-9 - One to Many Relationship",
        "video": "/Users/tejasmahadik/Downloads/Lec-9 One to Many Relationship.mp4",
        "soundscribe": "/Users/tejasmahadik/SoundScribe/Lec-9 One to Many Relationship_transcript.soundscribejob/manifest.json"
    },
    {
        "id": "Lec-10",
        "title": "Lec-10 - Many to Many Relationship",
        "video": "/Users/tejasmahadik/Downloads/Lec-10 Many to Many Relationship.mp4",
        "soundscribe": "/Users/tejasmahadik/SoundScribe/Lec-10 Many to Many Relationship_transcript.soundscribejob/manifest.json"
    }
]

shared_slides = "/Users/tejasmahadik/Downloads/Lec-7,-8,-9,-10-Types-of-Relationships.pdf"

def run_cmd(cmd):
    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"Command failed with exit code {res.returncode}")
        sys.exit(res.returncode)

def main():
    # Make sure we are in the workspace root
    os.makedirs("lecture-input", exist_ok=True)
    
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
        
        # 1. Clean workspace cache files
        for f in ["concept_block_map.json", "frame_manifest.json", "slide_manifest.json", "reference_manifest.json"]:
            if os.path.exists(f):
                os.remove(f)
                print(f"Removed cache: {f}")
                
        for f in ["lecture-input/REFERENCE_NOTES.txt", "lecture-input/REFERENCE_NOTES.pdf"]:
            if os.path.exists(f):
                os.remove(f)
                
        # 2. Stage source files
        print(f"Copying video: {lec['video']}")
        shutil.copy(lec["video"], "lecture-input/LECTURE.mp4")
        
        print(f"Copying slides: {shared_slides}")
        shutil.copy(shared_slides, "lecture-input/SLIDES.pdf")
        
        # Write title
        with open("lecture-input/lecture_title.txt", "w", encoding="utf-8") as f:
            f.write(lec["title"])
            
        # 3. Convert SoundScribe manifest to SRT
        print(f"Converting SoundScribe: {lec['soundscribe']}")
        run_cmd([
            "venv/bin/python", "scripts/soundscribe_to_srt.py",
            lec["soundscribe"], "lecture-input/transcript.srt"
        ])
        
        # 4. Run orchestrator
        print(f"Running orchestrator...")
        run_cmd(["venv/bin/python", "scripts/langgraph_orchestrator.py"])
        
        # 5. Run audit check
        print(f"Auditing notes...")
        run_cmd(["venv/bin/python", "scripts/audit.py", "--docx", "notes-output/LECTURE_NOTES.docx"])
        
        print(f"\n==========================================")
        print(f"SUCCESSFULLY FINISHED: {lec['title']}")
        print(f"==========================================\n")

if __name__ == "__main__":
    main()

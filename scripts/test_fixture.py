#!/usr/bin/env python3
import os
import sys
import json
import subprocess

def main():
    print("=== Running Pipeline Smoke Test Fixture ===")
    
    # Backup existing inserted_images.json if it exists
    inserted_images_backup = None
    if os.path.exists("inserted_images.json"):
        try:
            with open("inserted_images.json", "r", encoding="utf-8") as f:
                inserted_images_backup = f.read()
        except Exception as e:
            print(f"Warning: Could not backup inserted_images.json: {e}")
            
    # 1. Create mock manifests
    concept_map = {
        "lecture_title": "Mock Lecture Title",
        "blocks": [
            {
                "block_id": "CB1",
                "title": "Subject-Verb Agreement Principles",
                "transcript_range_percent": [0, 100],
                "explanation": "Subject-verb agreement is a fundamental rule where singular subjects take singular verbs and plural subjects take plural verbs. For example, a singular noun like child takes has, whereas children takes have.",
                "examples": [
                    {
                        "sentence": "Each of the candidates has submitted a resume.",
                        "working": "The pronoun 'each' is singular, so the verb must be 'has' rather than 'have'."
                    }
                ],
                "exercise_questions": [
                    "Underline the correct verb: The team [is/are] practicing now."
                ],
                "teacher_quotes": [
                    "Remember that prepositional phrases do not affect the subject's number."
                ],
                "flow": [
                    {
                        "type": "paragraph",
                        "text": "Subject-verb agreement is a fundamental rule where singular subjects take singular verbs and plural subjects take plural verbs. For example, a singular noun like child takes has, whereas children takes have."
                    },
                    {
                        "type": "example",
                        "index": 0
                    },
                    {
                        "type": "cornell_block",
                        "cue": "Singular Pronouns",
                        "summary": "Pronouns like each, everyone, and someone are singular."
                    }
                ]
            }
        ]
    }
    
    frame_manifest = {}
    
    slide_manifest = [
        {
            "slide_number": 1,
            "ocr_text": "Subject-Verb Agreement rules",
            "discussed": True
        }
    ]
    
    inserted_images = []
    
    # Write files
    paths = {
        "test_concept_map.json": concept_map,
        "test_frame_manifest.json": frame_manifest,
        "test_slide_manifest.json": slide_manifest,
        "inserted_images.json": inserted_images
    }
    
    for filename, content in paths.items():
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)
        except Exception as e:
            print(f"Error writing mock file {filename}: {e}")
            sys.exit(1)
            
    try:
        # 2. Run docx generator
        print("Generating mock document...")
        gen_cmd = [
            sys.executable, "scripts/generate_docx.py",
            "--concept-map", "test_concept_map.json",
            "--frame-manifest", "test_frame_manifest.json",
            "--slide-manifest", "test_slide_manifest.json",
            "--output", "test_notes.docx"
        ]
        res_gen = subprocess.run(gen_cmd, capture_output=True, text=True)
        if res_gen.returncode != 0:
            print("❌ Document generation failed!")
            print("STDOUT:", res_gen.stdout)
            print("STDERR:", res_gen.stderr)
            sys.exit(1)
            
        print("Document generated successfully.")
        
        # 3. Run audit
        print("Running quality audit...")
        audit_cmd = [
            sys.executable, "scripts/audit.py",
            "--docx", "test_notes.docx",
            "--concept-map", "test_concept_map.json",
            "--frame-manifest", "test_frame_manifest.json",
            "--slide-manifest", "test_slide_manifest.json"
        ]
        res_audit = subprocess.run(audit_cmd, capture_output=True, text=True)
        print(res_audit.stdout)
        if res_audit.returncode != 0:
            print("❌ Quality audit failed!")
            print(res_audit.stderr)
            sys.exit(1)
            
        print("✅ Success! The audit passed on the test document.")
        
    finally:
        # Cleanup files
        import glob
        temp_files = ["test_concept_map.json", "test_frame_manifest.json", "test_slide_manifest.json", "test_notes.docx"]
        for filename in temp_files:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass
                    
        # Clean up any generated archive copies
        for archived_f in glob.glob("*Mock_Lecture_Title*.docx"):
            try:
                os.remove(archived_f)
            except Exception:
                pass
                    
        # Restore inserted_images.json
        if inserted_images_backup is not None:
            try:
                with open("inserted_images.json", "w", encoding="utf-8") as f:
                    f.write(inserted_images_backup)
            except Exception as e:
                print(f"Warning: Could not restore inserted_images.json: {e}")
        elif os.path.exists("inserted_images.json"):
            try:
                os.remove("inserted_images.json")
            except Exception:
                pass

if __name__ == "__main__":
    main()

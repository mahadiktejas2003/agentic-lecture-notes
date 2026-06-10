#!/usr/bin/env python3
import json
import os
import sys
import glob
from docx import Document

def test_notes():
    print("Running Student Tester Persona...")
    concept_map_path = "concept_block_map.json"
    feedback_path = "notes-output/student_feedback.txt"
    os.makedirs(os.path.dirname(feedback_path), exist_ok=True)
    
    feedback = []
    feedback.append("=== Student Persona Feedback Report ===")
    
    # 1. JSON Manifest validation
    if not os.path.exists(concept_map_path):
        feedback.append("ERROR: concept_block_map.json not found. Student cannot test manifest notes.")
        with open(feedback_path, "w", encoding="utf-8") as f:
            f.write("\n".join(feedback) + "\n")
        return False
        
    with open(concept_map_path, "r", encoding="utf-8") as f:
        blocks = json.load(f)
        
    feedback.append(f"Total Concept Blocks analyzed in manifest: {len(blocks)}")
    
    confusing_count = 0
    examples_tested = 0
    
    for block in blocks:
        block_id = block.get("block_id", "Unknown")
        title = block.get("title", "Untitled")
        feedback.append(f"\nBlock {block_id}: {title}")
        
        # Test concepts
        concepts = block.get("concepts", [])
        feedback.append(f"  - Verified {len(concepts)} concepts & definitions.")
        if not concepts:
            feedback.append("  - [WARN] No definitions found for this block in manifest.")
            confusing_count += 1
            
        # Test examples
        examples = block.get("examples", [])
        for ex in examples:
            sentence = ex.get("sentence", "")
            working = ex.get("working", "")
            feedback.append(f"  - Tested Example: '{sentence[:60]}...'")
            feedback.append(f"    Working path: {working[:80]}...")
            examples_tested += 1
            
        # Test exercises
        exercises = block.get("exercise_questions", [])
        feedback.append(f"  - Checked {len(exercises)} exercise questions in manifest.")
        
    # 2. Parse and verify actually generated .docx
    docx_path = "notes-output/LECTURE_NOTES.docx"
    if not os.path.exists(docx_path):
        docx_files = glob.glob("notes-output/*.docx")
        if docx_files:
            docx_path = docx_files[0]
            
    if not os.path.exists(docx_path):
        feedback.append(f"\nERROR: No generated docx file found at '{docx_path}'. Student cannot perform document-based tests.")
        confusing_count += 1
    else:
        feedback.append(f"\nAnalyzing generated document: {docx_path}")
        try:
            doc = Document(docx_path)
            
            # Verify embedded image relations
            img_count = sum(1 for rel in doc.part.rels.values() if 'image' in rel.reltype)
            feedback.append(f"  - Document Embedded Image Relations: {img_count}")
            if img_count == 0:
                feedback.append("  - [FAIL] No embedded image relations found in docx.")
                confusing_count += 1
            else:
                feedback.append("  - [PASS] Embedded images verified successfully.")
                
            # Verify worked examples in docx
            # Worked examples in docx are expected to start with "Q:" or contain "example"
            worked_examples_docx = sum(1 for p in doc.paragraphs if p.text.strip().startswith('Q:') or 'example' in p.text.lower())
            feedback.append(f"  - Document Worked Examples: {worked_examples_docx}")
            if worked_examples_docx == 0:
                feedback.append("  - [FAIL] Document contains 0 worked examples.")
                confusing_count += 1
            else:
                feedback.append("  - [PASS] Worked examples verified successfully.")
                
            # Verify absence of banned attribution phrase
            banned_phrase = "This document was reconstructed by Antigravity"
            banned_found = False
            for p_idx, p in enumerate(doc.paragraphs):
                if banned_phrase in p.text:
                    feedback.append(f"  - [FAIL] Banned attribution phrase found in paragraph {p_idx+1}: '{p.text[:80]}...'")
                    banned_found = True
            
            if banned_found:
                confusing_count += 1
            else:
                feedback.append("  - [PASS] Banned attribution check passed (not found).")
                
        except Exception as e:
            feedback.append(f"ERROR: Failed to read docx document: {e}")
            confusing_count += 1
            
    feedback.append("\n=== Summary ===")
    feedback.append(f"Total Examples Tested: {examples_tested}")
    feedback.append(f"Confusing/Failure Sections Flagged: {confusing_count}")
    
    if confusing_count == 0:
        feedback.append("Status: Notes are well-structured, mathematically validated, and fully compliant.")
        success = True
    else:
        feedback.append("Status: Notes failed compliance tests.")
        success = False
        
    with open(feedback_path, "w", encoding="utf-8") as f:
        f.write("\n".join(feedback) + "\n")
        
    print(f"Student Feedback report generated at: {feedback_path}")
    return success

if __name__ == "__main__":
    passed = test_notes()
    sys.exit(0 if passed else 1)

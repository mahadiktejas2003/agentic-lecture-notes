#!/usr/bin/env python3
import os
import sys
import json
import re

def clean_transcript(srt_path):
    if not os.path.exists(srt_path):
        return ""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Strip timestamps and line numbers
    lines = content.split('\n')
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\d+$', line):
            continue
        if '-->' in line:
            continue
        text_lines.append(line)
    return " ".join(text_lines)

def analyze_lecture(srt_path):
    text = clean_transcript(srt_path)
    word_count = len(text.split())
    
    # Keyword matches
    syllabus_keywords = ['syllabus', 'overview', 'outline', 'weightage', 'topics', 'cover karenge', 'mains exam', 'syllabus checklist']
    syllabus_count = sum(1 for kw in syllabus_keywords if kw in text.lower())
    
    # Classification logic
    # Syllabus lectures are typically short (<10 minutes, <1500 words) and have high syllabus keyword density
    is_syllabus = (word_count < 1800 and syllabus_count >= 2) or ("syllabus" in text.lower())
    
    if is_syllabus:
        profile = {
            "lecture_type": "Syllabus/Intro",
            "notes_style": "Compact",
            "recommended_blocks": 3,
            "recommended_frames": 2,
            "generate_worked_examples": False,
            "generate_theoretical_theory": False,
            "visual_appendix_limit": 2,
            "focus_areas": ["Syllabus Outline", "Exam Weightage", "Preparation Strategy"],
            "explanation_limit": 400
        }
    else:
        profile = {
            "lecture_type": "Technical/Content",
            "notes_style": "Comprehensive",
            "recommended_blocks": 8,
            "recommended_frames": 15,
            "generate_worked_examples": True,
            "generate_theoretical_theory": True,
            "visual_appendix_limit": 20,
            "focus_areas": ["Detailed Concepts", "Worked Examples", "Traps and Tricks"],
            "explanation_limit": 600
        }
        
    profile["word_count"] = word_count
    profile["syllabus_keyword_matches"] = syllabus_count
    return profile

def main():
    srt_path = "lecture-input/transcript.srt"
    if len(sys.argv) > 1:
        srt_path = sys.argv[1]
        
    if not os.path.exists(srt_path):
        print(f"Error: Transcript not found at {srt_path}")
        sys.exit(1)
        
    profile = analyze_lecture(srt_path)
    
    with open("lecture_profile.json", "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
        
    print(f"✅ Analyzed lecture type: {profile['lecture_type']} (Words: {profile['word_count']}, Style: {profile['notes_style']})")
    print("Saved profile to lecture_profile.json")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import sys
import json
import glob
import datetime

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

SKILL_MAP = {
    1: (".agents/skills/note-composition/SKILL.md", "note-composition"),
    2: (".agents/skills/note-composition/SKILL.md", "note-composition"),
    3: (".agents/skills/note-composition/SKILL.md", "note-composition"),
    4: (".agents/skills/transcript-mapping/SKILL.md", "transcript-mapping"),
    5: (".agents/skills/note-composition/SKILL.md", "note-composition"),
    6: (".agents/skills/frame-extraction/SKILL.md", "frame-extraction"),
    7: (".agents/skills/note-composition/SKILL.md", "note-composition"),
    8: (".agents/skills/note-composition/SKILL.md", "note-composition"),
    9: (".agents/skills/slide-parsing/SKILL.md", "slide-parsing"),
    10: (".agents/skills/note-composition/SKILL.md", "note-composition"),
    11: (".agents/skills/note-composition/SKILL.md", "note-composition"),
    12: (".agents/skills/transcript-mapping/SKILL.md", "transcript-mapping"),
    13: (".agents/skills/transcript-mapping/SKILL.md", "transcript-mapping"),
    14: (".agents/skills/transcript-mapping/SKILL.md", "transcript-mapping"),
    15: (".agents/skills/transcript-mapping/SKILL.md", "transcript-mapping"),
}

PROPOSED_DIFFS = {
    1: """diff --git a/.agents/skills/note-composition/SKILL.md b/.agents/skills/note-composition/SKILL.md
--- a/.agents/skills/note-composition/SKILL.md
+++ b/.agents/skills/note-composition/SKILL.md
@@ -35,2 +35,3 @@
 ## Hardened Composition Constraints
 - **Structural Check**: Enforce that Heading 2 count is greater than zero and matches the revision box count exactly. Check for zero banned attributions.
""",
    2: """diff --git a/.agents/skills/note-composition/SKILL.md b/.agents/skills/note-composition/SKILL.md
--- a/.agents/skills/note-composition/SKILL.md
+++ b/.agents/skills/note-composition/SKILL.md
@@ -35,2 +35,3 @@
 ## Hardened Composition Constraints
 - **Revision Box Placement**: Ensure every single H2 section ends with a light-blue revision box containing key quick-rev bullets.
""",
    3: """diff --git a/.agents/skills/note-composition/SKILL.md b/.agents/skills/note-composition/SKILL.md
--- a/.agents/skills/note-composition/SKILL.md
+++ b/.agents/skills/note-composition/SKILL.md
@@ -35,2 +35,3 @@
 ## Hardened Composition Constraints
 - **Chronological Outline**: Ensure Heading 2 section headers align exactly with the list of concept blocks from the concept block map.
""",
    4: """diff --git a/.agents/skills/transcript-mapping/SKILL.md b/.agents/skills/transcript-mapping/SKILL.md
--- a/.agents/skills/transcript-mapping/SKILL.md
+++ b/.agents/skills/transcript-mapping/SKILL.md
@@ -34,2 +34,3 @@
 ## Hardened Mapping Constraints
 - **Completion Check**: Verify that transcript scanning yields at least 2 distinct concept blocks with real content.
""",
    5: """diff --git a/.agents/skills/note-composition/SKILL.md b/.agents/skills/note-composition/SKILL.md
--- a/.agents/skills/note-composition/SKILL.md
+++ b/.agents/skills/note-composition/SKILL.md
@@ -35,2 +35,3 @@
 ## Hardened Composition Constraints
 - **Factual Accuracy**: Cross-reference each generated example with the transcript map. Verify all calculations and steps are exact.
""",
    6: """diff --git a/.agents/skills/frame-extraction/SKILL.md b/.agents/skills/frame-extraction/SKILL.md
--- a/.agents/skills/frame-extraction/SKILL.md
+++ b/.agents/skills/frame-extraction/SKILL.md
@@ -46,2 +46,3 @@
 6. Write `frame_manifest.json` using `write_file`.
+- **Image Integrity Check**: Ensure all visual anchor cues lead to successfully cropped images with readable content.
""",
    7: """diff --git a/.agents/skills/note-composition/SKILL.md b/.agents/skills/note-composition/SKILL.md
--- a/.agents/skills/note-composition/SKILL.md
+++ b/.agents/skills/note-composition/SKILL.md
@@ -35,2 +35,3 @@
 ## Hardened Composition Constraints
 - **Minimum Count Enforcer**: Verify that at least 80% of expected visual assets (frames + slides) are successfully embedded in the final document.
""",
    8: """diff --git a/.agents/skills/note-composition/SKILL.md b/.agents/skills/note-composition/SKILL.md
--- a/.agents/skills/note-composition/SKILL.md
+++ b/.agents/skills/note-composition/SKILL.md
@@ -35,2 +35,3 @@
 ## Hardened Composition Constraints
 - **Traceability Rule**: Ensure that at least 50% of the concept blocks have direct teacher quotes or traps recorded to maintain link to source media.
""",
    9: """diff --git a/.agents/skills/slide-parsing/SKILL.md b/.agents/skills/slide-parsing/SKILL.md
--- a/.agents/skills/slide-parsing/SKILL.md
+++ b/.agents/skills/slide-parsing/SKILL.md
@@ -30,2 +30,3 @@
 3. Cross-reference transcript; map slides to timestamps.
+- **Slide Leak Prevention**: Verify that undiscussed slide content is never leaked or copied into the final generated document.
""",
    10: """diff --git a/.agents/skills/note-composition/SKILL.md b/.agents/skills/note-composition/SKILL.md
--- a/.agents/skills/note-composition/SKILL.md
+++ b/.agents/skills/note-composition/SKILL.md
@@ -35,2 +35,3 @@
 ## Hardened Composition Constraints
 - **Example Completeness**: Never drop or merge examples. Every example from the map must be formatted in a separate Q/Rule/Working/Answer block.
""",
    11: """diff --git a/.agents/skills/note-composition/SKILL.md b/.agents/skills/note-composition/SKILL.md
--- a/.agents/skills/note-composition/SKILL.md
+++ b/.agents/skills/note-composition/SKILL.md
@@ -35,2 +35,3 @@
 ## Hardened Composition Constraints
 - **Visual Density**: Double-check that all extracted board screenshots are inserted inline silently without placeholders.
""",
    12: """diff --git a/.agents/skills/transcript-mapping/SKILL.md b/.agents/skills/transcript-mapping/SKILL.md
--- a/.agents/skills/transcript-mapping/SKILL.md
+++ b/.agents/skills/transcript-mapping/SKILL.md
@@ -38,2 +38,3 @@
 - **Exercise Omissions**: Skip rendering any exercise item that lacks textual description or contains only placeholder values.
""",
    13: """diff --git a/.agents/skills/transcript-mapping/SKILL.md b/.agents/skills/transcript-mapping/SKILL.md
--- a/.agents/skills/transcript-mapping/SKILL.md
+++ b/.agents/skills/transcript-mapping/SKILL.md
@@ -36,2 +36,3 @@
 - **Quote Quality**: Clean each extracted teacher quote. Strip all SRT metadata (timestamps/line counters), leading stray vowel signs or symbols, ensure it is a complete sentence, and deduplicate identical quotes.
+- **SRT Artifact Filter**: Explicitly regex-match and filter out lines like `1` or `00:01:20,000 --> 00:01:25,000` from the quotes field.
""",
    14: """diff --git a/.agents/skills/transcript-mapping/SKILL.md b/.agents/skills/transcript-mapping/SKILL.md
--- a/.agents/skills/transcript-mapping/SKILL.md
+++ b/.agents/skills/transcript-mapping/SKILL.md
@@ -35,2 +35,3 @@
 - **Meaningful Block Titles**: Use the grammatical concept being taught as the title for each concept block, never generic question ranges (e.g. use "Disease Names & 'One Of' SVA Rules" instead of "Noun Practice Test Discussion (Questions 1 to 5)").
+- **Concept-Oriented Titles**: Ensure block titles describe the grammar rules or topic directly rather than referencing question numbers.
""",
    15: """diff --git a/.agents/skills/transcript-mapping/SKILL.md b/.agents/skills/transcript-mapping/SKILL.md
--- a/.agents/skills/transcript-mapping/SKILL.md
+++ b/.agents/skills/transcript-mapping/SKILL.md
@@ -38,2 +38,3 @@
 - **Explanation Conciseness**: Keep explanation texts under 600 characters and avoid starting sentences with repetitive phrases like "First,".
"""
}

def analyze_and_propose():
    print("Reading failure logs from agent_memory/failures/...")
    failure_files = glob.glob("agent_memory/failures/*.json")
    if not failure_files:
        print("No failure logs found. Skill improver has nothing to analyze.")
        return
        
    # Gather failed gates
    failed_counts = {}
    for filepath in failure_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                gates = data.get("failed_gates", [])
                for g in gates:
                    # Parse gate number (e.g. "Gate 13" -> 13)
                    if "Gate" in g:
                        num = int(g.replace("Gate", "").strip())
                        failed_counts[num] = failed_counts.get(num, 0) + 1
        except Exception as e:
            print(f"Warning: Failed to parse {filepath}: {e}")
            
    if not failed_counts:
        print("No specific gate failures identified in logs.")
        return
        
    print("Failure counts per gate:", failed_counts)
    
    # Generate proposed diffs directory
    os.makedirs("agent_memory/proposed_skill_diffs", exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for gate_num, count in failed_counts.items():
        if gate_num in SKILL_MAP:
            skill_path, skill_name = SKILL_MAP[gate_num]
            print(f"\nProposing skill diff for Gate {gate_num} (failed {count} times) -> {skill_name}")
            
            diff_text = PROPOSED_DIFFS.get(gate_num)
            if not diff_text:
                print(f"No predefined diff patch for Gate {gate_num}. Skipping.")
                continue
                
            filename = f"proposed_diff_Gate_{gate_num}_{timestamp}.diff"
            output_filepath = os.path.join("agent_memory/proposed_skill_diffs", filename)
            
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(diff_text)
                
            print(f"Proposed diff saved for human review: {output_filepath}")
            
if __name__ == "__main__":
    analyze_and_propose()

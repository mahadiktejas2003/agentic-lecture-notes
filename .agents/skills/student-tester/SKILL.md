---
name: student-tester
description: Reads generated notes, attempts example problems, and flags confusing sections.
---

# Student Tester Skill

## Tools
- `read_file` - notes
- `write_file` - feedback

## Execution
1. Read the generated notes from `notes-output/LECTURE_NOTES.docx`.
2. Identify all worked examples and attempt to solve them to verify the math.
3. Identify all concepts and definitions and check if they are clear and easy to understand.
4. Flag any confusing sections, missing formulas, or gaps in explanation.
5. Write feedback report to `notes-output/student_feedback.txt`.

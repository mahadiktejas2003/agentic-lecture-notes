#!/bin/bash
# pre-exec-check.sh — Verifies AGENTS.md and skill files exist and are readable.

# Array of required files
FILES=(
    "AGENTS.md"
    ".agents/skills/frame-extraction/SKILL.md"
    ".agents/skills/transcript-mapping/SKILL.md"
    ".agents/skills/slide-parsing/SKILL.md"
    ".agents/skills/note-composition/SKILL.md"
)

# Loop and check each file
for FILE in "${FILES[@]}"; do
    if [ ! -r "$FILE" ]; then
        echo "Error: Required file '$FILE' is missing or not readable." >&2
        exit 1
    fi
done

echo "Hook: pre-exec-check passed. All agent files are readable."
exit 0

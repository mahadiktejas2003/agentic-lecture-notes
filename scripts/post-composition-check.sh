#!/bin/bash
# post-composition-check.sh — Validates manifests are non-empty before composition.

# If video exists, frame_manifest.json must be populated
if [ -f "lecture-input/LECTURE.mp4" ]; then
    if [ -s frame_manifest.json ] && [ "$(cat frame_manifest.json)" != "{}" ]; then
        echo "Hook: frame_manifest.json is populated."
    else
        echo "Hook FAIL: frame_manifest.json is empty or missing (video is present)."; exit 1
    fi
else
    echo "Hook: No video file found. Skipping frame_manifest.json check."
fi

# concept_block_map.json must always exist and have at least 2 keys/elements
if [ -s concept_block_map.json ]; then
    python3 -c "import json; d=json.load(open('concept_block_map.json')); exit(0 if len(d)>=2 else 1)"
    if [ $? -eq 0 ]; then
        echo "Hook: concept_block_map.json has at least 2 keys/elements."
    else
        echo "Hook FAIL: concept_block_map.json has fewer than 2 keys/elements."; exit 1
    fi
else
    echo "Hook FAIL: concept_block_map.json missing."; exit 1
fi
echo "Hook: post-composition-check passed."
exit 0

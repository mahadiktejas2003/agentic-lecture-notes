#!/bin/bash
if [ -s frame_manifest.json ] && [ "$(cat frame_manifest.json)" != "{}" ]; then
    echo "Hook: frame_manifest.json is populated."
else
    echo "Hook FAIL: frame_manifest.json is empty or missing."; exit 1
fi
if [ -s concept_block_map.json ]; then
    python3 -c "import json; d=json.load(open('concept_block_map.json')); exit(0 if len(d)>=2 else 1)"
    if [ $? -eq 0 ]; then
        echo "Hook: concept_block_map.json has at least 2 blocks."
    else
        echo "Hook FAIL: concept_block_map.json has fewer than 2 blocks."; exit 1
    fi
else
    echo "Hook FAIL: concept_block_map.json missing."; exit 1
fi
echo "Hook: post-composition-check passed."
exit 0

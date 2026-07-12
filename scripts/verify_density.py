#!/usr/bin/env python3
import os
import sys
import json
import re
import argparse
import logging

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

def parse_srt_duration_and_cues(srt_path):
    """Parses SRT to get duration in minutes and check for visual cues."""
    if not os.path.exists(srt_path):
        logger.error(f"Transcript file not found: {srt_path}")
        return 0.0, 0
    
    with open(srt_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Duration parsing
    pattern = r'(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})'
    matches = list(re.finditer(pattern, content))
    duration_min = 0.0
    if matches:
        last_match = matches[-1]
        h, m, s, ms = int(last_match.group(5)), int(last_match.group(6)), int(last_match.group(7)), int(last_match.group(8))
        duration_min = (h * 3600 + m * 60 + s + ms / 1000.0) / 60.0
    
    # Visual cues count
    cue_words = ['board', 'slide', 'screen', 'look at', 'see here', 'dekhiye', 'dekho']
    content_lower = content.lower()
    cues_count = sum(content_lower.count(cue) for cue in cue_words)
    
    return duration_min, cues_count

def verify_density(concept_map_path, transcript_path):
    """
    Verifies density of concept blocks against the transcript.
    Returns (all_passed: bool, report: dict)
    """
    duration_min, cues_count = parse_srt_duration_and_cues(transcript_path)
    
    if not os.path.exists(concept_map_path):
        return False, {"error": f"Concept map not found: {concept_map_path}"}
        
    try:
        with open(concept_map_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return False, {"error": f"Failed to parse concept map JSON: {e}"}
        
    blocks = data.get('blocks', data) if isinstance(data, dict) else data
    if not isinstance(blocks, list):
        return False, {"error": "Invalid format: blocks is not a list"}
        
    total_examples = 0
    total_visual_moments = 0
    total_coverage_pct = 0
    meaningless_titles = []
    
    title_pattern = re.compile(r'^.*(Questions?\s*\d+)', re.IGNORECASE)
    
    for i, block in enumerate(blocks):
        examples = block.get('examples', [])
        total_examples += len(examples)
        
        visuals = block.get('visual_moments', [])
        total_visual_moments += len(visuals)
        
        rng = block.get('transcript_range_percent', [0, 0])
        if len(rng) == 2:
            total_coverage_pct += (rng[1] - rng[0])
            
        title = block.get('title', f"CB{i+1}")
        if title_pattern.match(title) or len(title.strip()) < 5:
            meaningless_titles.append(title)
            
    # Metrics calculations
    expected_density_threshold = 1.0
    target_examples = duration_min / 3.0
    example_density = total_examples / target_examples if target_examples > 0 else 0.0
    
    density_passed = example_density >= expected_density_threshold
    coverage_passed = total_coverage_pct >= 80
    
    visuals_passed = True
    if cues_count >= 5:
        visuals_passed = total_visual_moments >= 5
        
    titles_passed = len(meaningless_titles) == 0
    
    all_passed = density_passed and coverage_passed and visuals_passed and titles_passed
    
    report = {
        "duration_minutes": round(duration_min, 2),
        "total_examples": total_examples,
        "example_density": round(example_density, 2),
        "density_passed": density_passed,
        "total_coverage_pct": total_coverage_pct,
        "coverage_passed": coverage_passed,
        "visual_moments_count": total_visual_moments,
        "transcript_visual_cues": cues_count,
        "visuals_passed": visuals_passed,
        "meaningless_titles": meaningless_titles,
        "titles_passed": titles_passed,
        "all_passed": all_passed
    }
    
    return all_passed, report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Verify density of concept block map.")
    parser.add_argument('--concept-map', default='concept_block_map.json', help='Path to concept_block_map.json')
    parser.add_argument('--transcript', default='lecture-input/transcript.srt', help='Path to transcript.srt')
    args = parser.parse_args()
    
    logger.info(f"Verifying density of {args.concept_map} against {args.transcript}")
    passed, report = verify_density(args.concept_map, args.transcript)
    
    logger.info("=== Coverage Report ===")
    logger.info(f"Duration (min): {report.get('duration_minutes')}")
    logger.info(f"Total Examples: {report.get('total_examples')}")
    logger.info(f"Example Density (Target >= 1.0): {report.get('example_density')}")
    logger.info(f"Density Check Passed: {report.get('density_passed')}")
    logger.info(f"Total Coverage %: {report.get('total_coverage_pct')}%")
    logger.info(f"Coverage Check Passed: {report.get('coverage_passed')}")
    logger.info(f"Visual Moments Count: {report.get('visual_moments_count')}")
    logger.info(f"Visual Cue Words in SRT: {report.get('transcript_visual_cues')}")
    logger.info(f"Visuals Check Passed: {report.get('visuals_passed')}")
    logger.info(f"Meaningless Titles Found: {report.get('meaningless_titles')}")
    logger.info(f"Titles Check Passed: {report.get('titles_passed')}")
    logger.info(f"All Checks Passed: {report.get('all_passed')}")
    
    if not passed:
        logger.error("❌ Density verification failed!")
        sys.exit(1)
    else:
        logger.info("✅ Density verification passed successfully.")
        sys.exit(0)

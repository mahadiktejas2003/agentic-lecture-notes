#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
from typing import Dict, List, Tuple


def load_concept_map(path: str) -> Tuple[str, List[Dict]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("lecture_title", "Unknown Lecture"), data.get("blocks", [])
    if isinstance(data, list):
        lecture_title = data[0].get("lecture_title") if data else "Unknown Lecture"
        return lecture_title or "Unknown Lecture", data
    return "Unknown Lecture", []


def load_json_if_exists(path: str):
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_text_if_exists(path: str) -> str:
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[\u0900-\u097F]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def stringify_item(item) -> str:
    if not item:
        return ""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        parts = []
        for key in ["name", "title", "scenario"]:
            if item.get(key):
                parts.append(f"**{item.get(key)}**:")
                break
        
        main_text = ""
        for key in ["trap", "description", "note", "sentence"]:
            if item.get(key):
                main_text = item.get(key)
                break
        
        if main_text:
            parts.append(main_text)
            
        for key in ["danger", "prevention", "correction", "rule", "working"]:
            if item.get(key):
                parts.append(f"({key.capitalize()}: {item.get(key)})")
                
        if parts:
            return " ".join(parts)
            
        return " ".join(str(v) for v in item.values() if v)
        
    return str(item)


def strip_markup(text) -> str:
    if not isinstance(text, str):
        text = stringify_item(text)
    if not text:
        return ""
    text = clean_text(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("**", "").replace("*", "")
    return text.strip()


def shorten(text: str, limit: int) -> str:
    cleaned = strip_markup(text)
    if len(cleaned) > limit:
        return cleaned[:limit].strip() + "..."
    return cleaned


def slugify(text: str) -> str:
    text = clean_text(text).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "lecture"


def extract_markdown_from_output(output: str) -> str:
    if not output:
        return ""
    # Try matching explicit markdown/md code block
    fence_match = re.search(r"```(?:markdown|md)\s*(.*?)\s*```", output, re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip() + "\n"
    # If the entire output starts and ends with generic code fences, extract the inside
    generic_match = re.match(r"^\s*```[a-zA-Z0-9_-]*\s*(.*?)\s*```\s*$", output, re.DOTALL)
    if generic_match:
        return generic_match.group(1).strip() + "\n"
    return output.strip() + "\n"


def load_short_note_skill_prompt() -> str:
    skill_path = os.path.join(".agents", "skills", "short-note-composer", "SKILL.md")
    return load_text_if_exists(skill_path)


def summarize_examples(block: Dict, limit: int = 100) -> List[Dict]:
    summary = []
    for ex in (block.get("examples") or [])[:limit]:
        summary.append({
            "sentence": shorten(ex.get("sentence", ""), 500),
            "rule": shorten(ex.get("rule", ""), 500),
            "student_notes": shorten(ex.get("student_notes", ""), 500),
            "cloze_text": shorten(ex.get("cloze_text", ""), 500),
        })
    return summary


def summarize_blocks_for_llm(blocks: List[Dict], limit: int = 100) -> List[Dict]:
    summarized = []
    for block in blocks[:limit]:
        summarized.append({
            "title": shorten(block.get("title", ""), 500),
            "explanation": shorten(block.get("explanation", ""), 1000),
            "concepts": [
                {
                    "term": shorten(c.get("term", ""), 500),
                    "definition": shorten(c.get("definition", ""), 500),
                }
                for c in (block.get("concepts") or [])[:20]
            ],
            "examples": summarize_examples(block),
            "teacher_quotes": [shorten(q, 500) for q in (block.get("teacher_quotes") or [])[:20]],
            "traps": [shorten(t, 500) for t in (block.get("traps") or [])[:20]],
            "tricks": [shorten(t, 500) for t in (block.get("tricks") or [])[:20]],
        })
    return summarized


def summarize_slide_manifest_for_llm(slide_manifest) -> List[Dict]:
    if not isinstance(slide_manifest, list):
        return []
    summarized = []
    for slide in slide_manifest[:30]:
        summarized.append({
            "slide_number": slide.get("slide_number"),
            "discussed": slide.get("discussed"),
            "ocr_text": shorten(slide.get("ocr_text", ""), 500),
        })
    return summarized


def summarize_frame_manifest_for_llm(frame_manifest) -> List[Dict]:
    items = []
    if isinstance(frame_manifest, dict) and "frames" in frame_manifest and isinstance(frame_manifest["frames"], list):
        source = frame_manifest["frames"]
    elif isinstance(frame_manifest, list):
        source = frame_manifest
    elif isinstance(frame_manifest, dict):
        source = list(frame_manifest.values())
    else:
        source = []
    for item in source[:30]:
        items.append({
            "timestamp": item.get("timestamp"),
            "description": shorten(item.get("description", ""), 500),
            "ocr_text": shorten(item.get("ocr_text", ""), 500),
        })
    return items


def call_antigravity_markdown(prompt: str, timeout: int = 900) -> str:
    cli_path = (
        os.environ.get("ANTIGRAVITY_CLI_PATH")
        or shutil.which("antigravity")
        or "/Users/tejasmahadik/.gemini/antigravity/bin/antigravity"
    )
    if not os.path.exists(cli_path):
        raise FileNotFoundError(f"Antigravity CLI not found at: {cli_path}")
    result = subprocess.run(
        [cli_path, "chat", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Antigravity returned {result.returncode}")
    markdown = extract_markdown_from_output(result.stdout)
    if len(markdown.strip()) < 120:
        raise RuntimeError("Antigravity returned empty or too-short markdown output")
    return markdown


def classify_subject(lecture_title: str, blocks: List[Dict]) -> str:
    blob = " ".join(
        [lecture_title]
        + [b.get("title", "") for b in blocks]
        + [b.get("explanation", "") for b in blocks[:3]]
    ).lower()
    categories = {
        "math": ["aptitude", "permutation", "combination", "probability", "algebra", "equation", "ratio", "percentage", "distance", "direction", "quant", "time and work"],
        "reasoning": ["reasoning", "syllogism", "seating", "blood relation", "puzzle", "coding", "decoding", "inequality", "direction sense"],
        "english": ["pronoun", "noun", "verb", "grammar", "vocabulary", "adjective", "article", "preposition", "english"],
        "technical": ["cpu", "dbms", "operating system", "network", "python", "java", "algorithm", "database", "scheduling", "programming"],
        "gk": ["current affairs", "repo", "reverse repo", "polity", "geography", "history", "economy", "awareness"],
    }
    for subject, keywords in categories.items():
        if any(k in blob for k in keywords):
            return subject
    return "theory"


def infer_core_question(lecture_title: str, subject: str) -> str:
    title = strip_markup(lecture_title)
    templates = {
        "math": f"What are the core rules, shortcuts, and recurring solved patterns in {title}?",
        "reasoning": f"What are the core rules, decision paths, and traps in {title}?",
        "english": f"What are the rules, examples, and common errors in {title}?",
        "technical": f"What are the key concepts, why do they matter, and what are the exam traps in {title}?",
        "gk": f"What are the key facts, differences, and impacts in {title}?",
        "theory": f"What are the core questions, answers, and cause-effect links in {title}?",
    }
    return templates.get(subject, templates["theory"])


def first_items(blocks: List[Dict], key: str, limit: int) -> List:
    out = []
    for block in blocks:
        value = block.get(key, [])
        if isinstance(value, list):
            out.extend(value)
        if len(out) >= limit:
            break
    return out[:limit]


def gather_teacher_quotes(blocks: List[Dict], limit: int = 4) -> List[str]:
    quotes = []
    for quote in first_items(blocks, "teacher_quotes", limit * 2):
        q = strip_markup(quote)
        if q:
            quotes.append(q)
        if len(quotes) >= limit:
            break
    return quotes


def gather_traps(blocks: List[Dict], limit: int = 5) -> List[str]:
    traps: List[str] = []
    for block in blocks:
        for trap in (block.get("traps") or []):
            t = strip_markup(trap)
            if t:
                traps.append(t)
        for ex in (block.get("examples") or []):
            note = strip_markup(ex.get("student_notes", ""))
            if note and any(word in note.lower() for word in ["careful", "mistake", "trick", "wrong", "confuse", "impossible"]):
                traps.append(note)
        if len(traps) >= limit:
            break
    # De-duplicate while preserving order
    deduped = []
    seen = set()
    for trap in traps:
        if trap not in seen:
            seen.add(trap)
            deduped.append(trap)
    return deduped[:limit]


def render_math(blocks: List[Dict]) -> List[str]:
    rows = ["| Formula / Concept | Shortcut / Trick | Solved Pattern |", "|---|---|---|"]
    for block in blocks[:4]:
        concepts = block.get("concepts") or []
        concept = strip_markup(concepts[0].get("term", block.get("title", ""))) if concepts else strip_markup(block.get("title", ""))
        definition = strip_markup(concepts[0].get("definition", "")) if concepts else ""
        examples = block.get("examples") or []
        example = examples[0] if examples else {}
        tricks = block.get("tricks") or []
        trick = strip_markup(tricks[0] if tricks else definition[:80])
        solved = shorten(example.get("cloze_text") or example.get("sentence") or example.get("working", ""), 110)
        rows.append(f"| {concept} | {shorten(trick or definition, 90)} | {solved} |")
    return rows


def render_reasoning(blocks: List[Dict]) -> List[str]:
    bullets = ["**Decision Map**", "- Identify the relation/pattern before solving.", "- Track direction/order first, then infer conclusions.", "- Recheck option traps before finalizing."]
    if blocks:
        examples = blocks[0].get("examples") or []
        example = examples[0] if examples else {}
        sentence = shorten(example.get("sentence", "") or example.get("working", ""), 140)
        if sentence:
            bullets.append(f"- Worked pattern: {sentence[:140]}")
    return bullets


def render_english(blocks: List[Dict]) -> List[str]:
    rows = ["| Rule | Correct / Key Form | Wrong / Confusion |", "|---|---|---|"]
    for block in blocks[:4]:
        rule = strip_markup(block.get("title", ""))
        examples = block.get("examples") or []
        correct = shorten(examples[0].get("sentence", "") if examples else block.get("explanation", ""), 90)
        traps = block.get("traps") or []
        wrong = strip_markup(traps[0] if traps else "Common case/confusion from lecture")
        rows.append(f"| {rule} | {correct} | {shorten(wrong, 90)} |")
    return rows


def render_gk(blocks: List[Dict]) -> List[str]:
    lines = ["**What -> Why -> Impact**"]
    for block in blocks[:4]:
        title = strip_markup(block.get("title", ""))
        explanation = shorten(block.get("explanation", ""), 120)
        lines.append(f"- **{title}** -> {explanation}")
    return lines


def render_technical(blocks: List[Dict]) -> List[str]:
    rows = ["| Concept | Why It Matters |", "|---|---|"]
    for block in blocks[:4]:
        title = strip_markup(block.get("title", ""))
        explanation = shorten(block.get("explanation", ""), 120)
        rows.append(f"| {title} | {explanation} |")
    if len(blocks) >= 2:
        chain = " -> ".join(strip_markup(b.get("title", "")) for b in blocks[:4])
        rows.extend(["", f"**Dependency Chain:** {chain}"])
    return rows


def render_theory(blocks: List[Dict]) -> List[str]:
    rows = ["| Question | Answer / Evidence |", "|---|---|"]
    for block in blocks[:4]:
        question = strip_markup(block.get("title", ""))
        answer = shorten(block.get("explanation", ""), 130)
        rows.append(f"| {question} | {answer} |")
    return rows


def build_short_note(lecture_title: str, blocks: List[Dict], transcript_path: str) -> str:
    subject = classify_subject(lecture_title, blocks)
    core_question = infer_core_question(lecture_title, subject)
    quotes = gather_teacher_quotes(blocks)
    traps = gather_traps(blocks)

    lines: List[str] = []
    lines.append(f'From **{strip_markup(lecture_title)}**, answering: "{core_question}"')
    lines.append("")
    lines.append(f"**Subject Type:** `{subject}`")
    lines.append("")

    if subject == "math":
        lines.extend(render_math(blocks))
    elif subject == "reasoning":
        lines.extend(render_reasoning(blocks))
    elif subject == "english":
        lines.extend(render_english(blocks))
    elif subject == "gk":
        lines.extend(render_gk(blocks))
    elif subject == "technical":
        lines.extend(render_technical(blocks))
    else:
        lines.extend(render_theory(blocks))

    if quotes:
        lines.extend(["", "**Memory Hook / Emphasis**"])
        for quote in quotes[:2]:
            lines.append(f"- *{shorten(quote, 160)}*")

    if traps:
        lines.extend(["", "**Trap Box**"])
        for trap in traps[:4]:
            lines.append(f"- {shorten(trap, 180)}")
        lines.append("- [Add your mock errors here]")

    self_test = core_question.replace("What are", "Explain").replace("What is", "Explain").rstrip("?") + "."
    lines.extend([
        "",
        f"**Self-Test:** {self_test}",
        "",
        f"_Source: {os.path.basename(transcript_path) if transcript_path else 'lecture artifacts'}, generated from concept map + transcript._",
    ])
    return "\n".join(lines).strip() + "\n"


def sanitize_short_note_markdown(text: str, lecture_title: str, transcript_path: str, has_traps: bool) -> str:
    text = text.replace("\r\n", "\n").strip()
    text = re.sub(r"[\u0900-\u097F]+", "", text)
    
    # Strip any hallucinated SRS boilerplate
    text = re.sub(r"_Review: 1/4/52.*?(?=\n\n|\Z)", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\[ \] Day 1 - Blurt & compress.*?(?=\n\n|\Z)", "", text, flags=re.DOTALL | re.IGNORECASE)
    
    if not text.strip():
        return build_short_note(lecture_title, [], transcript_path)
    if "From " not in text:
        anchor = f'From **{strip_markup(lecture_title)}**, answering: "What are the key revision points from this lecture?"'
        text = anchor + "\n\n" + text
    if has_traps and "Trap Box" not in text and "[Add your mock errors here]" not in text:
        text += "\n\n**Trap Box**\n- [Add your mock errors here]\n"
    if "Self-Test:" not in text:
        text += "\n**Self-Test:** Explain the core idea of this lecture from memory.\n"
    if "_Source:" not in text:
        source_name = os.path.basename(transcript_path) if transcript_path else "lecture artifacts"
        text += f"\n_Source: {source_name}, generated from concept map + transcript._\n"
    return text.strip() + "\n"


def build_llm_prompt(
    lecture_title: str,
    concept_map: Dict,
    slide_manifest,
    frame_manifest,
    transcript_text: str,
) -> str:
    skill_prompt = load_short_note_skill_prompt()
    transcript_excerpt = transcript_text[:60000]
    if len(transcript_text) > 60000:
        transcript_excerpt = transcript_excerpt.rsplit(" ", 1)[0] + "..."
    concept_summary = {
        "lecture_title": concept_map.get("lecture_title", lecture_title) if isinstance(concept_map, dict) else lecture_title,
        "blocks": summarize_blocks_for_llm(
            concept_map.get("blocks", []) if isinstance(concept_map, dict) else []
        ),
    }
    slide_summary = summarize_slide_manifest_for_llm(slide_manifest)
    frame_summary = summarize_frame_manifest_for_llm(frame_manifest)
    concept_json = json.dumps(concept_summary, ensure_ascii=False, indent=2)
    slide_json = json.dumps(slide_summary, ensure_ascii=False, indent=2)
    frame_json = json.dumps(frame_summary, ensure_ascii=False, indent=2)
    return f"""
You are generating a richer second-stage short revision note for the agentic lecture-notes pipeline.

Follow the skill instructions below exactly. The goal is a separate compact revision artifact grounded in the lecture, not a replacement for the detailed notes.

=== SKILL INSTRUCTIONS ===
{skill_prompt}
=== END SKILL INSTRUCTIONS ===

Produce only the final markdown note. Do not explain your process. Do not include analysis outside the note.

Hard constraints:
- WORD BUDGET: The entire short revision note must be extremely compact, targeting 300 to 500 words (strictly less than 600 words total). Focus strictly on high-yield equations, concepts, and steps, and write concisely without narrative fluff.
- Preserve source fidelity.
- No Devanagari script.
- No conversational attribution like 'the teacher says'.
- Use markdown tables/bullets compactly.
- Keep it crisp and revision-oriented.
- Include: context anchor, compact body, trap box, self-test, source line.
- STRICTLY PROHIBITED: Do not include ANY spaced repetition (SRS) boilerplate, Anki tags, Cornell cues, or review checklists (e.g., 'Review: 1/4/52', 'Day 1 - Blurt', etc.). The notes must be clean and self-contained.
- STRICTLY PROHIBITED: Do not include the answers to the Self-Test questions in the document. The Self-Test section must contain ONLY the active recall questions, and the answers must be completely omitted to allow self-testing.

Lecture title:
{lecture_title}

Concept map JSON:
```json
{concept_json}
```

Slide manifest JSON:
```json
{slide_json}
```

Frame manifest JSON:
```json
{frame_json}
```

Transcript excerpt:
```text
{transcript_excerpt}
```
""".strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concept-map", required=True)
    parser.add_argument("--transcript", default="lecture-input/transcript.srt")
    parser.add_argument("--slide-manifest", default="slide_manifest.json")
    parser.add_argument("--frame-manifest", default="frame_manifest.json")
    parser.add_argument("--mode", choices=["auto", "llm", "heuristic"], default="auto")
    parser.add_argument("--output")
    args = parser.parse_args()

    lecture_title, blocks = load_concept_map(args.concept_map)
    concept_map_raw = load_json_if_exists(args.concept_map)
    slide_manifest = load_json_if_exists(args.slide_manifest)
    frame_manifest = load_json_if_exists(args.frame_manifest)
    transcript_text = load_text_if_exists(args.transcript)
    output_path = args.output or os.path.join("notes-output", f"{slugify(lecture_title)}_SHORTNOTE.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    content = ""
    llm_error = None
    if args.mode in {"auto", "llm"}:
        try:
            prompt = build_llm_prompt(
                lecture_title=lecture_title,
                concept_map=concept_map_raw or {"lecture_title": lecture_title, "blocks": blocks},
                slide_manifest=slide_manifest,
                frame_manifest=frame_manifest,
                transcript_text=transcript_text,
            )
            content = call_antigravity_markdown(prompt)
            content = sanitize_short_note_markdown(content, lecture_title, args.transcript, bool(traps))
        except Exception as exc:
            llm_error = exc
            if args.mode == "llm":
                raise

    if not content:
        content = build_short_note(lecture_title, blocks, args.transcript)
        if llm_error:
            content = (
                "<!-- LLM short-note generation failed; fallback formatter used. "
                f"{type(llm_error).__name__}: {str(llm_error).replace('--', '-')}"
                " -->\n" + content
            )

    # Ensure no Devanagari characters are written to the short note
    import re as regex_fallback
    if regex_fallback.search(r'[\u0900-\u097F]', content):
        content = regex_fallback.sub(r'[\u0900-\u097F]', '', content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(output_path)


if __name__ == "__main__":
    main()

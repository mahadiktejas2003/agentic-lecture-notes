import re

with open('/Users/tejasmahadik/Documents/agentic-lecture-notes/lecture-input/transcript.srt', 'r', encoding='utf-8') as f:
    content = f.read()

# We want to find blocks of SRT
blocks = content.strip().split('\n\n')

questions = []
for block in blocks:
    lines = block.split('\n')
    if len(lines) >= 3:
        num = lines[0]
        time_range = lines[1]
        text = ' '.join(lines[2:])
        # If there is a substantial amount of English text in quotes or representing sentences, let's capture it.
        # Often sentences are written in English (like "goes to the church", "Measles is", "twenty million degrees", etc.)
        english_phrases = re.findall(r'[A-Za-z\s\'\-\,\.\?\:\!\"]{10,}', text)
        if english_phrases:
            for phrase in english_phrases:
                phrase = phrase.strip()
                if len(phrase) > 15 and not phrase.startswith('Good evening') and not phrase.startswith('Recording in progress'):
                    questions.append((time_range, phrase))

# Print unique/interesting ones
seen = set()
for time, q in questions:
    if q.lower() not in seen:
        print(f"[{time}] {q}")
        seen.add(q.lower())

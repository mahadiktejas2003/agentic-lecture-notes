import json
import re

def main():
    path = "notes-output/LECTURE_NOTES_Lec-14_Error_Control_in_Data_Link_Layer_2026-07-07_17-58-56_concept_map.json"
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for block in data.get('blocks', []):
        # Shorten explanation to first 3 sentences/lines
        expl = block.get('explanation', '')
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n', expl) if s.strip()]
        if len(sentences) > 4:
            block['explanation'] = " ".join(sentences[:4])
            
        # Also shorten example workings
        for ex in block.get('examples', []):
            working = ex.get('working', '')
            ex_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n', working) if s.strip()]
            if len(ex_sentences) > 3:
                ex['working'] = " ".join(ex_sentences[:3])
                
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print("Minified Lec-14 concept map successfully.")

if __name__ == "__main__":
    main()

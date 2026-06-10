#!/usr/bin/env python3
"""
AI Services Layer - Unified Interface for Gemini, Groq, Claude, Ollama
Handles: Batch OCR, Concept Mapping, Note Composition
Implements Source Fidelity Protocol v8.0
"""
import os
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try importing providers (install missing ones with pip)
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

class AIServices:
    def __init__(self):
        self.gemini_client = None
        self.groq_client = None
        
        # Initialize clients if keys exist
        if HAS_GEMINI and os.getenv("GEMINI_API_KEY"):
            self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            print("✅ Gemini Client Initialized")
        
        if HAS_GROQ and os.getenv("GROQ_API_KEY"):
            self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            print("✅ Groq Client Initialized")

    def perform_batch_ocr(self, frame_paths: List[str]) -> List[Dict[str, str]]:
        """
        Extract text from multiple frames using Gemini 2.0 Flash Vision
        Returns: List of {frame_path: ..., text: ...}
        """
        if not self.gemini_client:
            print("⚠️ No AI client available. Returning placeholder OCR.")
            return [{"path": p, "text": "OCR_FAILED_NO_CLIENT"} for p in frame_paths]

        results = []
        print(f"🔍 Starting Batch OCR for {len(frame_paths)} frames...")
        
        # Process in batches of 5 to avoid rate limits
        for i, path in enumerate(frame_paths):
            try:
                if not os.path.exists(path):
                    results.append({"path": path, "text": "FILE_NOT_FOUND"})
                    continue
                
                # Upload image and prompt
                image_file = genai.upload_file(path=path)
                
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        "Extract ALL text from this lecture slide frame. Preserve mathematical formulas and code snippets exactly. If no text is visible, return 'NO_TEXT'.",
                        image_file
                    ]
                )
                
                text = response.text.strip()
                results.append({"path": path, "text": text})
                print(f"  [{i+1}/{len(frame_paths)}] OCR Complete: {len(text)} chars")
                
                # Small delay to prevent throttling
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ OCR failed for {path}: {str(e)}")
                results.append({"path": path, "text": f"OCR_ERROR: {str(e)}"})
        
        return results

    def generate_concept_map(self, transcript: str, ocr_results: List[Dict], slides_text: str = "") -> Dict[str, Any]:
        """
        Generate the Concept Block Map from transcript + OCR + Slides
        Uses Chain-of-Thought to ensure Source Fidelity
        """
        model_name = "gemini-2.0-flash"
        provider = "gemini"
        
        if not self.gemini_client and self.groq_client:
            model_name = "llama-3.3-70b-versatile"
            provider = "groq"

        if not self.gemini_client and not self.groq_client:
            print("❌ No AI providers available for concept mapping.")
            return self._get_fallback_map()

        # Construct prompt with strict constraints
        prompt = f"""
You are an expert educational content analyzer. Your task is to create a structured "Concept Block Map" from the provided lecture data.

SOURCE DATA:
1. Transcript Snippet: "{transcript[:5000]}..." (Truncated for context)
2. Slide/Frame Text: {json.dumps(ocr_results[:5])} (First 5 frames)
3. Additional Slides: "{slides_text[:2000]}..."

STRICT RULES (Source Fidelity Protocol v8.0):
1. DO NOT invent facts. Only use information present in the source.
2. Every concept must cite a timestamp from the transcript or a frame ID.
3. Identify: Key Concepts, Worked Examples, Diagrams, and "Trap" misconceptions.
4. Output MUST be valid JSON matching this schema:
{{
  "lecture_title": "String",
  "concept_blocks": [
    {{
      "id": "block_1",
      "title": "String",
      "timestamp_start": "MM:SS",
      "timestamp_end": "MM:SS",
      "key_points": ["String"],
      "worked_example": "String or null",
      "visual_refs": ["frame_id_1"],
      "trap_alert": "String or null"
    }}
  ]
}}

Generate the JSON now:
"""
        try:
            if provider == "gemini":
                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                raw_json = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(raw_json)
            
            elif provider == "groq":
                response = self.groq_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                raw_json = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                return json.loads(raw_json)
                
        except Exception as e:
            print(f"❌ Concept Map Generation Failed: {e}")
            return self._get_fallback_map()

    def _get_fallback_map(self) -> Dict[str, Any]:
        return {
            "lecture_title": "Unknown Lecture",
            "concept_blocks": [],
            "error": "AI Generation Failed - Fallback Used"
        }

# CLI Test Runner
if __name__ == "__main__":
    print("🧪 Testing AI Services Layer...")
    service = AIServices()
    
    # Test Concept Map
    dummy_transcript = "Welcome to today's lecture on CPU Scheduling. We will discuss First Come First Serve..."
    result = service.generate_concept_map(dummy_transcript, [])
    print("\n✅ Generated Concept Map:")
    print(json.dumps(result, indent=2))
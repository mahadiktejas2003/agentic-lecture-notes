#!/usr/bin/env python3
"""
AI Services Module - Unified interface for multiple AI providers
Supports: Gemini 2.0 Flash, Groq (Mixtral/Llama), Claude Opus, Ollama (local fallback)
"""

import os
import json
import base64
from typing import List, Dict, Optional, Any
from pathlib import Path

class AIServices:
    """Unified AI service router with fallback chain"""
    
    def __init__(self):
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.preferred_provider = os.getenv('AI_PROVIDER', 'gemini')
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for VLM APIs"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def batch_ocr_with_gemini(self, image_paths: List[str], max_batch_size: int = 10) -> List[Dict[str, str]]:
        """
        Batch OCR using Gemini 2.0 Flash Vision
        Returns list of {image_path: str, ocr_text: str}
        """
        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_key)
            
            results = []
            # Process in batches to avoid rate limits
            for i in range(0, len(image_paths), max_batch_size):
                batch = image_paths[i:i+max_batch_size]
                
                for img_path in batch:
                    try:
                        # Upload image and extract text
                        image_data = self.encode_image_to_base64(img_path)
                        
                        response = client.models.generate_content(
                            model='gemini-2.0-flash',
                            contents=[
                                "Extract ALL text from this lecture slide/frame. Preserve mathematical formulas, code snippets, and special characters exactly as shown. Return ONLY the extracted text, no commentary.",
                                {'mime_type': 'image/jpeg', 'data': image_data}
                            ]
                        )
                        
                        results.append({
                            'image_path': img_path,
                            'ocr_text': response.text.strip(),
                            'provider': 'gemini-2.0-flash'
                        })
                        
                    except Exception as e:
                        print(f"⚠️ Gemini OCR failed for {img_path}: {e}")
                        results.append({
                            'image_path': img_path,
                            'ocr_text': '[OCR FAILED]',
                            'provider': 'gemini-2.0-flash',
                            'error': str(e)
                        })
            
            return results
            
        except ImportError:
            print("⚠️ google-genai not installed. Install with: pip install google-genai")
            return [{'image_path': p, 'ocr_text': '[GOOGLE_GENAI NOT INSTALLED]', 'provider': 'none'} for p in image_paths]
    
    def generate_concept_map(self, transcript_text: str, ocr_results: List[Dict], slides_text: str = "") -> Dict:
        """
        Generate concept block map using LLM (Gemini/Groq/Claude)
        Follows Source Fidelity Protocol v8.0
        """
        
        prompt = f"""
You are an expert educational content analyst. Generate a concept block map from the following lecture materials.

STRICT RULES (Source Fidelity Protocol v8.0):
1. Extract concepts ONLY from provided sources (transcript, OCR, slides)
2. NEVER invent facts, examples, or numbers not present in sources
3. Every concept must have direct source citations (timestamp or slide number)
4. Preserve exact mathematical formulas and code snippets
5. Mark uncertain interpretations with "confidence": 0.8 or lower

INPUT DATA:
--- TRANSCRIPT EXCERPT ---
{transcript_text[:50000]}  # Limit to 50k chars

--- SLIDE TEXT (OCR) ---
{slides_text[:20000]} if slides_text else "No slides provided"

--- FRAME OCR SAMPLES ---
{json.dumps(ocr_results[:10])}  # First 10 frames as samples

OUTPUT FORMAT (JSON):
{{
    "lecture_title": "Exact title from sources",
    "concept_blocks": [
        {{
            "id": 1,
            "title": "Concept name",
            "start_timestamp": "00:02:15",
            "end_timestamp": "00:05:30",
            "key_points": ["Point 1", "Point 2"],
            "worked_examples": [{{"problem": "...", "solution": "..."}}],
            "visual_references": ["frame_001.jpg", "slide_03.png"],
            "source_citations": ["transcript:00:02:15", "slide:3"],
            "confidence": 0.95
        }}
    ],
    "tricky_concepts": ["List of concepts students often misunderstand"],
    "total_duration": "01:23:45"
}}

Generate the concept map now:
"""
        
        # Try providers in order: Gemini → Groq → Claude → Ollama
        providers = []
        
        if self.gemini_key:
            providers.append(('gemini', self._call_gemini(prompt)))
        
        if self.groq_key:
            providers.append(('groq', self._call_groq(prompt)))
        
        if self.anthropic_key:
            providers.append(('claude', self._call_claude(prompt)))
        
        # Fallback to Ollama (local)
        providers.append(('ollama', self._call_ollama(prompt)))
        
        for provider_name, result in providers:
            if result:
                try:
                    concept_map = json.loads(result)
                    concept_map['_generated_by'] = provider_name
                    return concept_map
                except json.JSONDecodeError as e:
                    print(f"⚠️ {provider_name} returned invalid JSON: {e}")
                    continue
        
        raise RuntimeError("All AI providers failed to generate valid concept map")
    
    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Gemini API"""
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_key)
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"⚠️ Gemini call failed: {e}")
            return None
    
    def _call_groq(self, prompt: str) -> Optional[str]:
        """Call Groq API (Mixtral/Llama3)"""
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Groq call failed: {e}")
            return None
    
    def _call_claude(self, prompt: str) -> Optional[str]:
        """Call Claude API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"⚠️ Claude call failed: {e}")
            return None
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call local Ollama (fallback)"""
        try:
            import requests
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.1',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=120
            )
            return response.json().get('response', '')
        except Exception as e:
            print(f"⚠️ Ollama call failed: {e}")
            return None


# Convenience function for batch OCR
def process_frames_with_ai(frame_paths: List[str]) -> List[Dict[str, str]]:
    """Process multiple frame images with AI OCR"""
    ai = AIServices()
    return ai.batch_ocr_with_gemini(frame_paths)


if __name__ == "__main__":
    # Test the AI services
    print("🧪 Testing AI Services...")
    ai = AIServices()
    
    if ai.gemini_key:
        print("✅ Gemini API key found")
    else:
        print("❌ Gemini API key missing")
    
    if ai.groq_key:
        print("✅ Groq API key found")
    else:
        print("❌ Groq API key missing")
    
    print("\nSet GEMINI_API_KEY, GROQ_API_KEY, ANTHROPIC_API_KEY in .env to enable AI features")

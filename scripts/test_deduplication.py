#!/usr/bin/env python3
import re
import unittest
import imagehash

def are_ocr_texts_similar(text1, text2, threshold=0.85):
    if not text1 or not text2:
        return False
    # Extract unique words with length >= 2 including numbers and variables
    w1 = set(re.findall(r'\b[a-zA-Z0-9_\-\+]{2,}\b', text1.lower()))
    w2 = set(re.findall(r'\b[a-zA-Z0-9_\-\+]{2,}\b', text2.lower()))
    
    if not w1 or not w2:
        return False
        
    common = w1 & w2
    ratio = len(common) / max(len(w1), len(w2))
    return ratio > threshold

def simulate_duplicate_check(prev_hash, prev_ocr, current_hash, current_ocr):
    is_duplicate = False
    
    # 1. Visual check
    if prev_hash is not None and current_hash is not None:
        if current_hash - prev_hash <= 2:
            is_duplicate = True
            return "Visual duplicate (hash diff <= 2)"
            
    # 2. OCR check
    if current_ocr.strip() and prev_ocr.strip():
        if are_ocr_texts_similar(current_ocr, prev_ocr, threshold=0.85):
            is_duplicate = True
            return "Textual duplicate (OCR similarity > 0.85)"
            
    return "Not duplicate"

class TestDeduplicationRobustness(unittest.TestCase):
    def test_permutations_vs_combinations_single_digit(self):
        text1 = "We need to select 3 distinct items out of 5 available: 5C3 = 2"
        text2 = "We need to select 3 distinct items out of 5 available: 5P3 = 6"
        
        w1 = set(re.findall(r'\b[a-zA-Z0-9_\-\+]{2,}\b', text1.lower()))
        w2 = set(re.findall(r'\b[a-zA-Z0-9_\-\+]{2,}\b', text2.lower()))
        
        print("\n--- Test Permutations vs Combinations (Single Digit Result) ---")
        print("w1:", w1)
        print("w2:", w2)
        
        similar = are_ocr_texts_similar(text1, text2)
        print(f"Are they classified as duplicates? {similar}")
        
        self.assertTrue(similar)

    def test_equations_differing_by_one_character(self):
        text1 = "Solve the following equation: x + y = 5"
        text2 = "Solve the following equation: x + y = 6"
        
        w1 = set(re.findall(r'\b[a-zA-Z0-9_\-\+]{2,}\b', text1.lower()))
        w2 = set(re.findall(r'\b[a-zA-Z0-9_\-\+]{2,}\b', text2.lower()))
        
        print("\n--- Test Equations Differing by One Character ---")
        print("w1:", w1)
        print("w2:", w2)
        
        similar = are_ocr_texts_similar(text1, text2)
        print(f"Are they classified as duplicates? {similar}")
        
        self.assertTrue(similar)

    def test_circular_permutations(self):
        text1 = "Permutation Example: Number of ways to arrange A, B, C: 3! = 6"
        text2 = "Permutation Example: Number of ways to arrange A, B, C: (3-1)! = 2"
        
        w1 = set(re.findall(r'\b[a-zA-Z0-9_\-\+]{2,}\b', text1.lower()))
        w2 = set(re.findall(r'\b[a-zA-Z0-9_\-\+]{2,}\b', text2.lower()))
        
        print("\n--- Test Circular Permutations ---")
        print("w1:", w1)
        print("w2:", w2)
        
        similar = are_ocr_texts_similar(text1, text2)
        print(f"Are they classified as duplicates? {similar}")
        
        self.assertTrue(similar)

    def test_matrix_operations(self):
        text1 = "Let Matrix A be: [[1, 2], [3, 4]]. We compute the determinant: det(A) = 1*4 - 2*3"
        text2 = "Let Matrix A be: [[1, 2], [3, 4]]. We compute the determinant: det(A) = 4 - 6"
        text3 = "Let Matrix A be: [[1, 2], [3, 4]]. We compute the determinant: det(A) = -2"
        
        similar_1_2 = are_ocr_texts_similar(text1, text2)
        similar_2_3 = are_ocr_texts_similar(text2, text3)
        
        print("\n--- Test Matrix Operations ---")
        print(f"Is step 2 a duplicate of step 1? {similar_1_2}")
        print(f"Is step 3 a duplicate of step 2? {similar_2_3}")
        
        self.assertTrue(similar_1_2)
        self.assertTrue(similar_2_3)

    def test_solved_state_bypass_failure(self):
        # State 1 (Intermediate math): Det(A) = 1*4 - 2*3
        # State 2 (Solved whiteboard state): Det(A) = -2
        # Mocking dhash:
        # Since State 2 has less text/drawings than State 1, the dhashes are visually different.
        # Let's say State 1 hash is hex "ffff00000000ffff"
        # Let's say State 2 hash is hex "ffff0000000f0fff" (Hamming distance = 5)
        # So visually they are NOT duplicates (since 5 > 2).
        h1 = imagehash.hex_to_hash("ffff00000000ffff")
        h2 = imagehash.hex_to_hash("ffff0000000f0fff")
        
        ocr1 = "Let Matrix A be: [[1, 2], [3, 4]]. We compute the determinant: det(A) = 1*4 - 2*3"
        ocr2 = "Let Matrix A be: [[1, 2], [3, 4]]. We compute the determinant: det(A) = -2"
        
        result = simulate_duplicate_check(h1, ocr1, h2, ocr2)
        print("\n--- Test Solved State Bypass Failure ---")
        print(f"Hash difference: {h2 - h1}")
        print(f"Duplicate check result: {result}")
        
        # The expected behavior is that they are not duplicate, because the solved state Det(A) = -2 is crucial!
        # But the actual behavior is that it is classified as a textual duplicate!
        self.assertEqual(result, "Textual duplicate (OCR similarity > 0.85)")

if __name__ == "__main__":
    unittest.main()

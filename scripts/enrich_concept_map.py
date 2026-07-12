#!/usr/bin/env python3
import json
import sys
import os

def enrich_transmission_media(data):
    print("Enriching CN Transmission Media concept map with deep concepts...")
    
    # Locate CB2 (Twisted Pair & Coaxial Cable)
    cb2 = None
    for block in data.get("blocks", []):
        if block.get("block_id") == "CB2" or "Twisted Pair" in block.get("title", ""):
            cb2 = block
            break
            
    if cb2:
        print("Found Twisted Pair & Coaxial block. Injecting details...")
        
        # 1. Update RJ45 Connector definition
        rj45 = next((c for c in cb2.get("concepts", []) if "RJ45" in c.get("term", "")), None)
        if rj45:
            rj45["definition"] = "Registered Jack 45; an **8-pin connector** featuring 8-pin male/female jacks arranged in 4 twisted pairs. It is the standard physical connector for twisted-pair Ethernet cables."
        else:
            cb2["concepts"].append({
                "term": "RJ45 Connector",
                "definition": "Registered Jack 45; featuring **8-pin male/female jacks** (8 pins total) arranged in twisted pairs to connect devices to twisted-pair cabling."
            })
            
        # 2. Update BNC Connector definition
        bnc = next((c for c in cb2.get("concepts", []) if "BNC" in c.get("term", "")), None)
        if bnc:
            bnc["definition"] = "Bayonet Neill–Concelman connector; named after the Bayonet locking mechanism, Paul Neill, and Carl Concelman. Used to terminate coaxial cables for radio frequency and Thin Ethernet applications."
        else:
            cb2["concepts"].append({
                "term": "BNC Connector",
                "definition": "Bayonet Neill–Concelman connector (Paul Neill and Carl Concelman); used for connecting coaxial cables to network interfaces."
            })
            
        # 3. Add Thin Ethernet vs Thick Ethernet concepts
        has_thin = any("Thin Ethernet" in c.get("term", "") for c in cb2.get("concepts", []))
        if not has_thin:
            cb2["concepts"].append({
                "term": "Thin Ethernet (10BASE2)",
                "definition": "A standard utilizing thin coaxial cable (~0.25 inch diameter) with a maximum segment length of **185 meters**. It is flexible, inexpensive, and easy to deploy using BNC connectors."
            })
            cb2["concepts"].append({
                "term": "Thick Ethernet (10BASE5)",
                "definition": "A standard utilizing thick, rigid coaxial cable (~0.5 inch diameter) with a maximum segment length of **500 meters**. Stiffer and harder to install, it serves as a robust backbone with high noise immunity."
            })
            
        # 4. Update Coaxial explanation with conductors and insulators
        coax_exp = next((e for e in cb2.get("concept_explanations", []) if "Coaxial" in e.get("concept_name", "")), None)
        coax_detail = ("Coaxial cable features a central inner core conductor surrounded by multiple layers of insulating materials (dielectric insulation and outer shielding mesh/foil) to reduce noise. "
                       "It offers higher bandwidth than Unshielded Twisted Pair (UTP) and experiences lesser attenuation and reduced noise. "
                       "However, due to signal decay over long runs, it still requires Repeaters to periodically regenerate and boost signal energy.")
        if coax_exp:
            coax_exp["detailed_explanation"] = coax_detail
        else:
            cb2["concept_explanations"].append({
                "concept_name": "Coaxial Cable Conductor and Attenuation",
                "detailed_explanation": coax_detail
            })
            
        # 5. Add Thin vs Thick Ethernet detailed explanation
        has_eth_exp = any("Thin Ethernet" in e.get("concept_name", "") for e in cb2.get("concept_explanations", []))
        if not has_eth_exp:
            cb2["concept_explanations"].append({
                "concept_name": "Thin Ethernet vs. Thick Ethernet (10BASE2 vs. 10BASE5)",
                "detailed_explanation": ("Thin Ethernet (10BASE2) uses flexible thin coaxial cable with BNC connectors, maxing out at 185m segment lengths. "
                                         "Thick Ethernet (10BASE5) uses rigid thick coaxial cable (approx 0.5 inches diameter) with transceiver taps, maxing out at 500m segments. "
                                         "Thick Ethernet is harder to bend and install but provides superior range and noise shielding, making it ideal as a backbone cable.")
            })
            
    # Locate CB3 (Optical Fiber)
    cb3 = None
    for block in data.get("blocks", []):
        if block.get("block_id") == "CB3" or "Fiber" in block.get("title", ""):
            cb3 = block
            break
            
    if cb3:
        print("Found Optical Fiber block. Injected details...")
        
        # 1. Add Propagation Modes
        has_mode = any("Propagation Mode" in c.get("term", "") for c in cb3.get("concepts", []))
        if not has_mode:
            cb3["concepts"].append({
                "term": "Propagation Mode",
                "definition": "The physical path or number of light beams/signals propagating inside the optical fiber channel."
            })
            cb3["concepts"].append({
                "term": "Graded-Index Distortion Advantage",
                "definition": "In Graded-Index multi-mode fiber, density varies gradually from center to cladding, bending light rays in smooth curves. All rays arrive at the receiver simultaneously, resulting in the **least distortion**."
            })
            cb3["concepts"].append({
                "term": "Core-Cladding Density Principle",
                "definition": "Total Internal Reflection requires Core optical density ($n_1$) to be higher than Cladding optical density ($n_2$). The critical angle is $\\theta_c = \\sin^{-1}(n_2 / n_1)$."
            })
            
        # 2. Add detailed concept explanations on density variations and modes
        cb3["concept_explanations"].append({
            "concept_name": "Propagation Modes in Optical Fiber",
            "detailed_explanation": ("Propagation mode refers to the physical paths or beams of light/signal travelling inside the channel. "
                                     "Single-Mode propagates a single ray along a direct axial path, requiring a very narrow core. "
                                     "Multi-Mode propagates multiple rays concurrently. Graded-Index multi-mode fiber features variable core density "
                                     "(highest at the center) that refracts light in smooth curves, resulting in the least signal distortion.")
        })
        cb3["concept_explanations"].append({
            "concept_name": "Core-Cladding Optical Density & Critical Angle",
            "detailed_explanation": ("For light to propagate inside the fiber core, the Core must have a higher optical density (higher refractive index n1) "
                                     "than the Cladding (lower refractive index n2). When light travels from the denser Core toward the less dense Cladding, "
                                     "if the angle of incidence exceeds the critical angle (θc = arcsin(n2/n1)), the light suffers Total Internal Reflection "
                                     "and bounces back inside the core.")
        })
        cb3["concept_explanations"].append({
            "concept_name": "Density Variation: Step-Index vs. Graded-Index",
            "detailed_explanation": ("In Step-Index multi-mode fiber, core density is uniform throughout (constant n1), dropping abruptly at the core-cladding boundary. "
                                     "Rays strike boundaries at sharp angles (zig-zag). Outer rays travel longer paths and arrive later than axial rays, causing high modal dispersion (distortion). "
                                     "In Graded-Index multi-mode fiber, core density is highest at the center and decreases gradually outward. "
                                     "Since velocity is inversely proportional to density (v = c/n), rays moving away from the center speed up, compensating for their longer curved physical paths. "
                                     "Consequently, all rays arrive at the receiver at the same time, making distortion minimal.")
        })
        
        # 3. Add Solved Exam Question / Example for Density Variation
        cb3["examples"].append({
            "timestamp": "00:11:00",
            "sentence": "Analyze how density variations in step-index and graded-index fibers affect signal distortion and transmission speed.",
            "rule": "Velocity is inversely proportional to refractive density ($v = c/n$). Continuous index grading bends light curves and compensates for physical path length differences.",
            "working": "1. Step-Index: Constant density ($n_1$). Rays at angle $\\theta$ travel longer paths than axial rays. Distortion = $\\Delta t = \\frac{L}{c}(n_1 - n_2)$.\n2. Graded-Index: Varying density $n(r) = n_1 \\sqrt{1 - 2\\Delta(r/a)^2}$. Rays traveling far from center bend through lower density (faster speed), compensating for the longer path.\n3. Result: Arrival times synchronize, making distortion minimal in Graded-Index.",
            "student_notes": "Total Internal Reflection requires: 1. Core density > Cladding density ($n_1 > n_2$). 2. Angle of incidence > Critical angle."
        })

    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: enrich_concept_map.py <concept_map_path>")
        sys.exit(1)
        
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    title = data.get("lecture_title", "")
    if "cn" in title.lower() and ("transmission" in title.lower() or "media" in title.lower()):
        data = enrich_transmission_media(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Successfully enriched concept block map!")
    else:
        print("Skipping enrichment: not the Transmission Media lecture.")

if __name__ == "__main__":
    main()

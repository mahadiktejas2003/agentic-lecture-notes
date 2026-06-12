#!/usr/bin/env python3
import os
import sys
import json
import re

def retrieve_runs(query_type="all", limit=5):
    memory_dir = "agent_memory"
    if not os.path.exists(memory_dir):
        print("No agent memory found.")
        return []
        
    records = []
    for f in sorted(os.listdir(memory_dir)):
        if f.startswith("run_") and f.endswith(".json"):
            path = os.path.join(memory_dir, f)
            with open(path, "r", encoding="utf-8") as file:
                records.append(json.load(file))
                
    # Sort by timestamp descending
    records = sorted(records, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    results = []
    if query_type == "last_runs" or query_type == "all":
        results = records[:limit]
    elif query_type.startswith("failed_gate_"):
        try:
            gate_num = int(query_type.split("_")[-1])
            for r in records:
                failed = r.get("failed_gates", [])
                for fg in failed:
                    digits = re.findall(r'\d+', fg)
                    if digits and int(digits[0]) == gate_num:
                        results.append(r)
                        break
        except ValueError:
            print(f"Invalid gate query: {query_type}")
    else:
        results = records[:limit]
        
    print(f"Query '{query_type}' returned {len(results)} matches:")
    for idx, r in enumerate(results):
        print(f"Match {idx+1}: Timestamp={r['timestamp']}, Status={r['status']}, Score={r['audit_score']}, Failed={r['failed_gates']}, Path={r['notes_path']}")
        
    return results

if __name__ == "__main__":
    q_type = sys.argv[1] if len(sys.argv) > 1 else "last_runs"
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    retrieve_runs(q_type, lim)

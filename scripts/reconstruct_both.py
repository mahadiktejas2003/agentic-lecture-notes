#!/usr/bin/env python3
import os
import sys
import json
import shutil
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DOWNLOADS_DIR = os.environ.get("DOWNLOADS_DIR", os.path.expanduser("~/Downloads"))
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_DIR = os.path.join(WORKSPACE_DIR, "lecture-input")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "notes-output")

# Profiles
SYLLABUS_PROFILE = {
    "lecture_type": "Syllabus/Intro",
    "notes_style": "Compact",
    "recommended_blocks": 3,
    "recommended_frames": 2,
    "generate_worked_examples": False,
    "generate_theoretical_theory": False,
    "visual_appendix_limit": 2,
    "focus_areas": ["Syllabus Outline", "Exam Weightage", "Preparation Strategy"],
    "explanation_limit": 400
}

# DBMS Syllabus Data
DBMS_TRANSCRIPT = os.path.join(DOWNLOADS_DIR, "DBMS Syllabus IBPS SO 2025 transcript.srt")
DBMS_VIDEO = os.path.join(DOWNLOADS_DIR, "DBMS Syllabus IBPS SO 2025.mp4")
DBMS_MAP = [
  {
    "block_id": "CB1",
    "lecture_title": "DBMS Syllabus for IBPS SO IT Officer 2025",
    "title": "DBMS Exam Weightage and Core Architecture",
    "transcript_range_percent": [0, 50],
    "explanation": "Introduces the overall exam weightage of DBMS in the IBPS SO IT Officer mains, where it constitutes 15-20 marks out of 60. Detailed syllabus topics are outlined, including Three Schema Architecture and the Relational Model.",
    "concepts": [
      {
        "term": "Exam Weightage",
        "definition": "Constitute 15-20 marks out of 60, making it single-handedly enough to clear the cut-off."
      },
      {
        "term": "Three Schema Architecture",
        "definition": "Standard database structure divided into view level (external), logical level, and physical/internal schema."
      },
      {
        "term": "Relational Model",
        "definition": "A model based on tables, tuples, cardinality, and arity."
      }
    ],
    "examples": [
      {
        "sentence": "How much weightage does DBMS have in the IBPS SO Mains exam?",
        "rule": "DBMS accounts for 15-20 marks out of 60.",
        "working": "Average mains cutoff is 13-14 marks. DBMS alone contributes 15-20 marks, making it the most critical subject -> 15-20 marks"
      }
    ],
    "exercise_questions": [
      "List the three levels of the Three Schema Architecture.",
      "Explain the difference between arity and cardinality in a table."
    ],
    "visual_moments": [
      {"timestamp": "00:00:10", "type": "board", "description": "DBMS Syllabus Intro and weightage details"},
      {"timestamp": "00:01:12", "type": "board", "description": "Three Schema Architecture and Relational Model definitions"},
      {"timestamp": "00:01:45", "type": "board", "description": "Relational Algebra and Joins overview"},
      {"timestamp": "00:02:22", "type": "board", "description": "ER Model and Keys details"}
    ],
    "teacher_quotes": [
      "तेरह-चौदह number का तो अकेला DBMS ही आपको मिल जाएगा exam में।"
    ],
    "traps": [
      "Do not miss basic database terminology like arity and cardinality, as direct questions are frequently asked."
    ],
    "tricks": [
      "Priority: Focus on breadth across all topics rather than deep query writing."
    ]
  },
  {
    "block_id": "CB2",
    "title": "Advanced DBMS Topics and PL/SQL",
    "transcript_range_percent": [50, 100],
    "explanation": "Covers SQL commands (DDL, DML, DCL, TCL), aggregate functions, ACID properties, transaction controls, indexing, PL/SQL procedural features (triggers, cursors, stored procedures), RAID levels, and Big Data basics.",
    "concepts": [
      {
        "term": "SQL Commands",
        "definition": "DDL (data definition), DML (data manipulation), DCL (data control), and TCL (transaction control)."
      },
      {
        "term": "ACID Properties",
        "definition": "Atomicity, Consistency, Isolation, and Durability - properties that guarantee reliable transaction processing."
      },
      {
        "term": "PL/SQL",
        "definition": "Procedural extensions to SQL including triggers, cursors, and stored procedures."
      },
      {
        "term": "RAID Levels",
        "definition": "Redundant Array of Independent Disks used for data redundancy and performance tuning."
      },
      {
        "term": "CAP Theorem",
        "definition": "Consistency, Availability, and Partition Tolerance - only two can be guaranteed simultaneously in a distributed system."
      }
    ],
    "examples": [],
    "exercise_questions": [
      "Explain the difference between DDL and DML commands.",
      "List the RAID levels commonly discussed in DBMS databases."
    ],
    "visual_moments": [
      {"timestamp": "00:03:43", "type": "board", "description": "SQL Commands and aggregate functions details"},
      {"timestamp": "00:04:22", "type": "board", "description": "ACID properties and transaction control concepts"},
      {"timestamp": "00:04:33", "type": "board", "description": "Indexing types and B/B+ trees"},
      {"timestamp": "00:04:44", "type": "board", "description": "PL/SQL triggers, cursors, and stored procedures"},
      {"timestamp": "00:05:15", "type": "board", "description": "RAID levels and NoSQL/Big Data basics"},
      {"timestamp": "00:05:30", "type": "board", "description": "BASE and CAP properties for Big Data databases"}
    ],
    "teacher_quotes": [
      "BASE properties क्या हैं? CAP properties क्या हैं? वो आपको जो है वो basic note कर सकते हो।"
    ],
    "traps": [
      "Do not confuse DDL and DML commands; ALTER is DDL while UPDATE is DML."
    ],
    "tricks": [
      "Remember the CAP theorem options: you can only choose CP, AP, or CA."
    ]
  }
]
DBMS_FRAMES = {
  "frame_001.png": {
    "timestamp": "00:00:10",
    "ocr_text": "DBMS Syllabus for IT Officer Mains Weightage 15-20 Marks",
    "type": "board"
  },
  "frame_002.png": {
    "timestamp": "00:01:12",
    "ocr_text": "Three Schema Architecture Internal Conceptual View Relational Model",
    "type": "board"
  },
  "frame_003.png": {
    "timestamp": "00:01:45",
    "ocr_text": "Relational Algebra Joins Union Intersection Minus",
    "type": "board"
  },
  "frame_004.png": {
    "timestamp": "00:02:22",
    "ocr_text": "ER Model Attributes Keys Primary Candidate Super Foreign Alternate",
    "type": "board"
  },
  "frame_005.png": {
    "timestamp": "00:03:43",
    "ocr_text": "SQL Commands DDL DML DCL TCL Subqueries Group By Order By Functions",
    "type": "board"
  },
  "frame_006.png": {
    "timestamp": "00:04:22",
    "ocr_text": "ACID Properties Concurrency Control Locks",
    "type": "board"
  },
  "frame_007.png": {
    "timestamp": "00:04:33",
    "ocr_text": "Indexing Primary Cluster Secondary B and B+ Trees",
    "type": "board"
  },
  "frame_008.png": {
    "timestamp": "00:04:44",
    "ocr_text": "Views PL/SQL Triggers Cursors Stored Procedures",
    "type": "board"
  },
  "frame_009.png": {
    "timestamp": "00:05:15",
    "ocr_text": "RAID Levels Redundant Array of Independent Disks",
    "type": "board"
  },
  "frame_010.png": {
    "timestamp": "00:05:30",
    "ocr_text": "NoSQL Big DataBASE CAP Theorem Properties",
    "type": "board"
  }
}

# Data Warehouse Syllabus Data
DWH_TRANSCRIPT = os.path.join(DOWNLOADS_DIR, "Data Warehouse Syllabus (IBPS SO 2025) transcript.srt")
DWH_VIDEO = os.path.join(DOWNLOADS_DIR, "Data Warehouse Syllabus (IBPS SO 2025).mp4")
DWH_MAP = [
  {
    "block_id": "CB1",
    "lecture_title": "Data Warehouse Syllabus (IBPS SO 2025)",
    "title": "Data Warehouse Syllabus and Exam Structure",
    "transcript_range_percent": [0, 50],
    "explanation": "Data Warehouse and Data Mining is a critical technical topic for technical officer exams. Out of the 60 mains marks, it consistently accounts for 3–5 questions (averaging 4 marks) annually. This syllabus lecture details the entire topic hierarchy and overall exam strategy required to answer direct TECHNICAL questions without unnecessary programming depth.",
    "concepts": [
      {
        "term": "Exam Weightage",
        "definition": "Accounts for an average of 4 out of 60 marks in the Technical Mains paper (range: 3 to 5 questions)."
      },
      {
        "term": "Data Warehouse (DWH) Architecture",
        "definition": "A staging area, metadata directories, data warehouses, and domain-specific data marts used for business intelligence."
      }
    ],
    "examples": [
      {
        "sentence": "How should a candidate prepare for Data Warehouse questions in the IBPS SO Mains exam?",
        "rule": "Focus on structural comparisons (OLTP/OLAP, Star/Snowflake) and definitions, avoiding deep coding.",
        "working": "Weightage is 3–5 questions. All past questions are direct conceptual MCQs. Therefore, prioritize theoretical definitions and structural trade-offs."
      }
    ],
    "exercise_questions": [
      "Detail the typical score contribution of Data Warehousing in technical mains exams.",
      "List the main components of a Data Warehouse architecture mentioned in the overview."
    ],
    "visual_moments": [
      {"timestamp": "00:00:05", "type": "board", "description": "Syllabus overview and Data Warehousing topic list"}
    ],
    "teacher_quotes": [
      "Mains mein har saal aapko check karoge toh easily char question, teen question, ya paanch question on an average mil hi jayenge."
    ],
    "traps": [
      "Do not spend time on coding or complex algorithms; study structural characteristics and conceptual definitions only."
    ],
    "tricks": [
      "Syllabus Strategy: Cover all topics at a conceptual level (width over depth)."
    ]
  },
  {
    "block_id": "CB2",
    "title": "Syllabus Topics & Core Checklist",
    "transcript_range_percent": [50, 100],
    "explanation": "The core syllabus covers transactional vs analytical database differences (OLTP vs OLAP), cube operations (roll-up, drill-down, slice, dice, pivot), dimensional schemas (Star Schema vs Snowflake Schema), fact and dimension tables, data integration processes (ETL), and data mining preprocessing.",
    "concepts": [
      {
        "term": "OLAP vs OLTP",
        "definition": "OLAP is optimized for read-heavy multi-dimensional analysis, whereas OLTP is optimized for write-heavy concurrent transactions."
      },
      {
        "term": "OLAP Operations",
        "definition": "Roll-up (aggregates), Drill-down (splits), Slice (cuts 1 dimension), Dice (selects sub-cube), and Pivot (rotates)."
      },
      {
        "term": "Star vs Snowflake",
        "definition": "Star Schema uses denormalized dimension tables directly connected to fact tables; Snowflake Schema normalizes dimension tables."
      },
      {
        "term": "Data Preprocessing",
        "definition": "Essential cleaning, integration, transformation, and reduction phases executed on raw data before mining."
      }
    ],
    "examples": [],
    "exercise_questions": [
      "Compare Star Schema and Snowflake Schema based on normalization.",
      "Identify the five primary OLAP cube operations."
    ],
    "visual_moments": [
      {"timestamp": "00:00:52", "type": "board", "description": "OLAP cube operations: Slicing, Dicing, Roll-up, Drill-down, and Pivot"},
      {"timestamp": "00:01:03", "type": "board", "description": "Star Schema and Snowflake Schema diagrams"},
      {"timestamp": "00:01:17", "type": "board", "description": "ETL flow diagram"}
    ],
    "teacher_quotes": [
      "Ye saare points questions hain jo har saal kuch na kuch alag-alag tareeqe se ghum-fir ke pooche jaate hain."
    ],
    "traps": [
      "OLTP database normalization prevents redundancy but slows multi-table aggregation joins."
    ],
    "tricks": [
      "Exam Tip: Focus heavily on the preprocessing phases and OLAP operations as they are frequently tested."
    ]
  }
]
DWH_FRAMES = {
  "frame_001.png": {
    "timestamp": "00:00:05",
    "ocr_text": "Data Warehousing Architecture OLAP vs OLTP Star Snowflake Schemas",
    "type": "board"
  },
  "frame_002.png": {
    "timestamp": "00:00:52",
    "ocr_text": "OLAP Operations Slicing Dicing Roll-up Drill-down Pivot",
    "type": "board"
  },
  "frame_003.png": {
    "timestamp": "00:01:03",
    "ocr_text": "Star Schema and Snowflake Schema Comparison",
    "type": "board"
  },
  "frame_004.png": {
    "timestamp": "00:01:17",
    "ocr_text": "ETL Process Extract Transform Load",
    "type": "board"
  }
}

def clean_lecture_input():
    logger.info("Cleaning lecture-input directory...")
    for f in os.listdir(INPUT_DIR):
        fp = os.path.join(INPUT_DIR, f)
        if os.path.isfile(fp) and not f.startswith('.'):
            os.remove(fp)

def run_pipeline_for_lecture(video_src, transcript_src, concept_map, frame_manifest, lecture_name):
    logger.info(f"==================================================")
    logger.info(f"🎬 Processing Lecture: {lecture_name}")
    logger.info(f"==================================================")
    
    # Check input files exist
    if not os.path.exists(video_src):
        logger.error(f"Error: Source video file not found: {video_src}")
        return False
    if not os.path.exists(transcript_src):
        logger.error(f"Error: Source transcript file not found: {transcript_src}")
        return False
        
    clean_lecture_input()
    
    # Copy source files
    shutil.copy(video_src, os.path.join(INPUT_DIR, "LECTURE.mp4"))
    shutil.copy(transcript_src, os.path.join(INPUT_DIR, "transcript.srt"))
    logger.info("Copied video and transcript to lecture-input/")
    
    # Write profile
    with open(os.path.join(WORKSPACE_DIR, "lecture_profile.json"), "w") as f:
        json.dump(SYLLABUS_PROFILE, f, indent=2)
        
    # Write manifests
    with open(os.path.join(WORKSPACE_DIR, "concept_block_map.json"), "w") as f:
        json.dump(concept_map, f, indent=2)
    with open(os.path.join(WORKSPACE_DIR, "frame_manifest.json"), "w") as f:
        json.dump(frame_manifest, f, indent=2)
    logger.info("Wrote manifests (concept_block_map.json and frame_manifest.json)")
    
    # Reset/clear output docx
    active_docx = os.path.join(OUTPUT_DIR, "LECTURE_NOTES.docx")
    if os.path.exists(active_docx):
        os.remove(active_docx)
        
    # Run orchestrator
    logger.info("Executing LangGraph pipeline...")
    python_bin = sys.executable
    result = subprocess.run([python_bin, "scripts/langgraph_orchestrator.py"], cwd=WORKSPACE_DIR)
    
    if result.returncode != 0:
        logger.error("LangGraph pipeline failed.")
        return False
        
    # Copy output doc to a lecture-specific path while preserving the canonical handoff path.
    safe_name = lecture_name.replace(" ", "_")
    final_docx = os.path.join(OUTPUT_DIR, f"{safe_name}_NOTES.docx")
    if os.path.exists(active_docx):
        shutil.copy2(active_docx, final_docx)
        logger.info(f"Saved notes to {final_docx}")
        
    logger.info(f"🎉 Completed pipeline run successfully for: {lecture_name}")
    return True

def main():
    # 1. Run DBMS Syllabus
    dbms_success = run_pipeline_for_lecture(
        DBMS_VIDEO, DBMS_TRANSCRIPT, DBMS_MAP, DBMS_FRAMES, "DBMS Syllabus"
    )
    
    # 2. Run Data Warehouse Syllabus
    dwh_success = run_pipeline_for_lecture(
        DWH_VIDEO, DWH_TRANSCRIPT, DWH_MAP, DWH_FRAMES, "Data Warehouse Syllabus"
    )
    
    if dbms_success and dwh_success:
        logger.info("🎉 All syllabus lectures compiled successfully!")
        sys.exit(0)
    else:
        logger.error("❌ One or more syllabus pipeline runs failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()

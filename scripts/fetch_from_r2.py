#!/usr/bin/env python3
import os
import sys
import json
import re
from pathlib import Path
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from docx import Document

# 1. Load environment variables
load_dotenv()

R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL") or os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "lecture-notes")
R2_REGION = os.getenv("R2_REGION", "auto")

# Target keys mapping
TARGET_FILES = {
    "lectures/lec-8-modulation-demodulation/notes.docx": "notes-output/LECTURE_NOTES_Lec-8_Modulation_Demodulation_original.docx",
    "lectures/lec-9-digital-to-analog-conversion/notes.docx": "notes-output/LECTURE_NOTES_Lec-9_Digital_to_Analog_conversion_original.docx",
    "lectures/lec-12-types-of-multiplexing-fdm-tdm-wdm/notes.docx": "notes-output/LECTURE_NOTES_Lec-12_Types_of_Multiplexing_FDM_TDM_WDM_original.docx",
    "lectures/lec-14-error-control-in-data-link-layer/notes.docx": "notes-output/LECTURE_NOTES_Lec-14_Error_Control_in_Data_Link_Layer_original.docx"
}

def count_images_in_docx(filepath):
    """Count image shapes and references in the docx file."""
    try:
        doc = Document(filepath)
        inline_shapes_count = len(doc.inline_shapes)
        
        # Count image relations
        rel_image_count = 0
        for r_id, rel in doc.part.rels.items():
            if "image" in rel.reltype:
                rel_image_count += 1
                
        # Count actual image parts in the package
        pkg_image_count = 0
        try:
            for part in doc.part.package.parts:
                if "image" in part.content_type:
                    pkg_image_count += 1
        except Exception:
            pass

        return {
            "inline_shapes": inline_shapes_count,
            "relations": rel_image_count,
            "package_parts": pkg_image_count,
            "error": None
        }
    except Exception as e:
        return {
            "inline_shapes": 0,
            "relations": 0,
            "package_parts": 0,
            "error": str(e)
        }

def list_bucket_objects(s3_client, bucket):
    """List all objects in the bucket."""
    objects = []
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket):
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat()
                    })
    except Exception as e:
        print(f"Error listing bucket: {e}", file=sys.stderr)
    return objects

def find_alternatives(all_objects, query_terms):
    """Find files matching target keywords in their keys."""
    matches = []
    for obj in all_objects:
        key_lower = obj['key'].lower()
        score = sum(1 for term in query_terms if term.lower() in key_lower)
        if score > 0:
            matches.append((obj, score))
    # Sort by relevance score descending
    matches.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matches]

def main():
    print("--- Starting R2 Fetch Script ---")
    
    # Ensure notes-output/ folder exists
    Path("notes-output").mkdir(parents=True, exist_ok=True)
    
    # Verify credentials
    if not all([R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        print("Error: R2 credentials missing in .env", file=sys.stderr)
        sys.exit(1)
        
    # Init S3 client
    s3 = boto3.client(
        service_name='s3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name=R2_REGION,
        config=Config(signature_version='s3v4')
    )
    
    report_data = {
        "bucket_name": R2_BUCKET_NAME,
        "endpoint": R2_ENDPOINT_URL,
        "downloads": [],
        "all_objects": [],
        "alternatives": {}
    }
    
    # Try downloading target files
    any_missing_or_empty = False
    
    for r2_key, local_path in TARGET_FILES.items():
        print(f"\nChecking: s3://{R2_BUCKET_NAME}/{r2_key}")
        result = {
            "key": r2_key,
            "local_path": local_path,
            "found": False,
            "size": 0,
            "empty": True,
            "downloaded": False,
            "images": None,
            "error": None
        }
        
        try:
            # Check object metadata first
            head = s3.head_object(Bucket=R2_BUCKET_NAME, Key=r2_key)
            result["found"] = True
            result["size"] = head.get('ContentLength', 0)
            result["empty"] = result["size"] == 0
            
            if result["size"] > 0:
                print(f"File found. Size: {result['size']} bytes. Downloading...")
                s3.download_file(R2_BUCKET_NAME, r2_key, local_path)
                result["downloaded"] = True
                
                # Check images
                img_counts = count_images_in_docx(local_path)
                result["images"] = img_counts
                print(f"Downloaded successfully. Image counts: {img_counts}")
            else:
                print("Warning: File is empty (0 bytes).")
                any_missing_or_empty = True
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                print(f"Key not found: {r2_key}")
            else:
                print(f"AWS ClientError checking {r2_key}: {e}")
                result["error"] = str(e)
            any_missing_or_empty = True
        except Exception as e:
            print(f"Unexpected error checking {r2_key}: {e}")
            result["error"] = str(e)
            any_missing_or_empty = True
            
        report_data["downloads"].append(result)
        
    # If any files are missing/empty, list the bucket and look for alternatives
    print("\n--- Bucket scan & search for alternatives ---")
    all_objects = list_bucket_objects(s3, R2_BUCKET_NAME)
    report_data["all_objects"] = all_objects
    print(f"Total objects in bucket: {len(all_objects)}")
    
    # Search terms extracted from target lecture keys
    search_queries = {
        "lec-8": ["lec-8", "modulation", "demodulation"],
        "lec-9": ["lec-9", "digital", "analog", "conversion"],
        "lec-12": ["lec-12", "multiplexing", "fdm", "tdm", "wdm"],
        "lec-14": ["lec-14", "error", "control", "link", "layer"]
    }
    
    for name, terms in search_queries.items():
        alts = find_alternatives(all_objects, terms)
        report_data["alternatives"][name] = alts
        if alts:
            print(f"Found {len(alts)} potential alternative(s) for {name}:")
            for alt in alts[:5]:
                print(f"  - {alt['key']} (size: {alt['size']} bytes)")
                
    # Generate the Markdown report
    report_dir = Path(".agents/teamwork_preview_worker_r2_fetch_gen2")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "r2_report.md"
    
    markdown_content = []
    markdown_content.append("# Cloudflare R2 Lecture Notes Fetch Report")
    markdown_content.append(f"\n- **Bucket:** `{R2_BUCKET_NAME}`")
    markdown_content.append(f"- **Endpoint:** `{R2_ENDPOINT_URL}`")
    markdown_content.append(f"- **Total Objects in Bucket:** {len(all_objects)}")
    
    markdown_content.append("\n## Requested Target Files Status")
    markdown_content.append("| Key | Local Path | Found? | Size (bytes) | Downloaded? | Inline Shapes | Image Relations | Package Images | Notes/Errors |")
    markdown_content.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    
    for dl in report_data["downloads"]:
        found_str = "Yes" if dl["found"] else "No"
        size_str = str(dl["size"])
        dl_str = "Yes" if dl["downloaded"] else "No"
        err_msg = dl["error"] or ""
        if dl["empty"] and dl["found"]:
            err_msg = "File is empty (0 bytes)"
            
        if dl["images"]:
            imgs = dl["images"]
            is_str = str(imgs["inline_shapes"])
            rel_str = str(imgs["relations"])
            pkg_str = str(imgs["package_parts"])
            if imgs["error"]:
                err_msg = f"python-docx error: {imgs['error']}"
        else:
            is_str, rel_str, pkg_str = "-", "-", "-"
            
        markdown_content.append(
            f"| `{dl['key']}` | `{dl['local_path']}` | {found_str} | {size_str} | {dl_str} | {is_str} | {rel_str} | {pkg_str} | {err_msg} |"
        )
        
    markdown_content.append("\n## Alternative File Search Findings")
    for name, alts in report_data["alternatives"].items():
        markdown_content.append(f"\n### Alternatives for `{name}`")
        if not alts:
            markdown_content.append("No alternative files found in the bucket containing matching keywords.")
        else:
            markdown_content.append("| Key | Size (bytes) | Last Modified |")
            markdown_content.append("| --- | --- | --- |")
            for alt in alts:
                markdown_content.append(f"| `{alt['key']}` | {alt['size']} | {alt['last_modified']} |")
                
    markdown_content.append("\n## All Objects in Bucket")
    if not all_objects:
        markdown_content.append("No objects found in the bucket.")
    else:
        markdown_content.append("| Key | Size (bytes) | Last Modified |")
        markdown_content.append("| --- | --- | --- |")
        for obj in all_objects:
            markdown_content.append(f"| `{obj['key']}` | {obj['size']} | {obj['last_modified']} |")
            
    with open(report_file, "w") as f:
        f.write("\n".join(markdown_content))
        
    print(f"\nReport written to: {report_file}")
    print("--- Done ---")

if __name__ == "__main__":
    main()

# 🚀 DEPLOYMENT & STORAGE STRATEGY

**Generated:** June 10, 2025  
**Analysis Model:** Qwen 3.7 Max (High Thinking)  
**Project:** Agentic Lecture Notes Reconstruction  

---

## 📊 EXECUTIVE SUMMARY

### Your Questions Answered:

| Question | Recommendation | Cost | Complexity |
|----------|---------------|------|------------|
| **Dockerize?** | ✅ YES - For reproducibility & CI/CD | Free | Low |
| **Build UI?** | ⚠️ LATER - Start with CLI + Webhook | Free | Medium |
| **Cloud Storage for Videos?** | ✅ YES - Use Backblaze B2 or Cloudflare R2 | Free tier available | Low |
| **Database Needed?** | ❌ NO - SQLite + JSON is sufficient | Free | None |
| **Scale to More Lectures?** | ✅ Use object storage + CDN | ~$0-5/month | Low |

---

## 🐳 DOCKERIZATION STRATEGY

### Why Dockerize? (Critical Benefits)

1. **Dependency Hell Solved**: FFmpeg, Tesseract, Python packages all containerized
2. **Reproducible Runs**: Same environment on your laptop, server, or CI/CD
3. **MCP Server Isolation**: Each MCP server runs in its own container
4. **Easy Scaling**: Spin up 10 parallel note generators for batch processing
5. **Production Ready**: Deploy to any cloud (AWS, GCP, Azure, DigitalOcean)

### Docker Architecture

```
┌─────────────────────────────────────────────────────┐
│  Docker Compose Stack                                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────┐  ┌──────────────────┐         │
│  │ Orchestrator     │  │ MCP Server 1     │         │
│  │ Container        │  │ (Port 8011)      │         │
│  │ - LangGraph      │  │ - generate_docx  │         │
│  │ - Audit          │  └──────────────────┘         │
│  └──────────────────┘                               │
│                                                      │
│  ┌──────────────────┐  ┌──────────────────┐         │
│  │ MCP Server 2     │  │ MCP Server 3     │         │
│  │ (Port 8012)      │  │ (Port 8013)      │         │
│  │ - audit_server   │  │ - extract_frames │         │
│  └──────────────────┘  └──────────────────┘         │
│                                                      │
│  ┌──────────────────┐                               │
│  │ Shared Volume    │                               │
│  │ - lecture-input/ │                               │
│  │ - notes-output/  │                               │
│  │ - agent_memory/  │                               │
│  └──────────────────┘                               │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Dockerfile (Multi-Stage Build)

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements-mcp.txt .
RUN pip install --no-cache-dir --user -r requirements-mcp.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY scripts/ ./scripts/
COPY .agents/ ./.agents/
COPY *.json ./

# Create volumes for data
VOLUME ["/app/lecture-input", "/app/notes-output", "/app/agent_memory"]

# Expose MCP server ports
EXPOSE 8011 8012 8013

# Default command
CMD ["python3", "scripts/langgraph_orchestrator.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  orchestrator:
    build: .
    volumes:
      - ./lecture-input:/app/lecture-input
      - ./notes-output:/app/notes-output
      - ./agent_memory:/app/agent_memory
      - ./logs:/app/logs
    environment:
      - MCP_API_KEY=lecture_notes_secure_mcp_key_2026
      - PYTHONUNBUFFERED=1
    depends_on:
      - mcp-generator
      - mcp-audit
      - mcp-extractor
    networks:
      - lecture-net

  mcp-generator:
    build: .
    command: python3 scripts/mcp_servers/generate_docx_server.py
    ports:
      - "8011:8011"
    environment:
      - MCP_API_KEY=lecture_notes_secure_mcp_key_2026
    volumes:
      - ./lecture-input:/app/lecture-input
      - ./notes-output:/app/notes-output
    networks:
      - lecture-net

  mcp-audit:
    build: .
    command: python3 scripts/mcp_servers/audit_server.py
    ports:
      - "8012:8012"
    environment:
      - MCP_API_KEY=lecture_notes_secure_mcp_key_2026
    volumes:
      - ./notes-output:/app/notes-output
    networks:
      - lecture-net

  mcp-extractor:
    build: .
    command: python3 scripts/mcp_servers/extract_frames_server.py
    ports:
      - "8013:8013"
    environment:
      - MCP_API_KEY=lecture_notes_secure_mcp_key_2026
    volumes:
      - ./lecture-input:/app/lecture-input
      - ./frames-cache:/app/frames-cache
    networks:
      - lecture-net

volumes:
  lecture-input:
  notes-output:
  agent_memory:
  logs:
  frames-cache:

networks:
  lecture-net:
    driver: bridge
```

### Usage Commands

```bash
# Build containers
docker-compose build

# Run full pipeline
docker-compose up orchestrator

# Run all services (including MCP servers)
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f orchestrator

# Scale for batch processing (10 parallel orchestrators)
docker-compose up --scale orchestrator=10 -d
```

---

## 🖥️ UI DEVELOPMENT STRATEGY

### Current State: CLI-Only
✅ Works perfectly for developers and power users  
❌ Not accessible to non-technical students/faculty  

### Recommended Approach: Progressive Enhancement

#### Phase 1: Minimal Viable UI (FREE)
**Technology:** FastAPI + HTMX (no JavaScript framework needed)

```python
# Simple 100-line web interface
from fastapi import FastAPI, UploadFile, File
import subprocess

app = FastAPI()

@app.post("/upload")
async def upload_lecture(video: UploadFile, transcript: UploadFile):
    # Save files
    video_path = f"lecture-input/{video.filename}"
    transcript_path = f"lecture-input/{transcript.filename}"
    
    # Trigger pipeline
    result = subprocess.run(
        ["python3", "scripts/langgraph_orchestrator.py"],
        capture_output=True
    )
    
    return {"status": "completed", "output": "notes-output/LECTURE_NOTES.docx"}
```

**Deployment:** Run on same server as Docker containers  
**Cost:** $0 (uses existing infrastructure)  
**Time to Build:** 2-4 hours  

#### Phase 2: Enhanced UI (OPTIONAL)
**Technology:** React + Tailwind CSS + WebSocket for progress tracking

Features:
- Drag-and-drop file upload
- Real-time progress bar (which gate is running)
- Download generated notes
- View audit report
- Lecture library (list of processed lectures)

**Cost:** $0 (static hosting on GitHub Pages/Netlify)  
**Time to Build:** 1-2 days  

#### Phase 3: Production UI (LATER)
**Technology:** Next.js + PostgreSQL + Redis

Features:
- User authentication
- Multi-user support
- Batch processing queue
- Email notifications when complete
- API for third-party integrations

**Cost:** ~$10/month (VPS + database)  
**Time to Build:** 1-2 weeks  

### My Recommendation: START WITH PHASE 1

Build a simple FastAPI web interface that:
1. Accepts file uploads via HTTP POST
2. Triggers the existing Docker pipeline
3. Returns download link when complete

This gives you a web UI in <4 hours with zero new dependencies.

---

## ☁️ CLOUD STORAGE STRATEGY (FREE TIER FOCUS)

### The Problem
- Lecture videos: 300MB - 2GB each
- Extracted frames: 50-200MB per lecture
- Slide decks: 10-50MB each
- **Total per lecture:** ~500MB - 2.5GB
- **Your disk space:** Limited

### Solution: Object Storage + Smart Caching

#### Option 1: Backblaze B2 (BEST CHOICE)
**Free Tier:** 10GB storage + 1GB/day downloads  
**Paid:** $0.005/GB/month ($5/TB/month)

**Why B2?**
- ✅ Cheapest cloud storage available
- ✅ S3-compatible API (works with existing tools)
- ✅ No egress fees up to 3x your storage
- ✅ Automatic lifecycle policies

**Setup:**
```bash
# Install B2 CLI
pip install b2sdk

# Authenticate
b2 authorize_account YOUR_KEY_ID YOUR_APP_KEY

# Create bucket
b2 create-bucket lecture-notes allPrivate

# Upload video
b2 upload-file lecture-notes LECTURE.mp4 lectures/2025-06-10/LECTURE.mp4

# Generate pre-signed URL (valid 24 hours)
b2 get-download-url-by-name lecture-notes lectures/2025-06-10/LECTURE.mp4
```

**Integration Code:**
```python
from b2sdk.v2 import InMemoryAccountInfo, B2Api

def upload_to_b2(local_path, bucket_name, remote_path):
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", KEY_ID, APP_KEY)
    
    bucket = b2_api.get_bucket_by_name(bucket_name)
    bucket.upload_local_file(local_path, remote_path)
    
    return bucket.get_download_url(remote_path)
```

#### Option 2: Cloudflare R2 (EXCELLENT ALTERNATIVE)
**Free Tier:** 10GB storage + 10M operations/month  
**Paid:** $0.015/GB/month

**Why R2?**
- ✅ ZERO egress fees (unlimited downloads)
- ✅ S3-compatible
- ✅ Built-in CDN
- ✅ Faster global access

**Setup:**
```bash
# Install AWS CLI (R2 is S3-compatible)
pip install awscli

# Configure R2 endpoint
aws configure set endpoint_url https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com

# Upload
aws s3 cp LECTURE.mp4 s3://lecture-notes/lectures/2025-06-10/LECTURE.mp4
```

#### Option 3: Google Drive API (QUICK START)
**Free Tier:** 15GB shared across Gmail/Drive  
**API:** Free up to 100GB/day bandwidth

**Why Consider?**
- ✅ You already have a Google account
- ✅ No new signup needed
- ✅ Familiar interface

**Downsides:**
- ❌ Slower than object storage
- ❌ Rate limits on API calls
- ❌ Not designed for programmatic access

#### Option 4: Internet Archive (COMPLETELY FREE)
**Storage:** Unlimited  
**Cost:** $0 forever

**Why Consider?**
- ✅ Truly free, no limits
- ✅ Non-profit, mission-aligned (education)
- ✅ Permanent preservation

**Downsides:**
- ❌ Slower upload/download
- ❌ Public by default (can mark as private)
- ❌ Less reliable API

### Recommended Hybrid Strategy

```
┌─────────────────────────────────────────────────────┐
│  Storage Hierarchy                                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  HOT STORAGE (Local SSD)                            │
│  - Currently processing lecture                     │
│  - Last 3 lectures' frames                          │
│  - Active agent_memory/                             │
│  Size: ~5GB                                         │
│                                                      │
│  WARM STORAGE (Backblaze B2)                        │
│  - All completed lecture videos                     │
│  - Frame caches (compressed)                        │
│  - Generated notes archive                          │
│  Size: 100GB+                                       │
│  Cost: ~$0.50/month                                 │
│                                                      │
│  COLD STORAGE (Internet Archive)                    │
│  - Final notes (PDF backup)                         │
│  - Raw transcripts                                  │
│  - Historical records                               │
│  Size: Unlimited                                    │
│  Cost: $0                                           │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Automated Lifecycle Policy

```python
# scripts/storage_manager.py

import os
import shutil
from datetime import datetime, timedelta
from b2sdk.v2 import B2Api, InMemoryAccountInfo

class StorageManager:
    def __init__(self):
        self.local_input = "lecture-input/"
        self.local_output = "notes-output/"
        self.b2_bucket = "lecture-notes"
        
    def archive_completed_lecture(self, lecture_id):
        """Move completed lecture from local to B2"""
        # Upload video to B2
        video_path = f"{self.local_input}{lecture_id}.mp4"
        if os.path.exists(video_path):
            upload_to_b2(video_path, self.b2_bucket, f"videos/{lecture_id}.mp4")
            os.remove(video_path)  # Free local space
            
        # Upload generated notes
        notes_path = f"{self.local_output}{lecture_id}_NOTES.docx"
        if os.path.exists(notes_path):
            upload_to_b2(notes_path, self.b2_bucket, f"notes/{lecture_id}_NOTES.docx")
            
        # Keep metadata local
        # (agent_memory/ stays on device)
        
    def cleanup_old_frames(self, days=7):
        """Delete frame caches older than N days"""
        frames_dir = "frames-cache/"
        cutoff = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(frames_dir):
            filepath = os.path.join(frames_dir, filename)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff:
                os.remove(filepath)
                
    def download_for_processing(self, lecture_id):
        """Download lecture from B2 for processing"""
        # Download video
        video_url = get_b2_url(self.b2_bucket, f"videos/{lecture_id}.mp4")
        download_file(video_url, f"{self.local_input}{lecture_id}.mp4")
        
        # Download transcript if stored separately
        # ...
```

---

## 🗄️ DATABASE STRATEGY

### Current Architecture: SQLite + JSON
```
agent_memory/
├── run_*.json           # Run metadata
├── failures/
│   └── fail_*.json      # Failure details
logs/
└── langgraph_checkpoints.db  # SQLite for LangGraph state
```

### Do You Need a Real Database? NO.

**Reasons SQLite is Sufficient:**
1. **Single-User System**: Only one pipeline running at a time
2. **Low Write Volume**: ~1 run per lecture (not high-frequency)
3. **Simple Queries**: Just need to store/retrieve run history
4. **Zero Maintenance**: No server to manage, no backups needed
5. **Portable**: One file, easy to copy/move

### When Would You Need PostgreSQL?

| Scenario | Current Load | Threshold | Action |
|----------|-------------|-----------|--------|
| Concurrent Users | 1 | >10 | Add PostgreSQL |
| Runs per Day | 1-5 | >50 | Add PostgreSQL |
| Query Complexity | Simple lookups | Analytics/Reports | Add PostgreSQL |
| Multi-Device Sync | Single device | 5+ devices | Add PostgreSQL + Sync |

### If You Scale: PostgreSQL Schema

```sql
-- Only needed if you outgrow SQLite

CREATE TABLE lectures (
    id UUID PRIMARY KEY,
    title VARCHAR(500),
    video_url TEXT,
    transcript_url TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE TABLE concept_blocks (
    id UUID PRIMARY KEY,
    lecture_id UUID REFERENCES lectures(id),
    block_id VARCHAR(50),
    title VARCHAR(500),
    transcript_start TIME,
    transcript_end TIME,
    example_count INT
);

CREATE TABLE run_history (
    id UUID PRIMARY KEY,
    lecture_id UUID REFERENCES lectures(id),
    status VARCHAR(50),
    audit_score INT,
    failed_gates JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE quality_gates (
    run_id UUID REFERENCES run_history(id),
    gate_number INT,
    gate_name VARCHAR(100),
    passed BOOLEAN,
    error_message TEXT
);
```

---

## 📈 SCALING STRATEGY

### Current Capacity
- **Throughput:** 1 lecture at a time
- **Processing Time:** ~5-15 minutes per lecture (depends on length)
- **Storage:** Local disk only

### Scaling to 100+ Lectures

#### Horizontal Scaling (Parallel Processing)
```bash
# Process 10 lectures simultaneously
docker-compose up --scale orchestrator=10

# Each orchestrator picks up a different lecture from queue
```

#### Queue-Based Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Upload    │────▶│  Redis Queue │────▶│ Orchestrator│
│   Service   │     │  (Lectures)  │     │   Pool (N)  │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │   B2 Cloud  │
                                         │   Storage   │
                                         └─────────────┘
```

#### Cost Projection (100 Lectures/Month)

| Resource | Usage | Cost/Month |
|----------|-------|------------|
| Backblaze B2 Storage | 50GB (100 × 500MB) | $0.25 |
| B2 Downloads | 100GB (2× per lecture) | $0 (within free tier) |
| Compute (DigitalOcean) | 1 CPU, 2GB RAM | $6.00 |
| Domain + SSL | Custom domain | $0.50 |
| **TOTAL** | | **~$7/month** |

---

## 🎯 ACTION PLAN (PRIORITIZED)

### Week 1: Foundation (FREE)
- [ ] **Day 1-2:** Create Dockerfile and docker-compose.yml
- [ ] **Day 3:** Test containerized pipeline end-to-end
- [ ] **Day 4:** Set up Backblaze B2 account and upload first lecture
- [ ] **Day 5:** Integrate B2 upload into `memory_store.py`

### Week 2: Automation (FREE)
- [ ] **Day 1-2:** Build `storage_manager.py` with lifecycle policies
- [ ] **Day 3:** Add automatic archival after successful run
- [ ] **Day 4-5:** Create simple FastAPI web UI (Phase 1)

### Week 3: Enhancement (~$5/month)
- [ ] **Day 1-2:** Deploy to cloud VPS (DigitalOcean/AWS Lightsail)
- [ ] **Day 3-4:** Add webhook for upload notifications
- [ ] **Day 5:** Set up custom domain and HTTPS

### Month 2: Production (OPTIONAL)
- [ ] Build React UI (Phase 2)
- [ ] Add user authentication
- [ ] Implement batch processing queue
- [ ] Add email notifications

---

## 🔧 IMPLEMENTATION FILES TO CREATE

### 1. `/workspace/Dockerfile`
```dockerfile
# See full content in "Dockerization Strategy" section above
```

### 2. `/workspace/docker-compose.yml`
```yaml
# See full content in "Dockerization Strategy" section above
```

### 3. `/workspace/scripts/storage_manager.py`
```python
# Handles B2 uploads, downloads, and lifecycle policies
# See "Automated Lifecycle Policy" section above
```

### 4. `/workspace/web_ui/app.py`
```python
# FastAPI minimal web interface
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
import subprocess
import uuid

app = FastAPI(title="Lecture Notes Generator")

@app.post("/process")
async def process_lecture(
    video: UploadFile,
    transcript: UploadFile,
    background_tasks: BackgroundTasks
):
    lecture_id = str(uuid.uuid4())
    
    # Save uploaded files
    video_path = f"lecture-input/{lecture_id}_{video.filename}"
    transcript_path = f"lecture-input/{lecture_id}_{transcript.filename}"
    
    with open(video_path, "wb") as f:
        f.write(video.file.read())
    with open(transcript_path, "wb") as f:
        f.write(transcript.file.read())
    
    # Queue processing
    background_tasks.add_task(run_pipeline, lecture_id)
    
    return {
        "lecture_id": lecture_id,
        "status": "processing",
        "check_status_endpoint": f"/status/{lecture_id}"
    }

def run_pipeline(lecture_id: str):
    result = subprocess.run(
        ["python3", "scripts/langgraph_orchestrator.py"],
        capture_output=True
    )
    # Update status, send notification, etc.

@app.get("/download/{lecture_id}")
async def download_notes(lecture_id: str):
    # Return generated .docx file
    pass
```

### 5. `/workspace/.dockerignore`
```
__pycache__/
*.pyc
*.pyo
.git/
agent_memory/runs/*.json
notes-output/*.docx
lecture-input/*.mp4
.env
venv/
```

---

## 💰 COMPLETE COST BREAKDOWN

### Completely Free Setup
| Component | Service | Cost |
|-----------|---------|------|
| Containerization | Docker | $0 |
| Orchestration | Docker Compose | $0 |
| Cloud Storage (10GB) | Backblaze B2 | $0 |
| Web Hosting | Render/Railway free tier | $0 |
| Domain | .tk/.ml domain or localhost | $0 |
| SSL | Let's Encrypt | $0 |
| **TOTAL** | | **$0/month** |

### Production Setup (Recommended)
| Component | Service | Cost |
|-----------|---------|------|
| VPS | DigitalOcean Droplet (1CPU/2GB) | $6/month |
| Cloud Storage | Backblaze B2 (50GB) | $0.25/month |
| Domain | Namecheap .com | $0.83/month |
| Backup Storage | Internet Archive | $0 |
| **TOTAL** | | **~$7/month** |

### Enterprise Setup (Future)
| Component | Service | Cost |
|-----------|---------|------|
| Kubernetes Cluster | DigitalOcean K8s | $12/month |
| Managed Database | DigitalOcean PostgreSQL | $15/month |
| CDN | Cloudflare Pro | $20/month |
| Cloud Storage | Backblaze B2 (500GB) | $2.50/month |
| Monitoring | Sentry + Datadog | $29/month |
| **TOTAL** | | **~$80/month** |

---

## 🎓 FINAL RECOMMENDATIONS

### 1. ✅ DOCKERIZE IMMEDIATELY
**Why:** Solves dependency issues, enables scaling, production-ready  
**Effort:** 2-4 hours  
**Benefit:** Run anywhere, reproducible builds  

### 2. ⚠️ BUILD MINIMAL UI (PHASE 1)
**Why:** Makes project accessible to non-developers  
**Effort:** 2-4 hours  
**Benefit:** Faculty/students can use without CLI knowledge  

### 3. ✅ USE BACKBLAZE B2 FOR STORAGE
**Why:** Cheapest option, S3-compatible, generous free tier  
**Effort:** 1-2 hours  
**Benefit:** Never run out of disk space, automatic archival  

### 4. ❌ SKIP DATABASE FOR NOW
**Why:** SQLite handles current load perfectly  
**When to Revisit:** If you hit 50+ runs/day or need multi-user sync  

### 5. ✅ IMPLEMENT LIFECYCLE POLICIES
**Why:** Automatically move old lectures to cloud, keep local disk clean  
**Effort:** 2-3 hours  
**Benefit:** Set-and-forget storage management  

---

## 🚀 QUICK START COMMANDS

```bash
# 1. Create Docker setup
cd /workspace
# (Create Dockerfile and docker-compose.yml)

# 2. Build and test
docker-compose build
docker-compose up orchestrator

# 3. Set up Backblaze B2
pip install b2sdk
b2 authorize_account YOUR_KEY_ID YOUR_APP_KEY
b2 create-bucket lecture-notes allPrivate

# 4. Add storage manager to pipeline
# (Edit memory_store.py to call storage_manager.archive_completed_lecture())

# 5. Launch minimal web UI
cd web_ui
uvicorn app:app --host 0.0.0.0 --port 8000

# 6. Access UI at http://localhost:8000
```

---

**CONCLUSION:** Your project is production-ready. With Docker + Backblaze B2 + minimal FastAPI UI, you can scale to 100+ lectures for **under $7/month** while keeping everything else free. Start with Dockerization this week, add cloud storage next week, and build the UI when you have time.

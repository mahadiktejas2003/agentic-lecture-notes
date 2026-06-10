# =============================================================================
# FREE FOREVER STACK - SETUP GUIDE FOR MAC M4 AIR
# Agentic Lecture Notes Platform | Production Ready
# =============================================================================

## 🎯 OVERVIEW

This guide will set up your lecture notes platform with:
- ✅ **Cloudflare R2**: 10GB free storage (videos, notes, transcripts)
- ✅ **Supabase**: 500MB free PostgreSQL + Auth + Realtime
- ✅ **Docker**: Native Mac M4 Silicon (ARM64) support
- ✅ **Next.js UI**: Beautiful web interface with real-time progress
- ✅ **$0/month cost** for ~50-80 lectures (with compression)

---

## 📋 PREREQUISITES

1. **Mac M4 Air** with macOS Sonoma or later
2. **Docker Desktop for Mac** (ARM64 version)
3. **Git** (pre-installed on macOS)
4. **Node.js 20+** (for local development)
5. **Python 3.11+** (for local development)

---

## 🚀 STEP 1: CREATE FREE CLOUD ACCOUNTS

### 1A. Cloudflare R2 Storage (10GB Free)

1. Go to https://www.cloudflare.com/sign-up
2. Create a free account (no credit card required)
3. Navigate to **R2 Storage** in the dashboard
4. Click **Create Bucket** → Name: `lecture-notes`
5. Go to **Manage R2 API Tokens** → **Create API Token**
   - Permissions: Object Read & Write
   - Save these credentials:
     ```
     Account ID: [your-account-id]
     Access Key ID: [your-access-key]
     Secret Access Key: [your-secret-key]
     Bucket Name: lecture-notes
     ```

### 1B. Supabase Database + Auth (500MB Free)

1. Go to https://supabase.com/sign-up
2. Create a free account (GitHub login recommended)
3. Click **New Project**
   - Name: `lecture-notes-db`
   - Database Password: [choose strong password]
   - Region: Choose closest to you (e.g., East US)
4. Wait 2-3 minutes for project to initialize
5. Go to **Settings** → **API**
   - Save these credentials:
     ```
     Project URL: https://[your-project].supabase.co
     Anon/Public Key: [your-anon-key]
     Service Role Key: [your-service-key] (keep secret!)
     ```

### 1C. Optional: Groq AI (Free Tier - 50 req/day)

1. Go to https://console.groq.com/signup
2. Create account → Get API Key
3. Free tier: 50 requests/day (Mixtral/Llama3)

---

## 🔧 STEP 2: CONFIGURE ENVIRONMENT VARIABLES

Create a `.env` file in your project root:

```bash
cd /Users/tejasmahadik/Documents/agentic-lecture-notes
nano .env
```

Paste this template (replace with YOUR credentials):

```bash
# =============================================================================
# CLOUDFLARE R2 CONFIGURATION
# =============================================================================
R2_BUCKET_NAME=lecture-notes
R2_ACCOUNT_ID=your-cloudflare-account-id-here
R2_ACCESS_KEY_ID=your-r2-access-key-here
R2_SECRET_ACCESS_KEY=your-r2-secret-key-here

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_KEY=your-supabase-service-key-here

# =============================================================================
# AI MODEL APIs (Optional - leave blank for local fallback)
# =============================================================================
GROQ_API_KEY=your-groq-api-key-here
CLOUDFLARE_AI_TOKEN=your-cloudflare-ai-token-here

# =============================================================================
# MCP SERVER CONFIGURATION
# =============================================================================
MCP_API_KEY=lecture_notes_secure_mcp_key_2026
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`)

---

## 🗄️ STEP 3: SET UP SUPABASE DATABASE

Run this SQL in Supabase SQL Editor:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create lectures table (metadata only - NO binary data)
CREATE TABLE lectures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    title TEXT NOT NULL,
    lecture_topic TEXT,
    status TEXT NOT NULL DEFAULT 'uploading' 
        CHECK (status IN ('uploading', 'processing', 'completed', 'failed')),
    
    -- R2 Storage Keys (pointers to files in Cloudflare R2)
    video_r2_key TEXT,
    transcript_r2_key TEXT,
    slides_r2_key TEXT,
    notes_r2_key TEXT,
    
    -- Metadata
    concept_map JSONB,
    frame_manifest JSONB,
    slide_manifest JSONB,
    audit_results JSONB,
    student_feedback TEXT,
    file_sizes JSONB,
    
    -- Pipeline Progress
    processing_progress INTEGER DEFAULT 0,
    current_stage TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    archived BOOLEAN DEFAULT FALSE
);

-- Create indexes for performance
CREATE INDEX idx_lectures_user_id ON lectures(user_id);
CREATE INDEX idx_lectures_status ON lectures(status);
CREATE INDEX idx_lectures_created_at ON lectures(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE lectures ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their own lectures
CREATE POLICY "Users can view own lectures"
    ON lectures FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own lectures"
    ON lectures FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own lectures"
    ON lectures FOR UPDATE
    USING (auth.uid() = user_id);

-- Create pipeline_runs table for audit trail
CREATE TABLE pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lecture_id UUID REFERENCES lectures(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',
    gate_results JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Create index
CREATE INDEX idx_pipeline_runs_lecture_id ON pipeline_runs(lecture_id);

-- Enable RLS
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;

-- RLS Policy
CREATE POLICY "Users can view own pipeline runs"
    ON pipeline_runs FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM lectures 
        WHERE lectures.id = pipeline_runs.lecture_id 
        AND lectures.user_id = auth.uid()
    ));
```

---

## 🐳 STEP 4: BUILD & RUN DOCKER CONTAINERS

### 4A. Install Docker Desktop for Mac (ARM64)

1. Download from https://desktop.docker.com/mac/main/arm64/Docker.dmg
2. Install and launch Docker Desktop
3. Ensure it's running (whale icon in menu bar)

### 4B. Build Containers (Optimized for Mac M4)

```bash
cd /Users/tejasmahadik/Documents/agentic-lecture-notes

# Build all containers (ARM64 native)
docker-compose build

# This will take 5-10 minutes on first run
# Downloads base images, installs FFmpeg, Tesseract, Python deps
```

### 4C. Launch All Services

```bash
# Start all 6 services
docker-compose up -d

# Check status
docker-compose ps

# View logs (real-time)
docker-compose logs -f
```

Expected output:
```
NAME                STATUS              PORTS
agentic-web-ui      Up                  0.0.0.0:3000->3000/tcp
agentic-pipeline    Up                  
agentic-redis       Up                  6379/tcp
agentic-mcp-gen     Up                  0.0.0.0:8011->8011/tcp
agentic-mcp-audit   Up                  0.0.0.0:8012->8012/tcp
agentic-mcp-extract Up                  0.0.0.0:8013->8013/tcp
```

---

## 🖥️ STEP 5: ACCESS THE WEB UI

Open your browser:

```
http://localhost:3000
```

You should see:
- 📊 Dashboard with recent lectures
- ⬆️ Upload button (drag & drop)
- 📚 Lecture library
- ⚙️ Settings (storage stats)

---

## 📹 STEP 6: UPLOAD YOUR FIRST LECTURE

### Option A: Via Web UI (Recommended)

1. Go to http://localhost:3000/upload
2. Drag & drop your video file (up to 300MB+)
3. Add lecture title and topic
4. Click **Upload & Process**
5. Watch real-time progress through 15-Gate Audit

### Option B: Via Command Line

```bash
# Copy video to lecture-input folder
cp ~/Downloads/lecture_video.mp4 \
   /Users/tejasmahadik/Documents/agentic-lecture-notes/lecture-input/

# The pipeline will auto-detect and process it
docker-compose logs -f pipeline-worker
```

---

## 🗜️ STEP 7: VIDEO COMPRESSION (CRITICAL FOR FREE TIER)

Compress videos BEFORE upload to maximize free storage:

```bash
# Install ffmpeg via Homebrew (if not already installed)
brew install ffmpeg

# Compress 300MB lecture to ~80MB (H.265/HEVC)
ffmpeg -i input_lecture.mp4 \
  -c:v libx265 -crf 28 -preset medium \
  -c:a aac -b:a 128k \
  output_compressed.mp4

# Expected reduction: 60-70% smaller with minimal quality loss
```

**Storage Math:**
- Without compression: 10GB = ~30 lectures (300MB each)
- With compression: 10GB = ~100 lectures (80MB each)
- **3.3x more lectures for FREE!**

---

## 📊 STEP 8: MONITOR STORAGE & COSTS

### Check R2 Storage Usage

```bash
# Install AWS CLI (for R2 management)
brew install awscli

# Configure for R2
aws configure set profile.r2.region auto
aws configure set profile.r2.endpoint_url https://your-account-id.r2.cloudflarestorage.com
aws configure set profile.r2.aws_access_key_id YOUR_ACCESS_KEY
aws configure set profile.r2.aws_secret_access_key YOUR_SECRET_KEY

# Check bucket size
aws s3 ls s3://lecture-notes --recursive --profile r2 | awk '{total+=$3} END {print total/1024/1024 " MB"}'
```

### Check Supabase Database Size

Go to Supabase Dashboard → Database → Stats
- Should show <10MB even with 100+ lectures (metadata only)

---

## 💰 COST PROJECTION

| Lectures/Month | Storage Used | Monthly Cost |
|----------------|--------------|--------------|
| 0-20           | ~2GB         | **$0.00**    |
| 20-50          | ~5GB         | **$0.00**    |
| 50-80          | ~10GB        | **$0.00**    |
| 80-100         | ~12GB        | **$0.03**    |
| 100-200        | ~20GB        | **$0.15**    |

**Note:** With H.265 compression, 10GB holds ~80-100 lectures!

---

## 🔧 TROUBLESHOOTING

### Issue: Docker containers won't start

```bash
# Restart Docker Desktop
# Or run:
docker-compose down
docker-compose up -d --build
```

### Issue: R2 upload fails

Check credentials in `.env`:
```bash
cat .env | grep R2
```

Test connection:
```bash
python3 scripts/storage_manager.py test-connection
```

### Issue: Supabase connection error

Verify URL and keys:
```bash
curl -X GET "https://your-project.supabase.co/rest/v1/" \
  -H "apikey: your-anon-key" \
  -H "Authorization: Bearer your-anon-key"
```

### Issue: Video processing OOM (Out of Memory)

Reduce concurrent frame extraction:
```bash
# Edit scripts/langgraph_orchestrator.py
# Change: MAX_CONCURRENT_FRAMES = 4 → 2
```

---

## 🎯 NEXT STEPS

1. ✅ Test with a small lecture video (50MB)
2. ✅ Verify notes generation quality
3. ✅ Set up automatic backup to Mega.nz (optional)
4. ✅ Customize UI theme/colors
5. ✅ Share with classmates!

---

## 📞 SUPPORT

- Documentation: `PROJECT_MEMORY.md`
- Deployment Guide: `DEPLOYMENT_STRATEGY.md`
- Agent Skills: `.agents/skills/`
- MCP Servers: `scripts/mcp_servers/`

---

**🎉 CONGRATULATIONS!** You now have a production-grade, forever-free lecture notes platform running on your Mac M4 Air!

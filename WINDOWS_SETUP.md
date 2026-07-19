# Windows Setup Guide

This guide provides instructions to run the entire **ASR transcription and notes pipeline** on a Windows PC (specifically optimized for systems with an **AMD Ryzen CPU, 16GB RAM, and no dedicated Nvidia GPU**).

---

## 📋 Prerequisites

Before starting, install the following software on Windows:

1. **Python 3.10+**: Download and install from the [official site](https://www.python.org/downloads/). Make sure to check **"Add Python to PATH"** during installation.
2. **Git**: Download and install [Git for Windows](https://gitforwindows.org/).
3. **FFmpeg** (Required for audio extraction from videos):
   * Download the latest build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z).
   * Extract the ZIP archive (e.g., to `C:\ffmpeg`).
   * Add the folder `C:\ffmpeg\bin` to your **Windows System PATH Environment Variables** so FFmpeg can be run from the Command Prompt.

---

## 🛠️ Step 1: Install and Set Up the Project

1. Open **Command Prompt** (cmd) or **PowerShell** and clone this repository:
   ```cmd
   git clone <your-repository-url>
   cd agentic-lecture-notes
   ```

2. Create and activate a Python virtual environment:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install the dependencies (including `faster-whisper` for local CPU-based ASR):
   ```cmd
   pip install -r requirements.txt
   ```

---

## 🎙️ Step 2: Running Local ASR (Transcription) on CPU

On Windows, the pipeline automatically detects that Apple Metal (MLX) is not available and falls back to **`faster-whisper`** to run transcription on your **Ryzen 7 CPU**:
* It is configured to use the **`base`** whisper model using **`int8`** quantization.
* This delivers extremely accurate transcripts with a very low RAM footprint (less than 500MB) and runs fast on Ryzen CPUs.

To test local transcription manually on a video file:
```cmd
venv\Scripts\activate
python scripts/transcribe_lecture.py --input "path\to\your\video.mp4" --output-dir "lecture-input"
```

---

## ☁️ Step 3: Configure Cloud AI Notes Generation

Because local 2B models lack the reasoning depth to format complex JSON and write study notes on a 16GB RAM machine, **notes generation is routed to the Cloud AI (Gemini Pro)**.

Create a `.env` file in the project root and add the following:
```env
# Disable local LLM for notes (uses Cloud AI)
USE_LOCAL_LLM="false"

# Cloudflare R2 Credentials
R2_ENDPOINT_URL="https://your-account-id.r2.cloudflarestorage.com"
R2_ACCESS_KEY_ID="your-access-key-id"
R2_SECRET_ACCESS_KEY="your-secret-access-key"
R2_BUCKET_NAME="lecture-notes"
R2_REGION="auto"

# Supabase Credentials (for web dashboard status)
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

---

## ⚙️ Step 4: Register Background Services on Windows

You can run the watcher and generator tasks as background services using the **Windows Task Scheduler**.

1. Open **Command Prompt as Administrator**.
2. Activate the virtual environment and run the services installer:
   ```cmd
   venv\Scripts\activate
   python scripts/setup_services.py install
   ```

This will automatically create and register three Windows tasks:
* **`LectureNotes_ASR_Watcher`**: Runs 24/7 in the background transcribing new video downloads.
* **`LectureNotes_Downloads_Tracker`**: Runs the notes generator pipeline every 20 minutes (between 7 AM and 1 PM).
* **`LectureNotes_WebUI`**: Launches the local dashboard at `http://localhost:8000`.

To check task status:
```cmd
python scripts/setup_services.py status
```

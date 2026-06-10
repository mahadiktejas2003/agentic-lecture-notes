# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements-mcp.txt .
RUN pip install --no-cache-dir --user -r requirements-mcp.txt

# Install additional Python dependencies for full pipeline
RUN pip install --no-cache-dir --user \
    langgraph \
    langchain \
    python-docx \
    pillow \
    pytesseract \
    opencv-python-headless \
    b2sdk \
    fastapi \
    uvicorn \
    python-multipart

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

# Create directories for data
RUN mkdir -p lecture-input notes-output agent_memory logs frames-cache

# Create volumes for data
VOLUME ["/app/lecture-input", "/app/notes-output", "/app/agent_memory", "/app/logs", "/app/frames-cache"]

# Expose MCP server ports
EXPOSE 8011 8012 8013 8000

# Default command
CMD ["python3", "scripts/langgraph_orchestrator.py"]

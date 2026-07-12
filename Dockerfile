FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg tesseract-ocr poppler-utils git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser

WORKDIR /app

COPY requirements-mcp.txt .
RUN pip install --no-cache-dir -r requirements-mcp.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

CMD ["python3", "scripts/langgraph_orchestrator.py"]

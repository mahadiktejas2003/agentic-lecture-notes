FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg tesseract-ocr poppler-utils git

WORKDIR /app

COPY requirements-mcp.txt .
RUN pip install --no-cache-dir -r requirements-mcp.txt

COPY . .

CMD ["python3", "scripts/langgraph_orchestrator.py"]

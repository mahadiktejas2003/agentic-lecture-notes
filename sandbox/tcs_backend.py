import json
import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="TCS iON Sandbox Local Backend Server")

# Allow CORS for ease of access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tcs_ion_sandbox.html")
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exam_results_log.json")
METADATA_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests_metadata.json")

class AnswersMapItem(BaseModel):
    id: int
    choice: str | None = None
    correct: str

class TimelineItem(BaseModel):
    time: str
    timestamp: float
    event: str

class TelemetryPayload(BaseModel):
    candidateId: str
    examId: str
    score: str
    correctCount: int
    incorrectCount: int
    timeline: list[TimelineItem]
    answersMap: list[AnswersMapItem]

@app.get("/", response_class=HTMLResponse)
async def serve_sandbox():
    """Serves the main TCS iON clone application file."""
    if os.path.exists(HTML_FILE_PATH):
        return FileResponse(HTML_FILE_PATH)
    return HTMLResponse("<h2>Error: tcs_ion_sandbox.html not found in sandbox directory.</h2>", status_code=404)

@app.get("/api/tests")
async def get_all_tests():
    """Returns a list of all available mock tests with basic metadata."""
    if not os.path.exists(METADATA_FILE_PATH):
        raise HTTPException(status_code=404, detail="Tests metadata database not found.")
    try:
        with open(METADATA_FILE_PATH, "r", encoding="utf-8") as f:
            tests = json.load(f)
        overview = []
        for t in tests:
            overview.append({
                "examId": t["examId"],
                "title": t["title"],
                "subject": t["subject"],
                "categoryFocus": t["categoryFocus"],
                "durationSeconds": t["durationSeconds"],
                "questionCount": len(t["questions"])
            })
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read tests metadata: {str(e)}")

@app.get("/api/tests/{exam_id}")
async def get_test_details(exam_id: str):
    """Returns the full configuration and questions of a specific test."""
    if not os.path.exists(METADATA_FILE_PATH):
        raise HTTPException(status_code=404, detail="Tests metadata database not found.")
    try:
        with open(METADATA_FILE_PATH, "r", encoding="utf-8") as f:
            tests = json.load(f)
        for t in tests:
            if t["examId"] == exam_id:
                return t
        raise HTTPException(status_code=404, detail=f"Test with ID {exam_id} not found.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read test details: {str(e)}")

@app.post("/webhook")
async def receive_webhook(payload: TelemetryPayload):
    """Receives local mock exam telemetry data and persists it to a local file."""
    data = payload.model_dump()
    
    # Print a beautiful representation of the results in the terminal
    total_qs = len(data['answersMap'])
    print("\n" + "="*60)
    print("      TCS iON DIGITAL EXAMINATION TELEMETRY DISPATCH      ")
    print("="*60)
    print(f"Candidate Roll ID: {data['candidateId']}")
    print(f"Exam Identifier  : {data['examId']}")
    print(f"Final Score      : {data['score']} / {total_qs}.00")
    print(f"Correct Answers  : {data['correctCount']}")
    print(f"Incorrect Answers: {data['incorrectCount']}")
    print("-"*60)
    print("  USER TIMELINE FOOTPRINT:")
    for log in data['timeline']:
        print(f"    [{log['time']}] {log['event']}")
    print("="*60 + "\n")
    
    # Save to local JSON file
    results = []
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "r") as f:
                results = json.load(f)
        except Exception:
            results = []
            
    results.append(data)
    
    with open(LOG_FILE_PATH, "w") as f:
        json.dump(results, f, indent=2)
        
    return {"status": "success", "message": "Telemetry written to local database ledger successfully."}

@app.get("/results")
async def get_results():
    """Returns all saved mock exam records."""
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to read results: {str(e)}"}
    return []

if __name__ == "__main__":
    print(f"Starting server... Serving file: {HTML_FILE_PATH}")
    uvicorn.run("tcs_backend:app", host="127.0.0.1", port=8000, reload=True)

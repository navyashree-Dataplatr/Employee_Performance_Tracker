
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .data_processor import DataProcessor

# -----------------------------
# Create FastAPI app
# -----------------------------
app = FastAPI(title="Employee Performance Tracker API")

# -----------------------------
# Enable CORS (same as Flask CORS)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Initialize DataProcessor
# -----------------------------
data_processor = DataProcessor(
    employees_csv=r"E:\poc projects\Employee_Performance_Tracker_App\Backend\Dataplatr_employees.csv",
    google_sheet_url="https://docs.google.com/spreadsheets/d/1ZUhkf7B5dU1-mfQOyTGRetS_GCo9lsqoXeq2KEq2bC4/edit?gid=1012493901#gid=1012493901"
)

# -----------------------------
# Health check
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -----------------------------
# Get employees
# -----------------------------
@app.get("/employees")
def get_employees():
    return data_processor.get_employees_list()

# -----------------------------
# Employee summary
# -----------------------------
@app.get("/employee-summary")
def get_employee_summary():
    return data_processor.get_employee_summary()

# -----------------------------
# Request body model for chat
# -----------------------------
class ChatRequest(BaseModel):
    query: str

# -----------------------------
# Chat endpoint
# -----------------------------
@app.post("/chat")
def chat(request: ChatRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")

    return data_processor.process_query(request.query)

# -----------------------------
# Chart data
# -----------------------------
@app.get("/chart-data")
def get_chart_data():
    chart_data = data_processor.get_chart_data()
    if not chart_data:
        raise HTTPException(status_code=500, detail="Unable to fetch chart data")
    return chart_data



# python -m uvicorn modularized_backend.app:app --reload --port 5000
#  With this
# from .google_sheet_connector import SimpleGoogleSheetConnector
# The dot (.) is non-negotiable
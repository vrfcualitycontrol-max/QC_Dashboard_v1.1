import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy import text, create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, JSON, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "")
REPORTS_DIR = os.getenv("REPORTS_DIR", "/app/reports")
DATA_MODE = os.getenv("DATA_MODE", "api")

app = FastAPI(title="Dashboard SC Backend", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None

# Database models
metadata = MetaData()

employee_scores = Table(
    "employee_scores",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("employee_name", String(255), nullable=False),
    Column("month", String(50), nullable=False),
    Column("period", String(50), nullable=False),
    Column("tqs", Float, default=0.0),
    Column("aht", String(20), default="N/A"),
    Column("activity_count", Integer, default=0),
    Column("svp_scores", JSON, default=dict),
    Column("raw_scores", JSON, default=dict),
    Column("tendencies", String, default=""),
    Column("recommendations", String, default=""),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)

employee_info = Table(
    "employees",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), unique=True, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: str
    service: str


class EmployeeResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int


class HistoryResponse(BaseModel):
    employee: str
    history: List[Dict[str, Any]]


class ForecastResponse(BaseModel):
    period: str
    forecast: List[Dict[str, Any]]
    model: str


def check_db() -> tuple[bool, str]:
    """Check database connection status."""
    if engine is None:
        return False, "not_configured"
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
        return True, "connected"
    except SQLAlchemyError:
        return False, "error"


def init_db():
    """Initialize database tables."""
    if engine:
        metadata.create_all(engine, checkfirst=True)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/api/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    ok, db_state = check_db()
    status_code = 200 if ok or db_state == "not_configured" else 503
    return JSONResponse(
        {
            "status": "healthy" if ok else "degraded",
            "database": db_state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "dashboard-sc-backend",
            "data_mode": DATA_MODE,
        },
        status_code=status_code,
    )


@app.get("/api/employees", response_model=EmployeeResponse)
def employees():
    """Get list of all employees."""
    if not engine:
        return {"items": [], "total": 0}
    
    try:
        with Session(engine) as session:
            # Get unique employee names from scores table
            stmt = select(employee_scores.c.employee_name).distinct()
            result = session.execute(stmt)
            names = [row[0] for row in result if row[0]]
            
            return {"items": [{"name": name} for name in sorted(names)], "total": len(names)}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/history/{employee_name}", response_model=HistoryResponse)
def history(employee_name: str, month: Optional[str] = None):
    """Get history for specific employee."""
    if not engine:
        return {"employee": employee_name, "history": []}
    
    try:
        with Session(engine) as session:
            # Build query
            stmt = select(employee_scores).where(employee_scores.c.employee_name == employee_name)
            
            if month:
                stmt = stmt.where(employee_scores.c.month == month)
            
            # Order by month and period
            stmt = stmt.order_by(employee_scores.c.month.desc(), employee_scores.c.period.desc())
            
            result = session.execute(stmt)
            rows = result.fetchall()
            
            history_data = []
            for row in rows:
                history_data.append({
                    "month": row.month,
                    "period": row.period,
                    "tqs": row.tqs,
                    "aht": row.aht,
                    "activity_count": row.activity_count,
                    "svp": row.svp_scores or {},
                    "tendencies": row.tendencies or "",
                    "recommendations": row.recommendations or "",
                })
            
            return {"employee": employee_name, "history": history_data}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/metrics")
def get_metrics():
    """Get all dashboard metrics in DASHBOARD_DATA format."""
    if not engine:
        return {}
    
    try:
        with Session(engine) as session:
            # Get all data grouped by employee
            stmt = select(employee_scores).order_by(
                employee_scores.c.employee_name,
                employee_scores.c.month.desc(),
                employee_scores.c.period.desc()
            )
            
            result = session.execute(stmt)
            rows = result.fetchall()
            
            # Build DASHBOARD_DATA structure
            dashboard_data = {}
            
            for row in rows:
                employee = row.employee_name
                month = row.month
                period = row.period
                
                if employee not in dashboard_data:
                    dashboard_data[employee] = {"months": {}}
                
                if month not in dashboard_data[employee]["months"]:
                    dashboard_data[employee]["months"][month] = {"periods": []}
                
                period_data = {
                    "period": period,
                    "tqs": row.tqs or 0.0,
                    "aht": row.aht or "N/A",
                    "svp": row.svp_scores or {},
                    "raw_scores": row.raw_scores or {},
                    "tendencies": row.tendencies or "",
                    "rec": row.recommendations or "",
                    "activity_count": row.activity_count or 0,
                }
                
                dashboard_data[employee]["months"][month]["periods"].append(period_data)
            
            # Sort periods within each month
            for employee_data in dashboard_data.values():
                for month_data in employee_data["months"].values():
                    month_data["periods"].sort(key=lambda x: x["period"])
            
            return dashboard_data
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/trends/forecast", response_model=ForecastResponse)
def forecast():
    """Get forecast data (placeholder for future ML implementation)."""
    return {"period": "current", "forecast": [], "model": "placeholder"}


@app.post("/api/upload/xlsx")
async def upload_xlsx(file: UploadFile = File(...)):
    """Upload and process XLSX file."""
    if not file.filename or not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Only XLSX files are allowed")
    
    if not REPORTS_DIR or not os.path.exists(REPORTS_DIR):
        raise HTTPException(status_code=500, detail="Reports directory not configured")
    
    # Save file to reports directory
    file_path = os.path.join(REPORTS_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {"status": "success", "message": f"File {file.filename} saved", "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


@app.post("/api/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process PDF file."""
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if not REPORTS_DIR or not os.path.exists(REPORTS_DIR):
        raise HTTPException(status_code=500, detail="Reports directory not configured")
    
    # Save file to reports directory
    file_path = os.path.join(REPORTS_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {"status": "success", "message": f"File {file.filename} saved", "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


@app.post("/api/process-reports")
def process_reports():
    """Trigger report processing (calls auto_updater logic)."""
    # This endpoint would trigger the auto_updater.py logic
    # For now, it's a placeholder
    return {"status": "processing_started", "message": "Report processing initiated"}


@app.get("/api/data-mode")
def get_data_mode():
    """Get current data mode."""
    return {"mode": DATA_MODE, "description": "API Mode - data from PostgreSQL"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
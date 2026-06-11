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
    # === НОВЫЕ ПОЛЯ: Финансы ===
    Column("collected_amount", Float, default=0.0),
    Column("collected_count", Integer, default=0),
    Column("collection_rate", Float, default=0.0),
    Column("plan_fulfillment", Float, default=0.0),
    # === НОВЫЕ ПОЛЯ: CRM ===
    Column("crm_actions", JSON, default=dict),
    Column("crm_actions_summary", String, default=""),
    Column("crm_behavior_pattern", String, default=""),
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
    """Initialize database tables and run automatic migrations if needed."""
    if engine:
        metadata.create_all(engine, checkfirst=True)
        # Автоматические ALTER TABLE для плавного расширения схемы данных
        try:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE employee_scores ADD COLUMN IF NOT EXISTS collected_amount FLOAT DEFAULT 0.0;"))
                conn.execute(text("ALTER TABLE employee_scores ADD COLUMN IF NOT EXISTS collected_count INTEGER DEFAULT 0;"))
                conn.execute(text("ALTER TABLE employee_scores ADD COLUMN IF NOT EXISTS collection_rate FLOAT DEFAULT 0.0;"))
                conn.execute(text("ALTER TABLE employee_scores ADD COLUMN IF NOT EXISTS plan_fulfillment FLOAT DEFAULT 0.0;"))
                conn.execute(text("ALTER TABLE employee_scores ADD COLUMN IF NOT EXISTS crm_actions JSON DEFAULT '{}';"))
                conn.execute(text("ALTER TABLE employee_scores ADD COLUMN IF NOT EXISTS crm_actions_summary VARCHAR DEFAULT '';"))
                conn.execute(text("ALTER TABLE employee_scores ADD COLUMN IF NOT EXISTS crm_behavior_pattern VARCHAR DEFAULT '';"))
        except Exception as e:
            print(f"[WARN] Error running automatic database migrations: {e}")


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


def calculate_efficiency_ratio(record: dict) -> float:
    """
    Композитный показатель: как качество разговора влияет на сборы
    Формула: (TQS нормализованный) * (collection_rate нормализованный) * (коэффициент активности) * 100
    """
    tqs = record.get("tqs", 0.0)
    collection_rate = record.get("collection_rate", 0.0)
    activity_count = record.get("activity_count", 0)
    
    tqs_norm = min(tqs / 100.0, 1.0) if tqs else 0.0
    rate_norm = min(collection_rate / 100.0, 1.0) if collection_rate else 0.0
    activity_factor = min(activity_count / 100.0, 1.5) if activity_count else 1.0
    
    return round(tqs_norm * rate_norm * activity_factor * 100.0, 2)


def calculate_crm_consistency(record: dict) -> float:
    """Вычисление уровня дисциплины CRM: Завершенные задачи / Созданные задачи"""
    crm = record.get("crm_actions", {})
    if not crm:
        return 0.0
    created = crm.get("tasks_created", 0)
    completed = crm.get("tasks_completed", 0)
    if created == 0:
        return 1.0 if completed > 0 else 0.0
    return round(completed / created, 2)


def calculate_correlation(data: list, field_x: str, field_y: str) -> float:
    """Расчет коэффициента корреляции Пирсона для вложенных полей на чистом Python"""
    def get_nested(obj, path: str):
        for key in path.split('.'):
            if isinstance(obj, dict):
                obj = obj.get(key, 0)
            elif hasattr(obj, key):
                obj = getattr(obj, key, 0)
            else:
                obj = 0
        return obj
        
    x_vals = []
    y_vals = []
    for d in data:
        x_val = get_nested(d, field_x)
        y_val = get_nested(d, field_y)
        try:
            x_vals.append(float(x_val) if x_val is not None else 0.0)
        except (ValueError, TypeError):
            x_vals.append(0.0)
        try:
            y_vals.append(float(y_val) if y_val is not None else 0.0)
        except (ValueError, TypeError):
            y_vals.append(0.0)
            
    n = len(x_vals)
    if n < 3:
        return 0.0
        
    pairs = [(x, y) for x, y in zip(x_vals, y_vals) if (x != 0 or y != 0)]
    if len(pairs) < 3:
        return 0.0
        
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    
    cov = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(len(xs)))
    var_x = sum((xs[i] - mean_x) ** 2 for i in range(len(xs)))
    var_y = sum((ys[i] - mean_y) ** 2 for i in range(len(xs)))
    
    if var_x == 0 or var_y == 0:
        return 0.0
        
    r = cov / (var_x * var_y) ** 0.5
    return round(r, 2)


@app.get("/api/metrics")
def get_metrics(month: Optional[str] = None, period: Optional[str] = None):
    """Get all dashboard metrics filtered by month and period."""
    if not engine:
        return {}
        
    try:
        with Session(engine) as session:
            stmt = select(employee_scores)
            
            if month:
                stmt = stmt.where(employee_scores.c.month == month)
            if period and period not in ("Все", "Все периоды"):
                stmt = stmt.where(employee_scores.c.period == period)
                
            stmt = stmt.order_by(
                employee_scores.c.employee_name,
                employee_scores.c.month.desc(),
                employee_scores.c.period.desc()
            )
            
            result = session.execute(stmt)
            rows = result.fetchall()
            
            # Группировка по сотруднику
            operator_groups = {}
            for row in rows:
                name = row.employee_name
                if name not in operator_groups:
                    operator_groups[name] = []
                operator_groups[name].append(row)
                
            metrics_list = []
            for name, records in operator_groups.items():
                total_tqs = 0.0
                total_aht_sec = 0
                aht_count = 0
                activity_count = 0
                collected_amount = 0.0
                collected_count = 0
                total_plan_fulfillment = 0.0
                total_collection_rate = 0.0
                
                crm_actions = {}
                crm_actions_summary = ""
                crm_behavior_pattern = "balanced"
                recommendations = ""
                
                for r in records:
                    total_tqs += r.tqs or 0.0
                    activity_count += r.activity_count or 0
                    
                    aht_str = r.aht
                    if aht_str and aht_str != "N/A":
                        parts = aht_str.split(':')
                        if len(parts) == 2:
                            try:
                                total_aht_sec += int(parts[0]) * 60 + int(parts[1])
                                aht_count += 1
                            except ValueError:
                                pass
                                
                    collected_amount += r.collected_amount or 0.0
                    collected_count += r.collected_count or 0
                    total_plan_fulfillment += r.plan_fulfillment or 0.0
                    total_collection_rate += r.collection_rate or 0.0
                    
                    if r.crm_actions:
                        for k, v in r.crm_actions.items():
                            try:
                                crm_actions[k] = crm_actions.get(k, 0) + int(v)
                            except (ValueError, TypeError):
                                pass
                                
                    if r.crm_actions_summary:
                        crm_actions_summary = r.crm_actions_summary
                    if r.crm_behavior_pattern:
                        crm_behavior_pattern = r.crm_behavior_pattern
                    if r.recommendations:
                        recommendations = r.recommendations
                
                n_records = len(records)
                avg_tqs = total_tqs / n_records if n_records > 0 else 0.0
                avg_aht_sec = total_aht_sec / aht_count if aht_count > 0 else 0
                
                avg_aht = "N/A"
                if avg_aht_sec > 0:
                    mins = int(avg_aht_sec // 60)
                    secs = int(avg_aht_sec % 60)
                    avg_aht = f"{mins:02d}:{secs:02d}"
                    
                avg_plan = total_plan_fulfillment / n_records if n_records > 0 else 0.0
                avg_rate = total_collection_rate / n_records if n_records > 0 else 0.0
                
                eff_record = {
                    "tqs": avg_tqs,
                    "collection_rate": avg_rate,
                    "activity_count": activity_count
                }
                eff_ratio = calculate_efficiency_ratio(eff_record)
                
                consistency_record = {
                    "crm_actions": crm_actions
                }
                consistency_score = calculate_crm_consistency(consistency_record)
                
                metric_item = {
                    "employee_name": name,
                    "tqs": round(avg_tqs, 2),
                    "aht": avg_aht,
                    "activity_count": activity_count,
                    "svp_scores": records[0].svp_scores,
                    "recommendations": recommendations,
                    
                    "collected_amount": round(collected_amount, 2),
                    "collected_count": collected_count,
                    "collection_rate": round(avg_rate, 2),
                    "plan_fulfillment": round(avg_plan, 2),
                    
                    "crm_actions": crm_actions,
                    "crm_actions_summary": crm_actions_summary or "Сбалансированная рабочая логика",
                    "crm_behavior_pattern": crm_behavior_pattern or "balanced",
                    
                    "efficiency_ratio": eff_ratio,
                    "crm_consistency_score": consistency_score
                }
                metrics_list.append(metric_item)
                
            team_averages = {}
            if metrics_list:
                team_tqs = sum(m["tqs"] for m in metrics_list) / len(metrics_list)
                
                total_aht_sec = 0
                aht_count = 0
                for m in metrics_list:
                    aht_str = m["aht"]
                    if aht_str and aht_str != "N/A":
                        parts = aht_str.split(':')
                        if len(parts) == 2:
                            total_aht_sec += int(parts[0]) * 60 + int(parts[1])
                            aht_count += 1
                avg_aht_sec = total_aht_sec / aht_count if aht_count > 0 else 0
                avg_aht = "N/A"
                if avg_aht_sec > 0:
                    mins = int(avg_aht_sec // 60)
                    secs = int(avg_aht_sec % 60)
                    avg_aht = f"{mins:02d}:{secs:02d}"
                    
                total_collected = sum(m["collected_amount"] for m in metrics_list)
                avg_rate = sum(m["collection_rate"] for m in metrics_list) / len(metrics_list)
                avg_crm_rate = sum(m["crm_consistency_score"] for m in metrics_list) / len(metrics_list)
                
                team_averages = {
                    "tqs": round(team_tqs, 2),
                    "aht": avg_aht,
                    "collected_amount": round(total_collected, 2),
                    "collection_rate": round(avg_rate, 2),
                    "crm_completion_rate": round(avg_crm_rate, 2)
                }
                
            correlations = {
                "tqs_vs_collections": calculate_correlation(metrics_list, "tqs", "collected_amount"),
                "crm_promised_vs_collections": calculate_correlation(metrics_list, "crm_actions.promised_to_pay", "collected_amount"),
                "aht_vs_collection_rate": 0.0
            }
            
            # Подготовка числового значения AHT в секундах для расчета корреляции
            aht_sec_list = []
            for m in metrics_list:
                aht_str = m["aht"]
                if aht_str and aht_str != "N/A":
                    parts = aht_str.split(':')
                    if len(parts) == 2:
                        aht_sec_list.append(int(parts[0]) * 60 + int(parts[1]))
                    else:
                        aht_sec_list.append(0.0)
                else:
                    aht_sec_list.append(0.0)
            
            corr_metrics_list = []
            for idx, m in enumerate(metrics_list):
                m_copy = m.copy()
                m_copy["aht_numeric"] = aht_sec_list[idx]
                corr_metrics_list.append(m_copy)
                
            correlations["aht_vs_collection_rate"] = calculate_correlation(corr_metrics_list, "aht_numeric", "collection_rate")
            
            return {
                "period": f"{month} - {period}" if month and period and period != "Все" else (month or "Все периоды"),
                "team_averages": team_averages,
                "correlations": correlations,
                "data": metrics_list
            }
            
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
import os
import json
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy import text, create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, JSON, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from parser import (
    detect_file_type, parse_quality_bytes, parse_collections_bytes,
    parse_crm_bytes, parse_report_pdf_bytes, normalize_name, SVP_KEYS
)

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
            
            # Избегаем дублирования при агрегации всего месяца
            if not period or period in ("Все", "Все периоды"):
                has_weekly = any(r.period not in ("Все", "Неизвестно") for r in rows)
                if has_weekly:
                    rows = [r for r in rows if r.period not in ("Все", "Неизвестно")]
                else:
                    rows = [r for r in rows if r.period == "Все"]
            
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


def sync_db_data(conn, month: str):
    """
    Синхронизирует и распределяет месячные данные (период='Все') по еженедельным периодам,
    или наоборот, подтягивает месячные данные в новые еженедельные периоды.
    """
    import re
    
    # 1. Получаем все существующие записи за данный месяц
    stmt = select(employee_scores).where(employee_scores.c.month == month)
    rows = conn.execute(stmt).fetchall()
    
    # Группируем по сотруднику и периоду
    by_employee = {}
    for r in rows:
        emp = r.employee_name
        if emp not in by_employee:
            by_employee[emp] = {}
        by_employee[emp][r.period] = r
        
    for emp, periods in by_employee.items():
        all_record = periods.get("Все")
        weekly_periods = [p for p in periods.keys() if p != "Все"]
        
        if not all_record or not weekly_periods:
            continue
            
        n_weeks = len(weekly_periods)
        
        # --- 1. Распределение CRM ---
        has_crm = all_record.crm_actions and len(all_record.crm_actions) > 0
        if has_crm:
            crm_actions_all = all_record.crm_actions
            crm_summary = all_record.crm_actions_summary
            crm_pattern = all_record.crm_behavior_pattern
            
            # Делим числовые счетчики на количество недель
            split_actions = {}
            for k, v in crm_actions_all.items():
                if isinstance(v, (int, float)):
                    split_actions[k] = int(v / n_weeks) if isinstance(v, int) else round(v / n_weeks, 2)
                else:
                    split_actions[k] = v
                    
            for wp in weekly_periods:
                w_rec = periods[wp]
                conn.execute(
                    employee_scores.update()
                    .where(employee_scores.c.id == w_rec.id)
                    .values(
                        crm_actions=split_actions,
                        crm_actions_summary=crm_summary,
                        crm_behavior_pattern=crm_pattern,
                        updated_at=datetime.now(timezone.utc)
                    )
                )
                
        # --- 2. Распределение Collections ---
        has_collections = all_record.collected_amount is not None and all_record.collected_amount > 0
        if has_collections:
            total_amount = all_record.collected_amount
            total_count = all_record.collected_count or 0
            rate = all_record.collection_rate or 0.0
            fulfillment = all_record.plan_fulfillment or 0.0
            
            # Пытаемся достать по дням из raw_scores
            by_day = {}
            if all_record.raw_scores and isinstance(all_record.raw_scores, dict) and "by_day" in all_record.raw_scores:
                by_day = all_record.raw_scores["by_day"]
                
            default_split_amount = total_amount / n_weeks
            default_split_count = int(total_count / n_weeks)
            
            for wp in weekly_periods:
                w_rec = periods[wp]
                match = re.match(r"(\d+)-(\d+)", wp)
                
                period_amount = 0.0
                period_count = 0
                has_matching_days = False
                
                if match and by_day:
                    start_day = int(match.group(1))
                    end_day = int(match.group(2))
                    
                    for day, amt in by_day.items():
                        try:
                            day_int = int(day)
                            if start_day <= day_int <= end_day:
                                period_amount += amt
                                period_count += 1
                                has_matching_days = True
                        except (ValueError, TypeError):
                            pass
                            
                if has_matching_days:
                    w_amount = round(period_amount, 2)
                    w_count = period_count
                else:
                    if by_day:
                        w_amount = 0.0
                        w_count = 0
                    else:
                        w_amount = round(default_split_amount, 2)
                        w_count = default_split_count
                        
                conn.execute(
                    employee_scores.update()
                    .where(employee_scores.c.id == w_rec.id)
                    .values(
                        collected_amount=w_amount,
                        collected_count=w_count,
                        collection_rate=rate,
                        plan_fulfillment=fulfillment,
                        updated_at=datetime.now(timezone.utc)
                    )
                )


def write_parsed_data_to_db(file_type: str, month: str, period: str, data: dict) -> int:
    """
    Записывает распарсенные данные в PostgreSQL.
    Для каждого сотрудника — upsert (INSERT or UPDATE) по ключу (employee_name, month, period).
    """
    if not engine:
        raise ValueError("Database not configured")
    
    count = 0
    with engine.begin() as conn:
        for employee_name, emp_data in data.items():
            # Проверяем существование записи
            select_stmt = select(employee_scores.c.id).where(
                employee_scores.c.employee_name == employee_name,
                employee_scores.c.month == month,
                employee_scores.c.period == period,
            )
            existing = conn.execute(select_stmt).first()
            
            # Формируем поля для обновления в зависимости от типа файла
            update_fields = {}
            
            if file_type == "quality":
                update_fields = {
                    "tqs": emp_data.get("tqs", 0.0),
                    "aht": emp_data.get("aht", "N/A"),
                    "activity_count": emp_data.get("activity_count", 0),
                    "svp_scores": emp_data.get("svp", {}),
                    "raw_scores": emp_data.get("raw_scores", {}),
                }
            elif file_type == "collections":
                update_fields = {
                    "collected_amount": emp_data.get("collected_amount", 0.0),
                    "collected_count": emp_data.get("collected_count", 0),
                    "collection_rate": emp_data.get("collection_rate", 0.0),
                    "plan_fulfillment": emp_data.get("plan_fulfillment", 0.0),
                }
                if period == "Все" and "by_day" in emp_data:
                    update_fields["raw_scores"] = {"by_day": emp_data["by_day"]}
            elif file_type == "crm":
                update_fields = {
                    "crm_actions": emp_data.get("crm_actions", {}),
                    "crm_actions_summary": emp_data.get("crm_actions_summary", ""),
                    "crm_behavior_pattern": emp_data.get("crm_behavior_pattern", ""),
                }
            elif file_type == "report":
                update_fields = {
                    "tendencies": emp_data.get("tendencies", ""),
                    "recommendations": emp_data.get("rec", ""),
                }
            
            update_fields["updated_at"] = datetime.now(timezone.utc)
            
            if existing:
                stmt = employee_scores.update().where(
                    employee_scores.c.id == existing[0]
                ).values(**update_fields)
                conn.execute(stmt)
            else:
                # INSERT — создаём новую запись
                insert_fields = {
                    "employee_name": employee_name,
                    "month": month,
                    "period": period,
                    "created_at": datetime.now(timezone.utc),
                    **update_fields,
                }
                conn.execute(employee_scores.insert().values(**insert_fields))
            
            count += 1
            
        # Проводим перекрёстную синхронизацию после записи файлов
        sync_db_data(conn, month)
    
    return count



@app.post("/api/upload")
async def upload_and_parse(files: List[UploadFile] = File(...)):
    """
    Загрузка и парсинг файлов. Автоматическое определение типа по содержимому.
    Принимает несколько файлов одновременно.
    """
    results = []
    
    for file in files:
        content = await file.read()
        filename = file.filename or "unknown"
        
        # 1. Определить тип
        file_type = detect_file_type(content, filename)
        
        if file_type == "unknown":
            results.append({
                "filename": filename,
                "type": "unknown",
                "status": "error",
                "message": f"Не удалось определить тип файла '{filename}'"
            })
            continue
        
        try:
            # 2. Парсинг
            if file_type == "quality":
                month, period, data = parse_quality_bytes(content, filename)
            elif file_type == "collections":
                month, period, data = parse_collections_bytes(content, filename)
            elif file_type == "crm":
                month, period, data = parse_crm_bytes(content, filename)
            elif file_type == "report":
                month, period, data = parse_report_pdf_bytes(content, filename)
            else:
                raise ValueError(f"Unknown type: {file_type}")
            
            # 3. Записать в БД
            employees_count = write_parsed_data_to_db(file_type, month, period, data)
            
            results.append({
                "filename": filename,
                "type": file_type,
                "month": month,
                "period": period,
                "employees_count": employees_count,
                "status": "ok"
            })
        except Exception as e:
            results.append({
                "filename": filename,
                "type": file_type,
                "status": "error",
                "message": str(e)
            })
    
    return {"results": results}


@app.get("/api/upload/status")
def upload_status():
    """
    Возвращает статус загруженных данных по периодам и по месяцам.
    """
    if not engine:
        return {"periods": [], "months": []}
    
    from sqlalchemy import func, exists, distinct
    
    with Session(engine) as session:
        # 1. Попериодный статус
        stmt = select(
            employee_scores.c.month,
            employee_scores.c.period,
        ).distinct().order_by(
            employee_scores.c.month.desc(),
            employee_scores.c.period.desc()
        )
        rows = session.execute(stmt).fetchall()
        
        periods = []
        for row in rows:
            month, period = row
            
            # Проверяем наличие данных каждого типа через EXISTS
            has_quality = session.execute(
                select(exists().where(
                    employee_scores.c.month == month,
                    employee_scores.c.period == period,
                    employee_scores.c.tqs > 0
                ))
            ).scalar()
            
            has_collections = session.execute(
                select(exists().where(
                    employee_scores.c.month == month,
                    employee_scores.c.period == period,
                    employee_scores.c.collected_amount > 0
                ))
            ).scalar()
            
            has_crm = session.execute(
                select(exists().where(
                    employee_scores.c.month == month,
                    employee_scores.c.period == period,
                    employee_scores.c.crm_actions_summary != '',
                    employee_scores.c.crm_actions_summary.is_not(None)
                ))
            ).scalar()
            
            has_report = session.execute(
                select(exists().where(
                    employee_scores.c.month == month,
                    employee_scores.c.period == period,
                    employee_scores.c.tendencies != '',
                    employee_scores.c.tendencies.is_not(None)
                ))
            ).scalar()
            
            emp_count = session.execute(
                select(func.count(distinct(employee_scores.c.employee_name))).where(
                    employee_scores.c.month == month,
                    employee_scores.c.period == period
                )
            ).scalar() or 0
            
            periods.append({
                "month": month,
                "period": period,
                "has_quality": bool(has_quality),
                "has_collections": bool(has_collections),
                "has_crm": bool(has_crm),
                "has_report": bool(has_report),
                "employees_count": emp_count,
            })
            
        # 2. Помесячный агрегированный статус
        month_stmt = select(employee_scores.c.month).distinct()
        months_rows = session.execute(month_stmt).fetchall()
        
        months_status = []
        for m_row in months_rows:
            m = m_row[0]
            
            has_quality = session.execute(
                select(exists().where(
                    employee_scores.c.month == m,
                    employee_scores.c.tqs > 0
                ))
            ).scalar()
            
            has_collections = session.execute(
                select(exists().where(
                    employee_scores.c.month == m,
                    employee_scores.c.collected_amount > 0
                ))
            ).scalar()
            
            has_crm = session.execute(
                select(exists().where(
                    employee_scores.c.month == m,
                    employee_scores.c.crm_actions_summary != '',
                    employee_scores.c.crm_actions_summary.is_not(None)
                ))
            ).scalar()
            
            has_report = session.execute(
                select(exists().where(
                    employee_scores.c.month == m,
                    employee_scores.c.tendencies != '',
                    employee_scores.c.tendencies.is_not(None)
                ))
            ).scalar()
            
            emp_count = session.execute(
                select(func.count(distinct(employee_scores.c.employee_name))).where(
                    employee_scores.c.month == m
                )
            ).scalar() or 0
            
            months_status.append({
                "month": m,
                "has_quality": bool(has_quality),
                "has_collections": bool(has_collections),
                "has_crm": bool(has_crm),
                "has_report": bool(has_report),
                "employees_count": emp_count,
            })
            
        return {"periods": periods, "months": months_status}


@app.get("/api/metrics/months")
def get_available_months():
    """Возвращает список доступных месяцев и их периодов."""
    if not engine:
        return {"months": []}
    
    with Session(engine) as session:
        stmt = select(
            employee_scores.c.month,
            employee_scores.c.period,
        ).distinct().order_by(
            employee_scores.c.month,
            employee_scores.c.period
        )
        rows = session.execute(stmt).fetchall()
        
        months_dict = {}
        for month, period in rows:
            if month not in months_dict:
                months_dict[month] = []
            months_dict[month].append(period)
        
        # Сортировка по календарному порядку
        MONTH_ORDER = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        sorted_months = sorted(
            months_dict.items(),
            key=lambda item: (
                MONTH_ORDER.index(item[0].split(' ')[0]) if item[0].split(' ')[0] in MONTH_ORDER else 999,
            ),
            reverse=True
        )
        
        return {
            "months": [
                {"month": m, "periods": sorted(ps)}
                for m, ps in sorted_months
            ]
        }


@app.delete("/api/data/{month}/{period}")
def delete_period_data(month: str, period: str):
    """Удаление данных за конкретный период (для перезагрузки)."""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    with engine.begin() as conn:
        stmt = employee_scores.delete().where(
            employee_scores.c.month == month,
            employee_scores.c.period == period,
        )
        result = conn.execute(stmt)
        return {"status": "ok", "deleted_rows": result.rowcount}


@app.get("/api/dashboard-data")
def get_dashboard_data():
    """
    Возвращает ВСЕ данные в формате DASHBOARD_DATA.
    Формат: { "ИмяСотрудника": { "months": { "Месяц": { "periods": [...] } } } }
    """
    if not engine:
        return {}
    
    with Session(engine) as session:
        stmt = select(employee_scores).order_by(
            employee_scores.c.employee_name,
            employee_scores.c.month,
            employee_scores.c.period
        )
        rows = session.execute(stmt).fetchall()
        
        result = {}
        for row in rows:
            name = row.employee_name
            month = row.month
            period = row.period
            
            if name not in result:
                result[name] = {"months": {}}
            if month not in result[name]["months"]:
                result[name]["months"][month] = {"periods": []}
            
            period_data = {
                "period": period,
                "tqs": row.tqs or 0.0,
                "aht": row.aht or "N/A",
                "svp": row.svp_scores or {k: 1.0 for k in SVP_KEYS},
                "raw_scores": row.raw_scores or {k: [] for k in SVP_KEYS},
                "tendencies": row.tendencies or "",
                "rec": row.recommendations or "",
                "activity_count": row.activity_count or 0,
                "collected_amount": row.collected_amount or 0.0,
                "collected_count": row.collected_count or 0,
                "collection_rate": row.collection_rate or 0.0,
                "plan_fulfillment": row.plan_fulfillment or 0.0,
                "crm_actions": row.crm_actions or {},
                "crm_actions_summary": row.crm_actions_summary or "",
                "crm_behavior_pattern": row.crm_behavior_pattern or "",
            }
            
            result[name]["months"][month]["periods"].append(period_data)
        
        return result


@app.get("/api/data-mode")
def get_data_mode():
    """Get current data mode."""
    return {"mode": DATA_MODE, "description": "API Mode - data from PostgreSQL"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
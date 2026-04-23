import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import create_engine


DATABASE_URL = os.getenv("DATABASE_URL", "")

app = FastAPI(title="Dashboard SC Backend", version="0.1.0")
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None


def check_db() -> tuple[bool, str]:
    if engine is None:
        return False, "not_configured"
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
        return True, "connected"
    except SQLAlchemyError:
        return False, "error"


@app.get("/api/health")
def health() -> JSONResponse:
    ok, db_state = check_db()
    return JSONResponse(
        {
            "status": "healthy",
            "database": db_state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "dashboard-sc-backend",
        },
        status_code=200 if ok or db_state == "not_configured" else 503,
    )


@app.get("/api/employees")
def employees() -> dict:
    # Safe default to keep frontend/API integration stable while backend grows.
    return {"items": [], "total": 0}


@app.get("/api/history/{employee_name}")
def history(employee_name: str) -> dict:
    return {"employee": employee_name, "history": []}


@app.get("/api/trends/forecast")
def forecast() -> dict:
    return {"period": "current", "forecast": [], "model": "placeholder"}

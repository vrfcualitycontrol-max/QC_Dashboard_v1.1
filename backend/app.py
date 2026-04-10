#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QC Dashboard Backend - FastAPI Application
Сервис для аналитики качества работы QC отдела
"""

import os
import json
import statistics
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import pdfplumber
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ============================================
# Конфигурация
# ============================================

BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# База данных
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://qc_user:qc_password@postgres:5432/qc_dashboard"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================
# Модели БД
# ============================================

class EmployeeScore(Base):
    """Оценки сотрудника за период"""
    __tablename__ = "employee_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String, nullable=False, index=True)
    period = Column(String, nullable=False, index=True)
    tqs = Column(Float, nullable=False)
    aht = Column(Float, default=0.0)
    activity_count = Column(Integer, default=0)
    scores = Column(JSON, nullable=True)  # {"greeting": 0.85, "ethics": 0.90, ...}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PDFRecommendation(Base):
    """Рекомендации из PDF отчетов"""
    __tablename__ = "pdf_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String, nullable=False, index=True)
    priority0 = Column(Text, nullable=True)
    trends = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ParsingLog(Base):
    """Лог парсинга файлов"""
    __tablename__ = "parsing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # "xlsx" или "pdf"
    status = Column(String, nullable=False)  # "success", "error", "warning"
    message = Column(Text, nullable=True)
    parsed_at = Column(DateTime, default=datetime.utcnow)


class TQSAHTCorrelation(Base):
    """Корреляция TQS и AHT"""
    __tablename__ = "tqs_aht_correlation"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String, nullable=False, index=True)
    period = Column(String, nullable=False)
    tqs = Column(Float, nullable=False)
    aht = Column(Float, nullable=False)
    correlation_coefficient = Column(Float, nullable=True)
    calculated_at = Column(DateTime, default=datetime.utcnow)


# Создание таблиц
Base.metadata.create_all(bind=engine)

# ============================================
# Pydantic схемы
# ============================================

class EmployeeStats(BaseModel):
    """Статистика сотрудника"""
    employee_name: str
    aggregated_tqs: float
    aggregated_aht: float
    sum_activity: int
    aggregated_scores: Dict[str, float]
    periods_count: int


class LeaderboardEntry(BaseModel):
    """Запись в рейтинге"""
    rank: int
    employee_name: str
    tqs: float
    aht: float
    activity_count: int
    trend: Optional[str] = None  # "up", "down", "stable"


class CorrelationResult(BaseModel):
    """Результат корреляции"""
    employee_name: str
    correlation: float
    interpretation: str
    data_points: int


class PeriodComparison(BaseModel):
    """Сравнение периодов"""
    employee_name: str
    period1: str
    period2: str
    tqs_change: float
    aht_change: float
    scores_change: Dict[str, float]


# ============================================
# FastAPI приложение
# ============================================

app = FastAPI(
    title="QC Dashboard API",
    description="API для аналитики качества работы QC отдела Soft Collection",
    version="1.2.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Утилиты
# ============================================

CRITERIA_COLUMNS = {
    "greeting": "Приветствие и прощание,\nОрганизация,  Идентификации\n5%",
    "ethics": "Этика общения\n5%",
    "crm": "Выбор корректного результата звонка в системе\n10%",
    "legend": "Легендирование\n15%",
    "informing": "Предоставление информации о задолженности\n10%",
    "argumentation": "Аргументация\n20%",
    "manipulation": "Манипуляция\n10%",
    "requirements": "Выставление требований - Уточнение способа оплаты\n15%",
    "summary": "Подведение итогов\n10%"
}

EMPLOYEE_COLUMN = "ФИО Сотрудника"
RESULT_COLUMN = "Итоги"
DURATION_COLUMN = "Длительность"


def get_db():
    """Получение сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parse_score(value: Any) -> float:
    """Конвертирует значение оценки в float"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    str_value = str(value).strip()
    if "%" in str_value:
        try:
            return float(str_value.replace("%", "").strip()) / 100
        except ValueError:
            return 0.0
    try:
        return float(str_value.replace(",", "."))
    except ValueError:
        return 0.0


def parse_duration(value) -> float:
    """Конвертирует длительность звонка в минуты"""
    if value is None:
        return 0.0
    try:
        return float(value.hour + value.minute / 60.0 + value.second / 3600.0)
    except (AttributeError, TypeError):
        return 0.0


def extract_period_from_filename(filename: str) -> Optional[str]:
    """Извлекает период из имени файла XLSX"""
    import re
    pattern = r'(\d{2})\.(\d{2})\.(\d{4})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})'
    match = re.search(pattern, filename)
    if match:
        day_start = match.group(1)
        month_num = match.group(2)
        year = match.group(3)
        day_end = match.group(4)
        months = {
            "01": "Янв", "02": "Фев", "03": "Мар", "04": "Апр",
            "05": "Май", "06": "Июн", "07": "Июл", "08": "Авг",
            "09": "Сен", "10": "Окт", "11": "Ноя", "12": "Дек"
        }
        month_name = months.get(month_num, month_num)
        return f"{day_start}-{day_end} {month_name} {year}"
    return None


# ============================================
# API Эндпоинты
# ============================================

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "QC Dashboard API",
        "version": "1.2.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": "disconnected", "error": str(e)}


@app.get("/api/employees", response_model=List[EmployeeStats])
async def get_employees():
    """Получить статистику всех сотрудников"""
    db = SessionLocal()
    try:
        employees = db.query(EmployeeScore.employee_name).distinct().all()
        result = []
        
        for (emp_name,) in employees:
            scores = db.query(EmployeeScore).filter(
                EmployeeScore.employee_name == emp_name
            ).all()
            
            if not scores:
                continue
            
            aggregated_tqs = statistics.mean([s.tqs for s in scores])
            aggregated_aht = statistics.mean([s.aht for s in scores if s.aht > 0]) if any(s.aht > 0 for s in scores) else 0
            sum_activity = sum([s.activity_count for s in scores])
            
            # Агрегация оценок по критериям
            all_scores = {k: [] for k in CRITERIA_COLUMNS.keys()}
            for s in scores:
                if s.scores:
                    for key, val in s.scores.items():
                        if key in all_scores:
                            all_scores[key].append(val)
            
            aggregated_scores = {
                key: statistics.mean(vals) if vals else 0
                for key, vals in all_scores.items()
            }
            
            result.append(EmployeeStats(
                employee_name=emp_name,
                aggregated_tqs=round(aggregated_tqs, 4),
                aggregated_aht=round(aggregated_aht, 2),
                sum_activity=sum_activity,
                aggregated_scores={k: round(v, 4) for k, v in aggregated_scores.items()},
                periods_count=len(scores)
            ))
        
        return result
    finally:
        db.close()


@app.get("/api/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    """Рейтинг сотрудников (leaderboard)"""
    db = SessionLocal()
    try:
        employees = db.query(EmployeeScore.employee_name).distinct().all()
        leaderboard = []
        
        for (emp_name,) in employees:
            scores = db.query(EmployeeScore).filter(
                EmployeeScore.employee_name == emp_name
            ).order_by(EmployeeScore.period).all()
            
            if not scores:
                continue
            
            avg_tqs = statistics.mean([s.tqs for s in scores])
            avg_aht = statistics.mean([s.aht for s in scores if s.aht > 0]) if any(s.aht > 0 for s in scores) else 0
            total_activity = sum([s.activity_count for s in scores])
            
            # Определение тренда
            if len(scores) >= 2:
                recent_tqs = [s.tqs for s in scores[-3:]]
                older_tqs = [s.tqs for s in scores[:3]]
                trend_value = statistics.mean(recent_tqs) - statistics.mean(older_tqs)
                
                if trend_value > 0.05:
                    trend = "up"
                elif trend_value < -0.05:
                    trend = "down"
                else:
                    trend = "stable"
            else:
                trend = None
            
            leaderboard.append({
                "employee_name": emp_name,
                "tqs": round(avg_tqs, 4),
                "aht": round(avg_aht, 2),
                "activity_count": total_activity,
                "trend": trend
            })
        
        # Сортировка по TQS (убывание)
        leaderboard.sort(key=lambda x: x["tqs"], reverse=True)
        
        # Добавление ранга
        result = []
        for idx, entry in enumerate(leaderboard, 1):
            result.append(LeaderboardEntry(
                rank=idx,
                **entry
            ))
        
        return result
    finally:
        db.close()


@app.get("/api/correlation/{employee_name}", response_model=CorrelationResult)
async def get_correlation(employee_name: str):
    """Корреляция TQS и AHT для сотрудника"""
    db = SessionLocal()
    try:
        scores = db.query(EmployeeScore).filter(
            EmployeeScore.employee_name == employee_name,
            EmployeeScore.aht > 0
        ).all()
        
        if len(scores) < 2:
            raise HTTPException(status_code=404, detail="Недостаточно данных для корреляции")
        
        tqs_values = [s.tqs for s in scores]
        aht_values = [s.aht for s in scores]
        
        # Расчёт коэффициента корреляции Пирсона
        n = len(tqs_values)
        mean_tqs = statistics.mean(tqs_values)
        mean_aht = statistics.mean(aht_values)
        
        numerator = sum((t - mean_tqs) * (a - mean_aht) for t, a in zip(tqs_values, aht_values))
        denom_tqs = sum((t - mean_tqs) ** 2 for t in tqs_values) ** 0.5
        denom_aht = sum((a - mean_aht) ** 2 for a in aht_values) ** 0.5
        
        if denom_tqs == 0 or denom_aht == 0:
            correlation = 0.0
        else:
            correlation = numerator / (denom_tqs * denom_aht)
        
        # Интерпретация
        if abs(correlation) < 0.3:
            interpretation = "Слабая корреляция"
        elif abs(correlation) < 0.7:
            interpretation = "Умеренная корреляция"
        else:
            interpretation = "Сильная корреляция"
        
        direction = "положительная" if correlation > 0 else "отрицательная"
        
        # Сохранение в БД
        correlation_record = TQSAHTCorrelation(
            employee_name=employee_name,
            period="aggregated",
            tqs=mean_tqs,
            aht=mean_aht,
            correlation_coefficient=round(correlation, 4)
        )
        db.add(correlation_record)
        db.commit()
        
        return CorrelationResult(
            employee_name=employee_name,
            correlation=round(correlation, 4),
            interpretation=f"{interpretation} ({direction})",
            data_points=n
        )
    finally:
        db.close()


@app.get("/api/trends")
async def get_trends():
    """Общие тренды по всем сотрудникам"""
    db = SessionLocal()
    try:
        # Группировка по периодам
        periods = db.query(EmployeeScore.period).distinct().order_by(EmployeeScore.period).all()

        trends = []
        for (period,) in periods:
            scores = db.query(EmployeeScore).filter(EmployeeScore.period == period).all()

            if not scores:
                continue

            avg_tqs = statistics.mean([s.tqs for s in scores])
            avg_aht = statistics.mean([s.aht for s in scores if s.aht > 0]) if any(s.aht > 0 for s in scores) else 0
            total_activity = sum([s.activity_count for s in scores])

            trends.append({
                "period": period,
                "avg_tqs": round(avg_tqs, 4),
                "avg_aht": round(avg_aht, 2),
                "total_activity": total_activity,
                "employees_count": len(scores)
            })

        return trends
    finally:
        db.close()


# ============================================
# НОВЫЕ ЭНДПОИНТЫ: История, Сравнение, Прогнозирование
# ============================================

@app.get("/api/history/{employee_name}")
async def get_employee_history(employee_name: str, mode: str = "detailed"):
    """
    Полная история показателей сотрудника по всем периодам
    mode: "detailed" — все периоды; "summary" — агрегация по месяцам
    Возвращает точные данные: TQS, AHT, оценки по критериям, активность
    """
    db = SessionLocal()
    try:
        scores = db.query(EmployeeScore).filter(
            EmployeeScore.employee_name == employee_name
        ).all()

        if not scores:
            raise HTTPException(status_code=404, detail="История не найдена")

        if mode == "summary":
            # Агрегация по месяцам с дедупликацией
            import re
            month_groups = {}
            for s in scores:
                match = re.match(r'\d{2}-\d{2}\s+(\w+\s+\d{4})', s.period)
                month_key = match.group(1) if match else s.period
                
                if month_key not in month_groups:
                    month_groups[month_key] = []
                month_groups[month_key].append(s)
            
            history = []
            for month_key in _sort_periods_chronological(list(month_groups.keys())):
                group = month_groups[month_key]
                
                # Дедупликация: уникальные периоды + TQS
                seen = set()
                unique = []
                for s in group:
                    key = (s.period, round(s.tqs, 4))
                    if key not in seen:
                        seen.add(key)
                        unique.append(s)
                
                entry = {
                    "period": month_key,
                    "tqs": round(statistics.mean([s.tqs for s in unique]), 4),
                    "aht": round(statistics.mean([s.aht for s in unique if s.aht > 0]), 2) if any(s.aht > 0 for s in unique) else None,
                    "activity_count": sum([s.activity_count for s in unique]),
                    "scores": {k: round(statistics.mean([s.scores.get(k, 0) for s in unique]), 4) for k in (unique[0].scores or {}).keys()},
                    "created_at": max(s.created_at for s in unique).isoformat(),
                    "mode": "summary"
                }
                history.append(entry)
        else:
            # Детальный режим — уникальные периоды (без дублей)
            seen = set()
            unique_scores = []
            for s in scores:
                key = (s.period, s.tqs)
                if key not in seen:
                    seen.add(key)
                    unique_scores.append(s)
            
            # Сортируем периоды
            unique_scores.sort(key=lambda s: _sort_periods_chronological([s.period]), reverse=True)
            # Простая сортировка:
            import re
            month_order = {'Янв': 1, 'Фев': 2, 'Мар': 3, 'Апр': 4, 'Май': 5, 'Июн': 6, 'Июл': 7, 'Авг': 8, 'Сен': 9, 'Окт': 10, 'Ноя': 11, 'Дек': 12}
            def period_key(s):
                match = re.match(r'(\d{2})-(\d{2})\s+(\w+)\s+(\d{4})', s.period)
                if match:
                    return (int(match.group(4)), month_order.get(match.group(3), 0), int(match.group(2)))
                return (0, 0, 0)
            unique_scores.sort(key=period_key, reverse=True)
            
            history = []
            for s in unique_scores:
                entry = {
                    "period": s.period,
                    "tqs": round(s.tqs, 4),
                    "aht": round(s.aht, 2) if s.aht > 0 else None,
                    "activity_count": s.activity_count,
                    "scores": {k: round(v, 4) for k, v in (s.scores or {}).items()},
                    "created_at": s.created_at.isoformat(),
                    "mode": "detailed"
                }
                history.append(entry)

        return {
            "employee_name": employee_name,
            "periods_count": len(history),
            "history": history
        }
    finally:
        db.close()


@app.get("/api/compare/{employee_name}")
async def compare_periods(employee_name: str, period1: str = None, period2: str = None):
    """
    Детальное сравнение двух периодов с точными расчётами
    Возвращает дельту по каждому показателю + интерпретацию
    """
    db = SessionLocal()
    try:
        scores = db.query(EmployeeScore).filter(
            EmployeeScore.employee_name == employee_name
        ).order_by(EmployeeScore.period).all()

        if len(scores) < 2:
            raise HTTPException(status_code=404, detail="Недостаточно данных для сравнения")

        # Если периоды не указаны, берём первый и последний
        if not period1 or not period2:
            period1 = scores[0].period
            period2 = scores[-1].period

        score1 = next((s for s in scores if s.period == period1), None)
        score2 = next((s for s in scores if s.period == period2), None)

        if not score1 or not score2:
            raise HTTPException(status_code=404, detail="Периоды не найдены")

        # Точные расчёты изменений
        tqs_delta = round((score2.tqs - score1.tqs) * 100, 2)
        aht_delta = round(score2.aht - score1.aht, 2) if score1.aht > 0 and score2.aht > 0 else None
        activity_delta = score2.activity_count - score1.activity_count

        # Изменения по критериям
        scores_delta = {}
        if score1.scores and score2.scores:
            for key in score1.scores.keys():
                val1 = score1.scores.get(key, 0)
                val2 = score2.scores.get(key, 0)
                delta_pct = round((val2 - val1) * 100, 2)
                scores_delta[key] = {
                    "period1": round(val1 * 100, 2),
                    "period2": round(val2 * 100, 2),
                    "delta_pct": delta_pct,
                    "trend": "up" if delta_pct > 0 else ("down" if delta_pct < 0 else "stable")
                }

        # Интерпретация
        tqs_interpretation = _interpret_tqs_change(tqs_delta)
        aht_interpretation = _interpret_aht_change(aht_delta) if aht_delta is not None else None

        return {
            "employee_name": employee_name,
            "period1": period1,
            "period2": period2,
            "tqs": {
                "period1": round(score1.tqs, 4),
                "period2": round(score2.tqs, 4),
                "delta_pct": tqs_delta,
                "interpretation": tqs_interpretation
            },
            "aht": {
                "period1": round(score1.aht, 2) if score1.aht > 0 else None,
                "period2": round(score2.aht, 2) if score2.aht > 0 else None,
                "delta_min": aht_delta,
                "interpretation": aht_interpretation
            },
            "activity": {
                "period1": score1.activity_count,
                "period2": score2.activity_count,
                "delta": activity_delta
            },
            "scores_delta": scores_delta
        }
    finally:
        db.close()


@app.get("/api/trends/forecast")
async def get_trends_with_forecast(employee_name: str = None):
    """
    Тренды с прогнозированием на основе экспоненциального сглаживания Хольта
    Если employee_name указан — тренды сотрудника, иначе — общие по команде
    """
    db = SessionLocal()
    try:
        if employee_name:
            scores = db.query(EmployeeScore).filter(
                EmployeeScore.employee_name == employee_name
            ).all()
        else:
            # Агрегация по всем сотрудникам за каждый период
            periods = db.query(EmployeeScore.period).distinct().all()
            scores = []
            for (period,) in periods:
                period_scores = db.query(EmployeeScore).filter(EmployeeScore.period == period).all()
                if period_scores:
                    scores.append(EmployeeScore(
                        employee_name="team",
                        period=period,
                        tqs=statistics.mean([s.tqs for s in period_scores]),
                        aht=statistics.mean([s.aht for s in period_scores if s.aht > 0]) if any(s.aht > 0 for s in period_scores) else 0,
                        activity_count=sum([s.activity_count for s in period_scores])
                    ))

        if len(scores) < 3:
            return {"error": "Недостаточно данных для прогнозирования (минимум 3 периода)"}

        # Сортировка периодов хронологически
        import re
        month_order = {'Янв': 1, 'Фев': 2, 'Мар': 3, 'Апр': 4, 'Май': 5, 'Июн': 6, 'Июл': 7, 'Авг': 8, 'Сен': 9, 'Окт': 10, 'Ноя': 11, 'Дек': 12}
        def period_key(s):
            match = re.match(r'(\d{2})-(\d{2})\s+(\w+)\s+(\d{4})', s.period)
            if match:
                return (int(match.group(4)), month_order.get(match.group(3), 0), int(match.group(2)))
            return (0, 0, 0)
        scores.sort(key=period_key)

        tqs_values = [s.tqs for s in scores]
        aht_values = [s.aht for s in scores if s.aht > 0]

        # Экспоненциальное сглаживание Хольта для TQS
        tqs_holt = _holt_exponential_smoothing(tqs_values, alpha=0.5, beta=0.3, steps=3)

        # Экспоненциальное сглаживание Хольта для AHT (если есть данные)
        aht_holt = None
        if len(aht_values) >= 3:
            aht_holt = _holt_exponential_smoothing(aht_values, alpha=0.5, beta=0.3, steps=3)

        # Формируем исторические точки
        historical = []
        for i, s in enumerate(scores):
            fitted_tqs = tqs_holt["fitted"][i] if i < len(tqs_holt["fitted"]) else s.tqs
            historical.append({
                "period": s.period,
                "tqs": round(s.tqs, 4),
                "tqs_fitted": round(fitted_tqs, 4),
                "aht": round(s.aht, 2) if s.aht > 0 else None,
                "activity_count": s.activity_count
            })

        # Интерпретация для бизнеса
        forecast_values = tqs_holt["forecast"]
        current_tqs = historical[-1]["tqs"] if historical else 0
        forecast_avg = statistics.mean(forecast_values)
        
        # Прогноз изменения
        change_pct = round((forecast_avg - current_tqs) * 100, 2)
        if change_pct > 2:
            business_outlook = "📈 Ожидается улучшение качества"
        elif change_pct > -2:
            business_outlook = "➡️ Качество останется стабильным"
        else:
            business_outlook = "📉 Ожидается снижение качества — требуется вмешательство"
        
        # Рекомендации
        recommendations = []
        if tqs_holt.get("r_squared", 0) < 0.5:
            recommendations.append("⚠️ Низкая точность модели — данные нестабильны, прогноз ненадёжен")
        if forecast_avg < 0.65:
            recommendations.append("🔴 Прогноз ниже 65% — критический уровень, нужен срочный разбор ошибок")
        elif forecast_avg < 0.75:
            recommendations.append("🟡 Прогноз 65-75% — провести обучение по проблемным зонам")
        else:
            recommendations.append("🟢 Прогноз выше 75% — поддерживать текущий уровень")
        
        if tqs_holt["trend"] == "нисходящий":
            recommendations.append("📉 Тренд нисходящий — выявить и устранить причину деградации")
        elif tqs_holt["trend"] == "восходящий":
            recommendations.append("📈 Тренд восходящий — поощрить команду, зафиксировать лучшие практики")

        return {
            "employee_name": employee_name or "team",
            "historical": historical,
            "forecast_periods": 3,
            "method": "Holt's Exponential Smoothing",
            "current_tqs": round(current_tqs, 4),
            "forecast_avg_tqs": round(forecast_avg, 4),
            "change_pct": change_pct,
            "business_outlook": business_outlook,
            "recommendations": recommendations,
            "tqs_forecast": {
                "values": [round(v, 4) for v in tqs_holt["forecast"]],
                "trend": tqs_holt["trend_direction"],
                "level": tqs_holt["level"],
                "trend_coefficient": tqs_holt["trend"],
                "r_squared": tqs_holt.get("r_squared", 0),
                "r_squared_label": tqs_holt.get("r_squared_label", "Недоступно"),
                "interpretation": f"Тренд TQS: {tqs_holt['trend_direction']}"
            },
            "aht_forecast": {
                "values": [round(v, 2) for v in aht_holt["forecast"]],
                "trend": aht_holt["trend_direction"]
            } if aht_holt else None
        }
    finally:
        db.close()


@app.get("/api/leaderboard/best-worst")
async def get_best_worst_employees(limit: int = 5):
    """
    Топ-5 лучших и топ-5 худших сотрудников по TQS
    Автоматически объединяет дубликаты имён (fuzzy match)
    """
    db = SessionLocal()
    try:
        from difflib import SequenceMatcher
        
        def names_similar(a: str, b: str, threshold: float = 0.80) -> bool:
            """Проверка схожести имён (для обнаружения опечаток)"""
            if a == b:
                return True
            parts_a = a.split()
            parts_b = b.split()
            if len(parts_a) != len(parts_b):
                return False
            # Первая часть (фамилия) должна совпадать полностью
            if parts_a[0].lower() != parts_b[0].lower():
                return False
            # Остальные части — проверяем схожесть
            similarities = [SequenceMatcher(None, pa.lower(), pb.lower()).ratio() for pa, pb in zip(parts_a, parts_b)]
            # Среднее по всем частям >= threshold
            return sum(similarities) / len(similarities) >= threshold
        
        # Получаем всех уникальных сотрудников
        all_employees = db.query(EmployeeScore.employee_name).distinct().all()
        all_names = [e[0] for e in all_employees]
        
        # Группируем похожие имена
        groups = []  # list of lists of similar names
        used = set()
        for name in all_names:
            if name in used:
                continue
            group = [name]
            used.add(name)
            for other in all_names:
                if other not in used and names_similar(name, other):
                    group.append(other)
                    used.add(other)
            groups.append(group)
        
        leaderboard = []
        for group in groups:
            # Собираем все записи для группы похожих имён
            all_scores = []
            for emp_name in group:
                scores = db.query(EmployeeScore).filter(EmployeeScore.employee_name == emp_name).all()
                all_scores.extend(scores)
            
            if not all_scores:
                continue
            
            avg_tqs = round(statistics.mean([s.tqs for s in all_scores]), 4)
            avg_aht = round(statistics.mean([s.aht for s in all_scores if s.aht > 0]), 2) if any(s.aht > 0 for s in all_scores) else 0
            total_activity = sum([s.activity_count for s in all_scores])
            
            # Используем имя с наибольшим количеством записей как каноническое
            canonical_name = max(group, key=lambda n: len([s for s in all_scores if s.employee_name == n]))
            
            leaderboard.append({
                "employee_name": canonical_name,
                "tqs": avg_tqs,
                "aht": avg_aht,
                "activity_count": total_activity
            })

        leaderboard.sort(key=lambda x: x["tqs"], reverse=True)

        return {
            "best": leaderboard[:limit],
            "worst": leaderboard[-limit:][::-1]
        }
    finally:
        db.close()


# ============================================
# Вспомогательные функции для расчётов
# ============================================

def _sort_periods_chronological(periods_list):
    """
    Сортировка периодов: новые первыми
    Формат: "01-05 Апр 2026", "23-31 Мар 2026"
    """
    import re
    month_order = {
        'Янв': 1, 'Фев': 2, 'Мар': 3, 'Апр': 4,
        'Май': 5, 'Июн': 6, 'Июл': 7, 'Авг': 8,
        'Сен': 9, 'Окт': 10, 'Ноя': 11, 'Дек': 12
    }
    
    def period_sort_key(period_str):
        # Извлекаем: день_начала, месяц, год, день_конца
        match = re.match(r'(\d{2})-(\d{2})\s+(\w+)\s+(\d{4})', period_str)
        if match:
            day_start = int(match.group(1))
            day_end = int(match.group(2))
            month = month_order.get(match.group(3), 0)
            year = int(match.group(4))
            return (year, month, day_end)  # Сортировка по убыванию
        return (0, 0, 0)
    
    return sorted(periods_list, key=period_sort_key, reverse=True)


def _interpret_tqs_change(delta_pct: float) -> str:
    """Интерпретация изменения TQS"""
    if delta_pct > 10:
        return "📈 Значительное улучшение"
    elif delta_pct > 3:
        return "↗️ Умеренное улучшение"
    elif delta_pct > 0:
        return "➡️ Небольшой рост"
    elif delta_pct == 0:
        return "➡️ Без изменений"
    elif delta_pct > -3:
        return "➡️ Небольшое снижение"
    elif delta_pct > -10:
        return "↘️ Умеренное снижение"
    else:
        return "📉 Значительное ухудшение"


def _interpret_aht_change(delta_min: float) -> str:
    """Интерпретация изменения AHT (снижение = хорошо)"""
    if delta_min < -1:
        return "📈 Значительное улучшение (время снизилось)"
    elif delta_min < -0.3:
        return "↗️ Умеренное улучшение"
    elif delta_min < 0:
        return "➡️ Небольшое улучшение"
    elif delta_min == 0:
        return "➡️ Без изменений"
    elif delta_min < 0.3:
        return "➡️ Небольшое ухудшение"
    elif delta_min < 1:
        return "↘️ Умеренное ухудшение"
    else:
        return "📉 Значительное ухудшение (время выросло)"


def _linear_regression(x: list, y: list) -> tuple:
    """
    Расчёт линейной регрессии (метод наименьших квадратов)
    Возвращает (slope, intercept)
    """
    n = len(x)
    if n < 2:
        return 0, 0

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)

    denominator = n * sum_x2 - sum_x ** 2
    if denominator == 0:
        return 0, sum_y / n if n > 0 else 0

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n

    return slope, intercept


def _holt_exponential_smoothing(data: list, alpha: float = 0.5, beta: float = 0.3, steps: int = 3) -> dict:
    """
    Метод экспоненциального сглаживания Хольта (двойное)
    alpha: сглаживание уровня (0-1)
    beta: сглаживание тренда (0-1)
    steps: количество шагов прогноза
    Возвращает: forecast_values, level, trend, fitted_values, r_squared
    """
    if len(data) < 3:
        return {"forecast": [], "level": 0, "trend": 0, "fitted": [], "r_squared": 0, "r_squared_label": "Недостаточно данных"}
    
    # Инициализация
    L = data[0]
    T = data[1] - data[0] if len(data) > 1 else 0
    
    fitted = [L]
    
    # Рекурсивное сглаживание
    for t in range(1, len(data)):
        L_prev, T_prev = L, T
        L = alpha * data[t] + (1 - alpha) * (L_prev + T_prev)
        T = beta * (L - L_prev) + (1 - beta) * T_prev
        fitted.append(L + T)
    
    # Прогноз
    forecast = [L + (h + 1) * T for h in range(steps)]
    
    # Расчёт R² (коэффициент детерминации)
    mean_actual = statistics.mean(data)
    ss_tot = sum((y - mean_actual) ** 2 for y in data)
    ss_res = sum((y - f) ** 2 for y, f in zip(data, fitted))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Интерпретация R²
    if r_squared >= 0.9:
        r_label = "Отличная точность модели"
    elif r_squared >= 0.7:
        r_label = "Хорошая точность модели"
    elif r_squared >= 0.5:
        r_label = "Удовлетворительная точность"
    elif r_squared >= 0.3:
        r_label = "Слабая точность — прогноз с осторожностью"
    else:
        r_label = "Низкая точность — высокий риск прогноза"
    
    # Интерпретация тренда
    if T > 0.02:
        trend_direction = "восходящий"
    elif T > 0.005:
        trend_direction = "слабовосходящий"
    elif T > -0.005:
        trend_direction = "стабильный"
    elif T > -0.02:
        trend_direction = "слабонисходящий"
    else:
        trend_direction = "нисходящий"
    
    return {
        "forecast": forecast,
        "level": round(L, 6),
        "trend": round(T, 6),
        "fitted": [round(v, 6) for v in fitted],
        "r_squared": round(r_squared, 4),
        "r_squared_label": r_label,
        "trend_direction": trend_direction,
        "alpha": alpha,
        "beta": beta
    }


@app.post("/api/upload/xlsx")
async def upload_xlsx(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Загрузка XLSX файла и парсинг"""
    db = SessionLocal()
    try:
        # Валидация
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="Только .xlsx файлы")
        
        # Сохранение файла
        REPORTS_DIR.mkdir(exist_ok=True)
        file_path = REPORTS_DIR / file.filename
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Логирование
        log = ParsingLog(
            filename=file.filename,
            file_type="xlsx",
            status="processing",
            message="Начат парсинг"
        )
        db.add(log)
        db.commit()
        
        # Парсинг в фоне
        if background_tasks:
            background_tasks.add_task(parse_xlsx_file, file_path, db)
        else:
            parse_xlsx_file(file_path, db)
        
        return {
            "status": "success",
            "message": f"Файл {file.filename} загружен и обрабатывается",
            "filename": file.filename
        }
    except Exception as e:
        log = ParsingLog(
            filename=file.filename if file.filename else "unknown",
            file_type="xlsx",
            status="error",
            message=str(e)
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/upload/pdf")
async def upload_pdf(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Загрузка PDF файла и парсинг"""
    db = SessionLocal()
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Только .pdf файлы")
        
        REPORTS_DIR.mkdir(exist_ok=True)
        file_path = REPORTS_DIR / file.filename
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        log = ParsingLog(
            filename=file.filename,
            file_type="pdf",
            status="processing",
            message="Начат парсинг"
        )
        db.add(log)
        db.commit()
        
        if background_tasks:
            background_tasks.add_task(parse_pdf_file, file_path, db)
        else:
            parse_pdf_file(file_path, db)
        
        return {
            "status": "success",
            "message": f"Файл {file.filename} загружен и обрабатывается",
            "filename": file.filename
        }
    except Exception as e:
        log = ParsingLog(
            filename=file.filename if file.filename else "unknown",
            file_type="pdf",
            status="error",
            message=str(e)
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/logs")
async def get_logs(limit: int = 50):
    """Получить логи парсинга"""
    db = SessionLocal()
    try:
        logs = db.query(ParsingLog).order_by(
            ParsingLog.parsed_at.desc()
        ).limit(limit).all()
        
        return [
            {
                "id": log.id,
                "filename": log.filename,
                "file_type": log.file_type,
                "status": log.status,
                "message": log.message,
                "parsed_at": log.parsed_at.isoformat()
            }
            for log in logs
        ]
    finally:
        db.close()


@app.get("/api/recommendations/{employee_name}")
async def get_recommendations(employee_name: str):
    """Получить рекомендации для сотрудника"""
    db = SessionLocal()
    try:
        recs = db.query(PDFRecommendation).filter(
            PDFRecommendation.employee_name == employee_name
        ).order_by(PDFRecommendation.created_at.desc()).all()
        
        if not recs:
            raise HTTPException(status_code=404, detail="Рекомендации не найдены")
        
        return {
            "employee_name": employee_name,
            "recommendations": [
                {
                    "priority0": r.priority0,
                    "trends": r.trends,
                    "recommendations": r.recommendations,
                    "created_at": r.created_at.isoformat()
                }
                for r in recs
            ]
        }
    finally:
        db.close()


# ============================================
# Функции парсинга
# ============================================

def normalize_employee_name(name: str) -> str:
    """
    Нормализация имён сотрудников — исправление известных опечаток.
    """
    corrections = {
        'Шавкатов Гафур': 'Шавкатов Гофур',
    }
    return corrections.get(name, name)


def parse_xlsx_file(file_path: Path, db: Session):
    """Парсинг XLSX файла"""
    try:
        period = extract_period_from_filename(file_path.name)
        if not period:
            raise ValueError(f"Не удалось извлечь период из {file_path.name}")
        
        df = pd.read_excel(file_path, sheet_name="Оценки звонков Soft Collection", engine="openpyxl")
        
        if EMPLOYEE_COLUMN not in df.columns:
            raise ValueError(f"Колонка '{EMPLOYEE_COLUMN}' не найдена")
        
        parsed_count = 0
        for employee, group in df.groupby(EMPLOYEE_COLUMN):
            if pd.isna(employee) or not str(employee).strip():
                continue

            employee = normalize_employee_name(str(employee).strip())
            
            scores_by_criteria = {k: [] for k in CRITERIA_COLUMNS.keys()}
            tqs_values = []
            duration_values = []
            
            for _, row in group.iterrows():
                tqs = parse_score(row.get(RESULT_COLUMN, 0))
                tqs_values.append(tqs)
                
                duration = parse_duration(row.get(DURATION_COLUMN))
                if duration > 0:
                    duration_values.append(duration)
                
                for criteria_key, column_name in CRITERIA_COLUMNS.items():
                    if column_name in df.columns:
                        score = parse_score(row.get(column_name, 0))
                        scores_by_criteria[criteria_key].append(score)
            
            avg_tqs = statistics.mean(tqs_values) if tqs_values else 0
            avg_aht = statistics.mean(duration_values) if duration_values else 0
            activity_count = len(group)
            
            avg_scores = {
                k: statistics.mean(v) if v else 0
                for k, v in scores_by_criteria.items()
            }
            
            # Сохранение в БД
            record = EmployeeScore(
                employee_name=employee,
                period=period,
                tqs=round(avg_tqs, 4),
                aht=round(avg_aht, 2),
                activity_count=activity_count,
                scores={k: round(v, 4) for k, v in avg_scores.items()}
            )
            db.add(record)
            parsed_count += 1
        
        db.commit()
        
        log = ParsingLog(
            filename=file_path.name,
            file_type="xlsx",
            status="success",
            message=f"Успешно распарсено: {parsed_count} сотрудников"
        )
        db.add(log)
        db.commit()
        
        logger.info(f"✅ XLSX {file_path.name}: {parsed_count} сотрудников")
        
    except Exception as e:
        db.rollback()
        log = ParsingLog(
            filename=file_path.name,
            file_type="xlsx",
            status="error",
            message=str(e)
        )
        db.add(log)
        db.commit()
        logger.error(f"❌ XLSX {file_path.name}: {e}")


def parse_pdf_file(file_path: Path, db: Session):
    """Парсинг PDF файла"""
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        import re
        sections = re.split(r'Отчет по сотруднику:', full_text)[1:]
        
        parsed_count = 0
        for section in sections:
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            employee_name = normalize_employee_name(lines[0].strip())
            if not employee_name:
                continue
            
            section_text = '\n'.join(lines[1:])
            
            priority0_match = re.search(r'Приоритет\s*0[:\s]*([^\n]+)', section_text, re.IGNORECASE)
            priority0 = priority0_match.group(1).strip() if priority0_match else None
            
            trends_match = re.search(r'Тенденции[:\s]*([^\n]+)', section_text, re.IGNORECASE)
            trends = trends_match.group(1).strip() if trends_match else None
            
            rec_match = re.search(r'Рекомендации[:\s]*(.+?)(?=\n\s*Отчет по сотруднику:|\Z)',
                                  section_text, re.IGNORECASE | re.DOTALL)
            recommendations = rec_match.group(1).strip() if rec_match else None
            
            if priority0 or trends or recommendations:
                record = PDFRecommendation(
                    employee_name=employee_name,
                    priority0=priority0,
                    trends=trends,
                    recommendations=recommendations
                )
                db.add(record)
                parsed_count += 1
        
        db.commit()
        
        log = ParsingLog(
            filename=file_path.name,
            file_type="pdf",
            status="success",
            message=f"Успешно распарсено: {parsed_count} сотрудников"
        )
        db.add(log)
        db.commit()
        
        logger.info(f"✅ PDF {file_path.name}: {parsed_count} сотрудников")
        
    except Exception as e:
        db.rollback()
        log = ParsingLog(
            filename=file_path.name,
            file_type="pdf",
            status="error",
            message=str(e)
        )
        db.add(log)
        db.commit()
        logger.error(f"❌ PDF {file_path.name}: {e}")


# ============================================
# Автозапуск при старте
# ============================================

@app.on_event("startup")
async def startup_event():
    """Парсинг существующих файлов при старте"""
    logger.info("🚀 Запуск QC Dashboard API v1.2")
    
    db = SessionLocal()
    try:
        if REPORTS_DIR.exists():
            xlsx_files = list(REPORTS_DIR.glob("*.xlsx"))
            pdf_files = list(REPORTS_DIR.glob("*.pdf"))
            
            logger.info(f"📁 Найдено XLSX: {len(xlsx_files)}, PDF: {len(pdf_files)}")
            
            for xlsx_file in xlsx_files:
                parse_xlsx_file(xlsx_file, db)
            
            for pdf_file in pdf_files:
                parse_pdf_file(pdf_file, db)
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

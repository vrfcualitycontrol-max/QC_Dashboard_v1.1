#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QC Soft Collection Auto Updater
Парсер XLSX/PDF файлов и обновление DASHBOARD_DATA в index.html
"""

import json
import os
import re
import time
import traceback
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

import pandas as pd
import pdfplumber
from sqlalchemy import (JSON, Column, DateTime, Float, Integer, MetaData,
                        String, Table, create_engine, select)
from sqlalchemy.exc import SQLAlchemyError
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

SCRIPT_DIR = Path(__file__).parent.resolve()
REPORTS_DIR = SCRIPT_DIR / "reports"
INDEX_HTML_PATH = SCRIPT_DIR / "assets" / "js" / "data.js"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://qc_user:change_me@localhost:5432/qc_dashboard"
)
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
DATA_MODE = os.getenv("DATA_MODE", "api")
ENABLE_BACKEND_SYNC = os.getenv("ENABLE_BACKEND_SYNC", "1") == "1"

MONTHS_MAP = {
    "01": "Январь 2026", "02": "Февраль 2026", "03": "Март 2026", "04": "Апрель 2026",
    "05": "Май 2026", "06": "Июнь 2026", "07": "Июль 2026", "08": "Август 2026",
    "09": "Сентябрь 2026", "10": "Октябрь 2026", "11": "Ноябрь 2026", "12": "Декабрь 2026"
}

XLSX_SHEET_NAME = "Оценки звонков Soft Collection"
SVP_COLUMNS_INDICES = list(range(6, 15))
TQS_INDEX = 15
DURATION_INDEX = 5
EMPLOYEE_INDEX = 0

SVP_KEYS = [
    "Приветствие",
    "Этика",
    "CRM",
    "Легенда",
    "Задолж.",
    "Аргумент.",
    "Манипул.",
    "Требования",
    "Итоги",
]

NAME_MAP = {
    "Toshtemirov Mukhammadali": "Тоштемиров Мухаммадали",
    "Abdullaeva Sevinch":      "Абдуллаева Севинч",
    "Alkarov Zhamshid":        "Алкаров Жамшид",
    "Bakhromova Nozima":       "Бахромова Нозима",
    "Boborakhmatov Sanyatbek": "Боборахматов Санъатбек",
    "Isakov Davron":           "Исаков Даврон",
    "Kayumova Soniya":         "Каюмова Сония",
    "Kurolboev Zhavokhir":     "Куролбоев Жавохир",
    "Mamaraimov Firdavs":      "Мамараимов Фирдавс",
    "Musaev Khurshid":         "Мусаев Хуршид",
    "Nadrullaeva Rukhsona":    "Надруллаева Рухсона",
    "Nizomiddinov Asliddin":   "Низомиддинов Аслиддин",
    "Rakhimzhonov Nodirzhon":  "Рахимжонов Нодиржон",
    "Sabitova Navruza":        "Сабитова Навруза",
    "Saburov Ogabek":          "Сабуров Оғабек",
    "Tozhiev Shokhrukh":       "Тожиев Шохрух",
    "Khakimov Umid":           "Хакимов Умид",
    "Shamiev Farrukh":         "Шамиев Фаррух",
    "Shoknazarova Sabrina":    "Шохназарова Сабрина",
    "Abduvalieva Zarifa":      "Абдувалиева Зарифа",
    "Komoldinov Diyorbek":     "Комолдинов Диёрбек",
    "Shavkatov Gofur":         "Шавкатов Гофур",
    "Makhmudzhonov Ibrokhim":  "Махмуджонов Иброхим",
    "Mirkamalov Boburzhon":    "Миркамалов Бобуржон",
    "Mirkhamidov Samandar":    "Мирхамидов Самандар",
    "Khasanova Madinabonu":    "Хасанова Мадинабону",
    "Sherkulov Azamat":        "Шеркулов Азамат",
}
for cyr in list(NAME_MAP.values()):
    NAME_MAP[cyr] = cyr


def normalize_name(name: Any) -> str:
    if pd.isna(name):
        return ""
    text = str(name).strip()
    return NAME_MAP.get(text, text)


def parse_score(value: Any) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(',', '.')
    if text.endswith('%'):
        text = text[:-1].strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def parse_duration(value: Any) -> float:
    if pd.isna(value) or value is None:
        return 0.0
    if hasattr(value, 'hour') and hasattr(value, 'minute'):
        hour = float(value.hour)
        minute = float(value.minute)
        second = float(getattr(value, 'second', 0))
        # XLSX often stores MM:SS as HH:MM:00 (e.g. 01:26:00 -> 1:26, 00:51:00 -> 0:51).
        # For call-center AHT we treat any HH:MM:00 as minutes:seconds.
        if second == 0:
            return hour + minute / 60.0
        return hour * 60.0 + minute + second / 60.0
    text = str(value).strip()
    if not text:
        return 0.0
    if ':' in text:
        parts = [p for p in text.split(':') if p.strip()]
        try:
            if len(parts) == 3:
                p0 = float(parts[0])
                p1 = float(parts[1])
                p2 = float(parts[2])
                if p2 == 0:
                    return p0 + p1 / 60.0
                return p0 * 60.0 + p1 + p2 / 60.0
            if len(parts) == 2:
                return float(parts[0]) + float(parts[1]) / 60.0
            return float(parts[0])
        except ValueError:
            return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def format_duration(minutes: float) -> str:
    """Возвращает строку в формате MM:SS (минуты:секунды)."""
    if minutes <= 0:
        return "N/A"
    total_seconds = int(minutes * 60)
    mins = total_seconds // 60
    secs = total_seconds % 60
    return f"{mins:02d}:{secs:02d}"


def extract_month_and_period(filename: str) -> tuple[str, str]:
    # Try format: "13.04.2026 - 19.04.2026"
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})", filename)
    if match:
        month = MONTHS_MAP.get(match.group(2), f"{match.group(2)}.{match.group(3)}")
        period = f"{match.group(1)}-{match.group(4)}"
        return month, period
    
    # Try format: "13-19.04.2026"
    match = re.search(r"(\d{2})-(\d{2})\.(\d{2})\.(\d{4})", filename)
    if match:
        month = MONTHS_MAP.get(match.group(3), f"{match.group(3)}.{match.group(4)}")
        period = f"{match.group(1)}-{match.group(2)}"
        return month, period
    
    return "Неизвестно", "Неизвестно"


def ensure_employee_period(data: Dict[str, Any], employee: str, month: str, period: str) -> Dict[str, Any]:
    if employee not in data:
        data[employee] = {"months": {}}
    if month not in data[employee]["months"]:
        data[employee]["months"][month] = {"periods": []}
    periods = data[employee]["months"][month]["periods"]
    for item in periods:
        if item["period"] == period:
            return item
    placeholder = {
        "period": period,
        "tqs": 0.0,
        "aht": "N/A",
        "svp": {key: 1.0 for key in SVP_KEYS},
        "raw_scores": {key: [] for key in SVP_KEYS},
        "tendencies": "",
        "rec": "",
        "_tqs_values": [],
        "_durations": [],
        "_activity_count": 0,
    }
    periods.append(placeholder)
    periods.sort(key=lambda item: item["period"])
    return placeholder


def read_xlsx_files() -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if not REPORTS_DIR.exists():
        print(f"[WARNING] reports directory not found: {REPORTS_DIR}")
        return data
    xlsx_files = sorted(REPORTS_DIR.glob("*.xlsx"))
    if not xlsx_files:
        print(f"[WARNING] no XLSX files found in {REPORTS_DIR}")
        return data
    print(f"[INFO] found {len(xlsx_files)} XLSX files")
    for xlsx_file in xlsx_files:
        month, period = extract_month_and_period(xlsx_file.name)
        if month == "Неизвестно":
            print(f"[WARNING] could not parse month from {xlsx_file.name}")
        try:
            df = pd.read_excel(xlsx_file, sheet_name=XLSX_SHEET_NAME, engine="openpyxl", header=2)
        except Exception as exc:
            print(f"[ERROR] failed to read {xlsx_file.name}: {exc}")
            continue
        if df.shape[1] < max(SVP_COLUMNS_INDICES) + 1:
            print(f"[WARNING] unexpected XLSX format {xlsx_file.name}; columns={df.shape[1]}")
            continue
        for _, row in df.iterrows():
            employee = normalize_name(row.iloc[EMPLOYEE_INDEX])
            if not employee:
                continue
            entry = ensure_employee_period(data, employee, month, period)
            tqs = parse_score(row.iloc[TQS_INDEX])
            duration = parse_duration(row.iloc[DURATION_INDEX])
            svp_values = [parse_score(row.iloc[idx]) for idx in SVP_COLUMNS_INDICES]
            entry["_tqs_values"].append(tqs)
            entry["_durations"].append(duration)
            entry["_activity_count"] += 1
            for key, value in zip(SVP_KEYS, svp_values):
                entry["raw_scores"][key].append(value)
        print(f"[INFO] {xlsx_file.name} loaded")
    # finalize aggregates
    for employee, employee_data in data.items():
        for month, month_data in employee_data["months"].items():
            for period_item in month_data["periods"]:
                if period_item["_tqs_values"]:
                    period_item["tqs"] = round(mean(period_item["_tqs_values"]), 2)
                if period_item["_durations"]:
                    period_item["aht"] = format_duration(mean(period_item["_durations"]))
                if period_item.get("_activity_count") is None:
                    period_item["_activity_count"] = len(period_item["_tqs_values"])
                period_item["activity_count"] = period_item.get("_activity_count", len(period_item["_tqs_values"]))
                for key in SVP_KEYS:
                    if period_item["raw_scores"][key]:
                        period_item["svp"][key] = round(mean(period_item["raw_scores"][key]), 2)
                period_item.pop("_tqs_values", None)
                period_item.pop("_durations", None)
                period_item.pop("_activity_count", None)
    
    # Сортировка месяцев по календарному порядку для каждого сотрудника
    MONTH_ORDER = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    for employee, employee_data in data.items():
        if 'months' in employee_data:
            sorted_months = dict(sorted(
                employee_data['months'].items(),
                key=lambda item: (
                    MONTH_ORDER.index(item[0].split(' ')[0]) if item[0].split(' ')[0] in MONTH_ORDER else 999,
                    -int(item[0].split(' ')[1]) if len(item[0].split(' ')) > 1 and item[0].split(' ')[1].isdigit() else 0
                )
            ))
            employee_data['months'] = sorted_months
    
    return data


def extract_pdf_sections(text: str) -> List[str]:
    parts = re.split(r"Отчет\s+по\s+сотруднику\s*[:：]", text, flags=re.IGNORECASE)
    return [part.strip() for part in parts if part.strip()]


def extract_section_text(block: str, key: str) -> str:
    # Find the line with the key
    pattern = re.search(fr"{re.escape(key)}\s*[:：]?\s*", block, flags=re.IGNORECASE)
    if not pattern:
        return ""
    
    # Get everything after the key
    start_pos = pattern.end()
    remaining = block[start_pos:]
    
    # If this is "Рекомендации", capture everything until paragraph break or end
    if "рекомендаци" in key.lower():
        # Stop at double newline (paragraph break) - this is where recommendations end
        match_break = re.search(r"\n\s*\n", remaining)
        if match_break:
            text = remaining[:match_break.start()]
        else:
            text = remaining
    else:
        # For other sections, just take until end of line (existing behavior)
        match_newline = re.search(r"\n", remaining)
        if match_newline:
            text = remaining[:match_newline.start()]
        else:
            text = remaining
    
    return text.strip().replace("\n", " ").replace("\r", " ")


def read_pdf_files(data: Dict[str, Any]) -> None:
    if not REPORTS_DIR.exists():
        return
    pdf_files = sorted(REPORTS_DIR.glob("*.pdf"))
    if not pdf_files:
        return
    print(f"[INFO] found {len(pdf_files)} PDF files")
    for pdf_file in pdf_files:
        month, period = extract_month_and_period(pdf_file.name)
        print(f"[INFO] parsing PDF: {pdf_file.name}")
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as exc:
            print(f"[ERROR] failed to open PDF {pdf_file.name}: {exc}")
            continue
        sections = extract_pdf_sections(text)
        for section in sections:
            lines = [line.strip() for line in section.splitlines() if line.strip()]
            if not lines:
                continue
            employee = normalize_name(lines[0])
            if not employee:
                continue
            entry = ensure_employee_period(data, employee, month, period)
            entry["tendencies"] = extract_section_text(section, "Тенденции") or entry["tendencies"]
            entry["rec"] = extract_section_text(section, "Рекомендации") or entry["rec"]
    return


def clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Удаляет мусорные записи из собранных данных."""
    cleaned: Dict[str, Any] = {}
    for employee, emp_data in data.items():
        if not employee or str(employee).strip() == "":
            continue
        clean_months: Dict[str, Any] = {}
        for month, month_data in emp_data.get("months", {}).items():
            if month == "Неизвестно":
                continue
            clean_periods: List[Dict[str, Any]] = []
            for period in month_data.get("periods", []):
                if period.get("period") == "Неизвестно":
                    continue
                if period.get("tqs", 0) == 0 and not period.get("_tqs_values"):
                    continue
                period.pop("_tqs_values", None)
                period.pop("_durations", None)
                period.pop("_activity_count", None)
                clean_periods.append(period)
            if clean_periods:
                clean_months[month] = {"periods": clean_periods}
        if clean_months:
            cleaned[employee] = {"months": clean_months}
    return cleaned


def update_index_html(new_data: Dict[str, Any]) -> bool:
    if not INDEX_HTML_PATH.exists():
        print(f"[ERROR] index.html not found at {INDEX_HTML_PATH}")
        return False
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    payload = json.dumps(new_data, ensure_ascii=False, indent=2)
    replacement = f"// --- DATA START ---\nconst DASHBOARD_DATA = {payload};\n// --- DATA END ---"
    pattern = re.compile(r"// --- DATA START ---.*?// --- DATA END ---", flags=re.DOTALL)
    if not pattern.search(content):
        print("[ERROR] data markers not found in index.html")
        return False
    updated = pattern.sub(replacement, content)
    INDEX_HTML_PATH.write_text(updated, encoding="utf-8")
    print(f"[INFO] dashboard data updated in {INDEX_HTML_PATH.name}")
    return True


def get_db_engine():
    """Create database engine for PostgreSQL."""
    return create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


def _build_multipart_body(field_name: str, filename: str, content: bytes, content_type: str) -> tuple[str, bytes]:
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    body_lines = [
        f"--{boundary}",
        f"Content-Disposition: form-data; name=\"{field_name}\"; filename=\"{filename}\"",
        f"Content-Type: {content_type}",
        "",
    ]
    body = "\r\n".join(body_lines).encode("utf-8") + b"\r\n" + content + b"\r\n" + f"--{boundary}--\r\n".encode("utf-8")
    return boundary, body


def _upload_file_to_backend(file_path: Path) -> None:
    if not BACKEND_API_URL:
        return
    file_type = file_path.suffix.lower()
    if file_type == ".xlsx":
        endpoint = "upload/xlsx"
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif file_type == ".pdf":
        endpoint = "upload/pdf"
        content_type = "application/pdf"
    else:
        return

    url = f"{BACKEND_API_URL.rstrip('/')}/api/{endpoint}"
    try:
        with file_path.open("rb") as f:
            content = f.read()
        boundary, body = _build_multipart_body("file", file_path.name, content, content_type)
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            response_text = response.read().decode("utf-8", errors="replace")
            print(f"[INFO] uploaded {file_path.name} to backend: {response_text[:200]}")
    except urllib.error.HTTPError as exc:
        print(f"[ERROR] backend upload failed {file_path.name}: {exc.code} {exc.reason}")
    except urllib.error.URLError as exc:
        print(f"[ERROR] backend upload failed {file_path.name}: {exc}")
    except Exception as exc:
        print(f"[ERROR] unexpected backend upload error for {file_path.name}: {exc}")


def sync_reports_to_backend() -> None:
    if not BACKEND_API_URL:
        return
    if not REPORTS_DIR.exists():
        return

    for file_path in sorted(REPORTS_DIR.glob("*.xlsx")) + sorted(REPORTS_DIR.glob("*.pdf")):
        _upload_file_to_backend(file_path)


def write_dashboard_data_to_db(data: Dict[str, Any]) -> None:
    """Save aggregated dashboard metrics into PostgreSQL."""
    try:
        engine = get_db_engine()
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
            Column("created_at", DateTime),
            Column("updated_at", DateTime),
            extend_existing=True,
        )
        metadata.create_all(engine, checkfirst=True)

        with engine.begin() as conn:
            for employee_name, employee_data in data.items():
                for month, month_data in employee_data["months"].items():
                    for period_item in month_data["periods"]:
                        row = {
                            "employee_name": employee_name,
                            "month": month,
                            "period": period_item["period"],
                            "tqs": float(period_item["tqs"] or 0.0),
                            "aht": str(period_item["aht"]),
                            "activity_count": int(period_item.get("activity_count", 0)),
                            "svp_scores": period_item.get("svp", {}),
                            "raw_scores": period_item.get("raw_scores", {}),
                            "tendencies": period_item.get("tendencies", ""),
                            "recommendations": period_item.get("rec", ""),
                            "updated_at": datetime.now(timezone.utc),
                        }
                        select_stmt = select(employee_scores.c.id).where(
                            employee_scores.c.employee_name == employee_name,
                            employee_scores.c.month == month,
                            employee_scores.c.period == period_item["period"],
                        )
                        existing = conn.execute(select_stmt).first()
                        if existing:
                            update_stmt = (
                                employee_scores.update()
                                .where(employee_scores.c.id == existing[0])
                                .values(**row)
                            )
                            conn.execute(update_stmt)
                        else:
                            row["created_at"] = datetime.now(timezone.utc)
                            conn.execute(employee_scores.insert().values(**row))
        print("[INFO] dashboard data written to PostgreSQL")
    except SQLAlchemyError as exc:
        print(f"[ERROR] Could not write dashboard data to DB: {exc}")
    except Exception as exc:
        print(f"[ERROR] Unexpected DB write failure: {exc}")


def refresh_dashboard() -> None:
    """
    Обновляет данные дашборда в зависимости от режима:
      DATA_MODE=static  — обновляет assets/js/data.js (фронтенд читает его напрямую).
      DATA_MODE=api     — сейчас тоже обновляет assets/js/data.js, потому что фронтенд пока не умеет читать из API.
      ENABLE_BACKEND_SYNC=1 — параллельно записывает агрегаты в PostgreSQL.
                              Используется при static-mode для накопления данных в БД
                              в рамках подготовки к переходу на API Mode.
    """
    try:
        print(f"[INFO] refresh_dashboard | DATA_MODE={DATA_MODE} | ENABLE_BACKEND_SYNC={ENABLE_BACKEND_SYNC}")
        data = read_xlsx_files()
        read_pdf_files(data)
        data = clean_data(data)
        if not data:
            print("[WARNING] no dashboard data generated")
            return

        # Всегда обновляем data.js — фронтенд пока читает данные из этого файла
        update_index_html(data)

        # Запись в PostgreSQL: всегда при API Mode; при Static Mode — если ENABLE_BACKEND_SYNC=1
        if DATA_MODE == "api" or ENABLE_BACKEND_SYNC:
            write_dashboard_data_to_db(data)
            sync_reports_to_backend()
        else:
            print("[INFO] ENABLE_BACKEND_SYNC=0: пропускаем запись в БД и синхронизацию с backend")

    except Exception:
        print("[ERROR] failed to refresh dashboard")
        traceback.print_exc()


class ReportsHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(".xlsx") or event.src_path.lower().endswith(".pdf"):
            print(f"[INFO] detected new file: {event.src_path}")
            time.sleep(1.5)
            refresh_dashboard()

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(".xlsx") or event.src_path.lower().endswith(".pdf"):
            print(f"[INFO] detected modified file: {event.src_path}")
            time.sleep(1.5)
            refresh_dashboard()


def main() -> None:
    refresh_dashboard()
    observer = Observer()
    observer.schedule(ReportsHandler(), str(REPORTS_DIR), recursive=False)
    observer.start()
    print(f"[INFO] watching {REPORTS_DIR} for XLSX/PDF updates...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()

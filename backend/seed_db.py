"""
Скрипт начальной загрузки данных из папки reports/ в PostgreSQL.
Запускается ОДИН РАЗ при первом деплое для импорта исторических данных.

Использование:
    cd backend
    python seed_db.py
"""
import os
import sys
from pathlib import Path

# Добавить корневую директорию проекта в PATH
sys.path.insert(0, str(Path(__file__).parent))

from parser import (
    detect_file_type, parse_quality_bytes, parse_collections_bytes,
    parse_crm_bytes, parse_report_pdf_bytes
)
from app import engine, init_db, write_parsed_data_to_db

def seed_from_reports():
    init_db()
    
    reports_dir_str = os.environ.get("REPORTS_DIR")
    if reports_dir_str:
        reports_dir = Path(reports_dir_str)
    else:
        reports_dir = Path(__file__).parent.parent / "reports"
        
    if not reports_dir.exists():
        print(f"[ERROR] reports/ directory not found at {reports_dir}")
        return
    
    files = sorted(list(reports_dir.glob("*.xlsx")) + list(reports_dir.glob("*.pdf")))
    print(f"[INFO] Found {len(files)} files in reports/")
    
    for file_path in files:
        try:
            content = file_path.read_bytes()
            file_type = detect_file_type(content, file_path.name)
            
            if file_type == "unknown":
                print(f"[SKIP] {file_path.name} — unknown type")
                continue
            
            if file_type == "quality":
                month, period, data = parse_quality_bytes(content, file_path.name)
            elif file_type == "collections":
                month, period, data = parse_collections_bytes(content, file_path.name)
            elif file_type == "crm":
                month, period, data = parse_crm_bytes(content, file_path.name)
            elif file_type == "report":
                month, period, data = parse_report_pdf_bytes(content, file_path.name)
            else:
                continue
            
            count = write_parsed_data_to_db(file_type, month, period, data)
            print(f"[OK] {file_path.name} -> {file_type} | {month} {period} | {count} employees")
            
        except Exception as e:
            print(f"[ERROR] {file_path.name}: {e}")
    
    print("[DONE] Seed complete!")

if __name__ == "__main__":
    seed_from_reports()

#!/usr/bin/env python3
# -*- utf-8 -*-
"""
QC Soft Collection Auto Updater
Парсер для извлечения данных из XLSX и PDF файлов
и обновления аналитического дашборда
"""

import os
import re
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import pdfplumber


# Конфигурация
SCRIPT_DIR = Path(__file__).parent
REPORTS_DIR = SCRIPT_DIR / "reports"
INDEX_FILE = SCRIPT_DIR / "index.html"

# Название листа в XLSX с данными оценок
XLSX_SHEET_NAME = "Оценки звонков Soft Collection"

# Маппинг колонок XLSX (точные названия из файлов)
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

# Веса критериев (для справки)
CRITERIA_WEIGHTS = {
    "greeting": 0.05,
    "ethics": 0.05,
    "crm": 0.10,
    "legend": 0.15,
    "informing": 0.10,
    "argumentation": 0.20,
    "manipulation": 0.10,
    "requirements": 0.15,
    "summary": 0.10
}


def extract_period_from_filename(filename: str) -> Optional[str]:
    """
    Извлекает период из имени файла XLSX.
    Паттерн: дд.мм.гггг - дд.мм.гггг
    Возвращает формат: "01-08 Фев 2026"
    """
    pattern = r'(\d{2})\.(\d{2})\.(\d{4})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})'
    match = re.search(pattern, filename)
    
    if match:
        day_start = match.group(1)
        month_num = match.group(2)
        year = match.group(3)
        day_end = match.group(4)
        
        # Конвертация месяца в русское сокращение
        months = {
            "01": "Янв", "02": "Фев", "03": "Мар", "04": "Апр",
            "05": "Май", "06": "Июн", "07": "Июл", "08": "Авг",
            "09": "Сен", "10": "Окт", "11": "Ноя", "12": "Дек"
        }
        month_name = months.get(month_num, month_num)
        
        return f"{day_start}-{day_end} {month_name} {year}"
    
    return None


def parse_score(value: Any) -> float:
    """
    Конвертирует значение оценки в float (0, 0.5, 1).
    """
    if pd.isna(value):
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    str_value = str(value).strip()
    
    # Процентное значение (например "83%")
    if "%" in str_value:
        try:
            return float(str_value.replace("%", "").strip()) / 100
        except ValueError:
            return 0.0
    
    # Дробное значение
    try:
        return float(str_value.replace(",", "."))
    except ValueError:
        return 0.0


def read_xlsx_files() -> Dict[str, Dict[str, Any]]:
    """
    Читает все XLSX файлы из папки reports.
    Возвращает структуру данных по сотрудникам и периодам.
    """
    employees_data: Dict[str, Dict[str, Any]] = {}

    if not REPORTS_DIR.exists():
        print(f"[WARNING] Папка reports не найдена: {REPORTS_DIR}")
        return employees_data

    xlsx_files = list(REPORTS_DIR.glob("*.xlsx"))

    if not xlsx_files:
        print(f"[WARNING] XLSX файлы не найдены в {REPORTS_DIR}")
        return employees_data

    print(f"[INFO] Найдено XLSX файлов: {len(xlsx_files)}")

    for xlsx_file in xlsx_files:
        print(f"[INFO] Обработка файла: {xlsx_file.name}")

        period = extract_period_from_filename(xlsx_file.name)
        if not period:
            print(f"[WARNING] Не удалось извлечь период из {xlsx_file.name}")
            continue

        try:
            # Читаем конкретный лист с данными оценок
            df = pd.read_excel(xlsx_file, sheet_name=XLSX_SHEET_NAME, engine="openpyxl")
        except Exception as e:
            print(f"[ERROR] Ошибка чтения листа '{XLSX_SHEET_NAME}' из {xlsx_file.name}: {e}")
            continue

        # Проверка наличия необходимых колонок
        if EMPLOYEE_COLUMN not in df.columns:
            print(f"[WARNING] Колонка '{EMPLOYEE_COLUMN}' не найдена в {xlsx_file.name}")
            print(f"  Доступные колонки: {list(df.columns)[:10]}...")
            continue
        
        # Группировка по сотрудникам
        for employee, group in df.groupby(EMPLOYEE_COLUMN):
            if pd.isna(employee) or not str(employee).strip():
                continue

            employee = str(employee).strip()

            if employee not in employees_data:
                employees_data[employee] = {
                    "periods": {}
                }

            # Сбор оценок по критериям
            scores_by_criteria: Dict[str, List[float]] = {k: [] for k in CRITERIA_COLUMNS.keys()}
            tqs_values: List[float] = []
            duration_values: List[float] = []

            for _, row in group.iterrows():
                # TQS из колонки "Итоги"
                tqs = parse_score(row.get(RESULT_COLUMN, 0))
                tqs_values.append(tqs)

                # Длительность звонка
                duration = parse_duration(row.get(DURATION_COLUMN))
                if duration > 0:
                    duration_values.append(duration)

                # Оценки по критериям
                for criteria_key, column_name in CRITERIA_COLUMNS.items():
                    if column_name in df.columns:
                        score = parse_score(row.get(column_name, 0))
                        scores_by_criteria[criteria_key].append(score)

            # Агрегация данных за период
            employees_data[employee]["periods"][period] = {
                "tqs": statistics.mean(tqs_values) if tqs_values else 0,
                "activity_count": len(group),
                "scores": scores_by_criteria,
                "aht": statistics.mean(duration_values) if duration_values else 0  # AHT в минутах
            }

    return employees_data


def parse_duration(value) -> float:
    """
    Конвертирует длительность звонка в минуты.
    Формат времени в Excel: ММ:СС:00 (минуты:секунды), где hour=минуты, minute=секунды.
    """
    if value is None:
        return 0.0
    try:
        # datetime.time: hour=минуты, minute=секунды, second=0
        # Конвертируем в минуты: минуты + секунды/60
        return float(value.hour + value.minute / 60.0 + value.second / 3600.0)
    except (AttributeError, TypeError):
        return 0.0


def read_pdf_files() -> Dict[str, Dict[str, str]]:
    """
    Читает все PDF файлы из папки reports.
    Извлекает секции "Отчет по сотруднику: [ФИО]".
    Возвращает данные по сотрудникам: priority0, trends, recommendations.
    """
    pdf_data: Dict[str, Dict[str, str]] = {}
    
    if not REPORTS_DIR.exists():
        return pdf_data
    
    pdf_files = list(REPORTS_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"[INFO] PDF файлы не найдены в {REPORTS_DIR}")
        return pdf_data
    
    print(f"[INFO] Найдено PDF файлов: {len(pdf_files)}")
    
    for pdf_file in pdf_files:
        print(f"[INFO] Обработка PDF: {pdf_file.name}")
        
        try:
            with pdfplumber.open(pdf_file) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                
                # Парсинг секций по сотрудникам
                parse_pdf_sections(full_text, pdf_data)
                
        except Exception as e:
            print(f"[ERROR] Ошибка чтения {pdf_file.name}: {e}")
    
    return pdf_data


def parse_pdf_sections(text: str, pdf_data: Dict[str, Dict[str, str]]) -> None:
    """
    Парсит текст PDF и извлекает секции по сотрудникам.
    """
    # Паттерн для поиска секции сотрудника
    employee_pattern = r'Отчет по сотруднику:\s*([^\n]+)'
    
    # Разбиваем текст на секции
    sections = re.split(r'Отчет по сотруднику:', text)[1:]  # Пропускаем первую часть
    
    for section in sections:
        lines = section.strip().split('\n')
        if not lines:
            continue
        
        # Первая строка - имя сотрудника
        employee_name = lines[0].strip()
        if not employee_name:
            continue
        
        # Остальной текст секции
        section_text = '\n'.join(lines[1:])
        
        # Извлечение Приоритет 0
        priority0_match = re.search(r'Приоритет\s*0[:\s]*([^\n]+)', section_text, re.IGNORECASE)
        priority0 = priority0_match.group(1).strip() if priority0_match else None
        
        # Извлечение Тенденции
        trends_match = re.search(r'Тенденции[:\s]*([^\n]+)', section_text, re.IGNORECASE)
        trends = trends_match.group(1).strip() if trends_match else None
        
        # Извлечение Рекомендации (может быть многострочным)
        rec_match = re.search(r'Рекомендации[:\s]*(.+?)(?=\n\s*Отчет по сотруднику:|\Z)', 
                              section_text, re.IGNORECASE | re.DOTALL)
        recommendations = rec_match.group(1).strip() if rec_match else None
        
        if employee_name not in pdf_data:
            pdf_data[employee_name] = {}
        
        if priority0:
            pdf_data[employee_name]["priority0"] = priority0
        if trends:
            pdf_data[employee_name]["trends"] = trends
        if recommendations:
            pdf_data[employee_name]["recommendations"] = recommendations


def calculate_aggregated_scores(periods_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Вычисляет агрегированные оценки по всем периодам.
    Использует среднее арифметическое для точного отражения выработки.
    """
    all_scores: Dict[str, List[float]] = {k: [] for k in CRITERIA_COLUMNS.keys()}

    for period_data in periods_data.values():
        scores = period_data.get("scores", {})
        for criteria_key in all_scores.keys():
            if criteria_key in scores:
                all_scores[criteria_key].extend(scores[criteria_key])

    aggregated = {}
    for criteria_key, scores_list in all_scores.items():
        if scores_list:
            # Используем среднее арифметическое для точного расчета выработки
            aggregated[criteria_key] = round(statistics.mean(scores_list), 4)
        else:
            aggregated[criteria_key] = 0.0

    return aggregated


def calculate_aggregated_tqs(periods_data: Dict[str, Any]) -> float:
    """
    Вычисляет средний TQS по всем периодам.
    """
    tqs_values = [p.get("tqs", 0) for p in periods_data.values()]
    if tqs_values:
        return round(statistics.mean(tqs_values), 2)
    return 0.0


def calculate_sum_activity(periods_data: Dict[str, Any]) -> int:
    """
    Суммирует количество звонков по всем периодам.
    """
    return sum(p.get("activity_count", 0) for p in periods_data.values())


def generate_pdf_summary(pdf_data: Dict[str, Dict[str, str]]) -> str:
    """
    Генерирует общую сводку по всем сотрудникам из PDF.
    """
    if not pdf_data:
        return ""
    
    summary_parts = []
    
    for employee, data in pdf_data.items():
        short_name = employee
        # Сокращаем имя для краткости
        name_parts = employee.split()
        if len(name_parts) >= 2:
            short_name = f"{name_parts[0]} {name_parts[1][0]}."
        
        if data.get("priority0"):
            summary_parts.append(f"🔴 {short_name}: {data['priority0']}")
        
        if data.get("recommendations"):
            recs = data["recommendations"].split('\n')[:2]  # Берём первые 2 рекомендации
            for rec in recs:
                if rec.strip():
                    summary_parts.append(f"💡 {short_name}: {rec.strip()}")
    
    if summary_parts:
        return "\n".join(summary_parts[:10])  # Ограничиваем 10 строками
    
    return ""


def calculate_aggregated_aht(periods_data: Dict[str, Any]) -> float:
    """
    Вычисляет среднее время разговора (AHT) по всем периодам.
    """
    aht_values = [p.get("aht", 0) for p in periods_data.values() if p.get("aht", 0) > 0]
    if aht_values:
        return round(statistics.mean(aht_values), 2)
    return 0.0


def build_dashboard_data(
    employees_data: Dict[str, Dict[str, Any]],
    pdf_data: Dict[str, Dict[str, str]]
) -> Dict[str, Any]:
    """
    Строит финальную структуру данных для дашборда.
    """
    dashboard_data: Dict[str, Any] = {}

    for employee, emp_data in employees_data.items():
        periods = emp_data.get("periods", {})

        if not periods:
            continue

        dashboard_data[employee] = {
            "dashboard_name": employee,
            "periods": {},
            "aggregated_scores": calculate_aggregated_scores(periods),
            "aggregated_tqs": calculate_aggregated_tqs(periods),
            "sum_activity": calculate_sum_activity(periods),
            "aggregated_aht": calculate_aggregated_aht(periods)
        }

        # Добавляем данные по периодам
        for period, period_data in periods.items():
            dashboard_data[employee]["periods"][period] = {
                "tqs": round(period_data["tqs"], 4),
                "activity_count": period_data["activity_count"],
                "scores": period_data["scores"],
                "aht": round(period_data.get("aht", 0), 2)
            }

        # Добавляем PDF данные если есть
        if employee in pdf_data:
            dashboard_data[employee]["pdf_data"] = pdf_data[employee]

    # Добавляем общую сводку из PDF
    pdf_summary = generate_pdf_summary(pdf_data)
    if pdf_summary:
        dashboard_data["_meta_pdf_summary"] = pdf_summary

    return dashboard_data


def update_index_html(dashboard_data: Dict[str, Any]) -> bool:
    """
    Обновляет index.html, вставляя данные между маркерами.
    """
    if not INDEX_FILE.exists():
        print(f"[ERROR] Файл index.html не найден: {INDEX_FILE}")
        return False
    
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[ERROR] Ошибка чтения index.html: {e}")
        return False
    
    # Маркеры
    start_marker = "// --- DATA START ---"
    end_marker = "// --- DATA END ---"
    
    # Проверяем наличие маркеров
    if start_marker not in content or end_marker not in content:
        print("[ERROR] Не удалось найти маркеры данных в index.html")
        return False
    
    # Генерируем JSON с данными
    json_data = json.dumps(dashboard_data, ensure_ascii=False, indent=2)
    
    # Находим позиции маркеров
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("[ERROR] Не удалось найти позиции маркеров")
        return False
    
    # Находим конец строки с start_marker
    line_end = content.find('\n', start_idx)
    if line_end == -1:
        line_end = len(content)
    
    # Находим начало строки с end_marker (ищем начало строки перед end_marker)
    line_start = content.rfind('\n', 0, end_idx)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1  # Пропускаем сам символ \n
    
    # Формируем новую секцию данных
    # Сохраняем отступы оригинала
    original_line = content[start_idx:line_end+1]
    indent = ""
    match = re.match(r'^(\s*)', original_line)
    if match:
        indent = match.group(1)
    
    # Форматируем JSON с правильными отступами
    json_lines = json_data.split('\n')
    formatted_json = '\n'.join(indent + line if line else line for line in json_lines)
    
    # Собираем новый контент
    new_content = (
        content[:line_end+1] + 
        indent + "window.DASHBOARD_DATA = " + formatted_json + "\n" +
        content[line_start:]
    )
    
    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        print(f"[ERROR] Ошибка записи index.html: {e}")
        return False
    
    return True


def main():
    """
    Основная функция обновления дашборда.
    """
    print("=" * 60)
    print("QC Soft Collection Auto Updater")
    print("=" * 60)
    print(f"[INFO] Директория скрипта: {SCRIPT_DIR}")
    print(f"[INFO] Директория отчетов: {REPORTS_DIR}")
    print(f"[INFO] Файл дашборда: {INDEX_FILE}")
    print()
    
    # Чтение XLSX файлов
    print("[STEP 1] Чтение XLSX файлов...")
    employees_data = read_xlsx_files()
    print(f"[INFO] Сотрудников найдено: {len(employees_data)}")
    print()
    
    # Чтение PDF файлов
    print("[STEP 2] Чтение PDF файлов...")
    pdf_data = read_pdf_files()
    print(f"[INFO] PDF данных найдено: {len(pdf_data)}")
    print()
    
    # Построение структуры данных
    print("[STEP 3] Построение структуры данных...")
    dashboard_data = build_dashboard_data(employees_data, pdf_data)
    print(f"[INFO] Записей в дашборде: {len(dashboard_data)}")
    print()
    
    # Обновление index.html
    print("[STEP 4] Обновление index.html...")
    if update_index_html(dashboard_data):
        print("[SUCCESS] index.html обновлен")
    else:
        print("[ERROR] Не удалось обновить index.html")
        return 1
    
    print()
    print("=" * 60)
    print("Обновление завершено успешно!")
    print("=" * 60)
    
    # Вывод краткой статистики
    if dashboard_data:
        print("\n📊 Краткая статистика:")
        for emp, data in dashboard_data.items():
            if emp == "_meta_pdf_summary":
                continue
            print(f"  • {emp}: TQS={data['aggregated_tqs']*100:.0f}%, "
                  f"Звонков={data['sum_activity']}")
    
    return 0


if __name__ == "__main__":
    exit(main())

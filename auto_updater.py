#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QC Soft Collection Auto Updater
Парсер XLSX/PDF файлов и обновление DASHBOARD_DATA в index.html
"""

import json
import os
import sys

# Автоматический запуск через venv, если библиотеки не установлены в текущем окружении
try:
    import pandas
    import pdfplumber
    import openpyxl
    import watchdog
except ImportError:
    # Путь к venv относительно корня проекта
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(SCRIPT_DIR, "venv")
    if os.name == 'nt':
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")
        
    if os.path.exists(venv_python):
        if os.environ.get("AUTO_UPDATER_VENV_RETRY") == "1":
            print("[ОШИБКА] Не удалось запустить скрипт даже через виртуальное окружение venv.")
            print("Убедитесь, что вы запустили setup_env.bat для установки всех зависимостей.")
            sys.exit(1)
        os.environ["AUTO_UPDATER_VENV_RETRY"] = "1"
        print("[INFO] Не найдены необходимые библиотеки. Перезапускаю через venv...")
        import subprocess
        try:
            result = subprocess.call([venv_python] + sys.argv)
            sys.exit(result)
        except Exception as e:
            print(f"[ОШИБКА] Ошибка при перезапуске процесса через venv: {e}")
            sys.exit(1)
    else:
        print("[ОШИБКА] Отсутствуют необходимые библиотеки (pandas, pdfplumber и др.) и папка venv не найдена.")
        print("Пожалуйста, запустите setup_env.bat, чтобы настроить рабочее окружение проекта.")
        sys.exit(1)

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
    # 1. Try format: "13.04.2026 - 19.04.2026"
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})", filename)
    if match:
        month = MONTHS_MAP.get(match.group(2), f"{match.group(2)}.{match.group(3)}")
        period = f"{match.group(1)}-{match.group(4)}"
        return month, period
    
    # 2. Try format: "13-19.04.2026"
    match = re.search(r"(\d{2})-(\d{2})\.(\d{2})\.(\d{4})", filename)
    if match:
        month = MONTHS_MAP.get(match.group(3), f"{match.group(3)}.{match.group(4)}")
        period = f"{match.group(1)}-{match.group(2)}"
        return month, period

    # 2.5. Try format: "01-07 Июнь 2026" or "01-07 июнь"
    match_week = re.search(r"(\d{2})-(\d{2})\s+(Январь|Февраль|Март|Апрель|Май|Июнь|Июль|Август|Сентябрь|Октябрь|Ноябрь|Декабрь)\s*(\d{4})?", filename, re.IGNORECASE)
    if match_week:
        month_name = match_week.group(3).capitalize()
        year = match_week.group(4) if match_week.group(4) else "2026"
        period = f"{match_week.group(1)}-{match_week.group(2)}"
        return f"{month_name} {year}", period

    # 3. Try format: "Февраль 2026" or "Февраль"
    match_month = re.search(r"(Январь|Февраль|Март|Апрель|Май|Июнь|Июль|Август|Сентябрь|Октябрь|Ноябрь|Декабрь)\s*(\d{4})?", filename, re.IGNORECASE)
    if match_month:
        month_name = match_month.group(1).capitalize()
        year = match_month.group(2) if match_month.group(2) else "2026"
        return f"{month_name} {year}", "Неизвестно"

    # 4. Try format: "02.2026"
    match_num = re.search(r"(\d{2})\.(\d{4})", filename)
    if match_num:
        month = MONTHS_MAP.get(match_num.group(1), f"{match_num.group(1)}.{match_num.group(2)}")
        return month, "Неизвестно"
    
    return "Неизвестно", "Неизвестно"


def parse_collections_file(filepath: Path) -> Dict[str, Any]:
    """Парсинг файла 'Сборы - ММ 2026.xlsx' с двухтабличной структурой"""
    try:
        df = pd.read_excel(filepath, header=None)
    except Exception as exc:
        print(f"[ERROR] failed to read collections file {filepath.name}: {exc}")
        return {}
    
    # Поиск разделителя между ежедневными сборами и планом
    split_idx = None
    plan_header_idx = None
    for idx, row in df.iterrows():
        row_strs = [str(val).lower().strip() for val in row if pd.notna(val)]
        if any('план' in s and 'мес' in s for s in row_strs) or any('отработанных' in s for s in row_strs) or any('взысканию' in s for s in row_strs):
            if split_idx is None:
                split_idx = idx
            if any('отработанных' in s or 'взысканию' in s for s in row_strs):
                plan_header_idx = idx
                break
                
    if split_idx is None:
        split_idx = len(df)
        
    # 1. Ежедневные сборы (строки от 1 до split_idx)
    data_rows = df.iloc[1:split_idx]
    daily_collections = {}
    
    for _, row in data_rows.iterrows():
        fio = row.iloc[0]
        if pd.isna(fio) or not str(fio).strip() or str(fio).strip() in ('Оператор', 'ФИО'):
            continue
        emp_name = normalize_name(fio)
        if not emp_name:
            continue
            
        amounts = []
        by_day = {}
        for col_idx, val in enumerate(row.iloc[1:], start=1):
            try:
                if pd.isna(val) or str(val).strip() in ('-', ''):
                    continue
                num = float(str(val).replace(' ', '').replace('\xa0', ''))
                if num > 0:
                    amounts.append(num)
                    header_val = df.iloc[0].iloc[col_idx]
                    if hasattr(header_val, 'day'):
                        day = header_val.day
                        by_day[day] = by_day.get(day, 0.0) + num
                    else:
                        by_day[col_idx] = by_day.get(col_idx, 0.0) + num
            except (ValueError, TypeError):
                pass
                
        daily_collections[emp_name] = {
            'collected_amount': sum(amounts),
            'collected_count': len(amounts),
            'by_day': by_day
        }
        
    # 2. План по взысканию (строки после plan_header_idx)
    plans = {}
    if plan_header_idx is not None and plan_header_idx + 1 < len(df):
        plan_rows = df.iloc[plan_header_idx + 1:]
        for _, row in plan_rows.iterrows():
            fio = row.iloc[0]
            if pd.isna(fio) or not str(fio).strip() or 'план' in str(fio).lower():
                continue
            emp_name = normalize_name(fio)
            if not emp_name:
                continue
                
            plan_val = 0.0
            if len(row) > 2:
                try:
                    val = row.iloc[2]
                    if pd.notna(val) and str(val).strip() not in ('-', ''):
                        plan_val = float(str(val).replace(' ', '').replace('\xa0', ''))
                except (ValueError, TypeError):
                    pass
            plans[emp_name] = plan_val

    # 3. Объединение
    result = {}
    for emp_name, col_info in daily_collections.items():
        plan_amount = plans.get(emp_name, 0.0)
        collected_amount = col_info['collected_amount']
        collected_count = col_info['collected_count']
        
        collection_rate = (collected_amount / plan_amount * 100) if plan_amount > 0 else 0.0
        plan_fulfillment = collection_rate
        
        result[emp_name] = {
            'collected_amount': round(collected_amount, 2),
            'collected_count': collected_count,
            'collection_rate': round(collection_rate, 2),
            'plan_fulfillment': round(plan_fulfillment, 2),
            'by_day': col_info['by_day']
        }
    return result


def parse_crm_actions_file(filepath: Path) -> Dict[str, Any]:
    """Парсинг файла 'CRM-действия - ММ 2026.xlsx' с пивотной структурой"""
    try:
        df = pd.read_excel(filepath, header=None)
    except Exception as exc:
        print(f"[ERROR] failed to read CRM actions file {filepath.name}: {exc}")
        return {}
        
    # Поиск строки заголовков
    header_idx = None
    for idx, row in df.iterrows():
        row_strs = [str(val).lower().strip() for val in row if pd.notna(val)]
        if any('названия строк' in s or 'оператор' in s or 'фио' in s for s in row_strs):
            header_idx = idx
            break
            
    if header_idx is None:
        print(f"[WARNING] could not find header row in CRM file {filepath.name}")
        return {}
        
    headers = [str(h).strip() for h in df.iloc[header_idx]]
    data_rows = df.iloc[header_idx + 1:]
    
    result = {}
    for _, row in data_rows.iterrows():
        fio = row.iloc[0]
        if pd.isna(fio) or not str(fio).strip() or 'общий итог' in str(fio).lower() or 'итог' in str(fio).lower():
            continue
        emp_name = normalize_name(fio)
        if not emp_name:
            continue
            
        # Сбор количества действий по каждому типу
        actions = {}
        for col_idx, val in enumerate(row[1:]):
            header = headers[col_idx + 1]
            if not header or 'общий итог' in header.lower() or 'итог' in header.lower():
                continue
            try:
                if pd.isna(val) or str(val).strip() in ('-', ''):
                    count = 0
                else:
                    count = int(float(str(val).replace(' ', '').replace('\xa0', '')))
            except (ValueError, TypeError):
                count = 0
            if count > 0:
                actions[header] = count
                
        # Маппинг русских типов действий на стандартные ключи
        actions_map = {
            'обещал оплатить': 'promised_to_pay',
            'отказ от оплаты': 'refused_payment',
            'думает по поводу оплаты': 'thinking',
            'заявленный платеж': 'declared_payment',
            'бросил трубку': 'hung_up',
            'отказ вести разговор': 'refused_conversation',
            'тишина': 'silence',
        }
        
        mapped_actions = {}
        for k, v in actions.items():
            mapped_key = actions_map.get(k.lower().strip(), 'other')
            mapped_actions[mapped_key] = mapped_actions.get(mapped_key, 0) + v
            
        # Гарантируем наличие всех ключей для структуры
        for key in ['promised_to_pay', 'refused_payment', 'thinking', 'declared_payment', 'hung_up', 'refused_conversation', 'silence', 'other']:
            if key not in mapped_actions:
                mapped_actions[key] = 0
                
        # Определение созданных и завершенных задач
        # Созданные задачи = общее количество звонков (сумма всех колонок)
        # Завершенные задачи = количество результативных звонков (с установленным контактом)
        non_contact_keys = ['Автоответчик', 'Нет ответа', 'Телефон отключен', 'Бросил трубку', 'Тишина', 'Сброс']
        total_actions = sum(actions.values())
        non_contact_actions = sum(v for k, v in actions.items() if any(nc.lower() in k.lower() for nc in non_contact_keys))
        
        tasks_created = total_actions
        tasks_completed = max(0, total_actions - non_contact_actions)
        tasks_rolled_back = 0
        
        mapped_actions['tasks_created'] = tasks_created
        mapped_actions['tasks_completed'] = tasks_completed
        mapped_actions['tasks_rolled_back'] = tasks_rolled_back
        
        behavior_summary = generate_crm_summary(mapped_actions, tasks_completed, tasks_created)
        pattern = identify_behavior_pattern(mapped_actions)
        
        result[emp_name] = {
            'crm_actions': mapped_actions,
            'crm_actions_summary': behavior_summary,
            'crm_behavior_pattern': pattern
        }
    return result


def generate_crm_summary(actions: dict, completed: int, created: int) -> str:
    """Генерация человеко-читаемого вывода по CRM-логике"""
    promised = actions.get('promised_to_pay', 0)
    refused = actions.get('refused_payment', 0)
    thinking = actions.get('thinking', 0)
    
    if refused > promised * 2:
        return "Преобладает пассивная тактика: частые отказы без попытки переговоров"
    elif thinking > promised * 1.5:
        return "Излишне много статусов 'Думает': необходимо дожимать на этапе требования"
    elif promised / max(completed, 1) > 0.7:
        return "Эффективная конверсия обещаний в платежи: высокая настойчивость"
    elif created > completed * 1.5:
        return "Много созданных задач с низкой завершаемостью: требуется контроль дисциплины"
    else:
        return "Сбалансированная рабочая логика"


def identify_behavior_pattern(actions: dict) -> str:
    """Определение паттерна поведения оператора"""
    total_keys = ['promised_to_pay', 'refused_payment', 'thinking', 'declared_payment', 'hung_up', 'refused_conversation', 'silence', 'other']
    total = sum(actions.get(k, 0) for k in total_keys)
    if total == 0: 
        return "balanced"
    
    promised = actions.get('promised_to_pay', 0)
    refused = actions.get('refused_payment', 0)
    avoidant_actions = actions.get('hung_up', 0) + actions.get('silence', 0)
    
    if promised / total > 0.4:
        return "negotiator"  # Переговорщик
    elif refused / total > 0.3:
        return "passive"     # Пассивный
    elif avoidant_actions > total * 0.25:
        return "avoidant"    # Избегающий
    else:
        return "balanced"    # Сбалансированный


def merge_collections_data(data: Dict[str, Any], collections_data: Dict[str, Any], month: str, period: str) -> None:
    for employee, c_info in collections_data.items():
        if employee not in data:
            data[employee] = {"months": {}}
        if month not in data[employee]["months"]:
            data[employee]["months"][month] = {"periods": []}
            
        periods_list = data[employee]["months"][month]["periods"]
        
        if period != "Неизвестно":
            entry = ensure_employee_period(data, employee, month, period)
            entry.update({
                'collected_amount': c_info['collected_amount'],
                'collected_count': c_info['collected_count'],
                'collection_rate': c_info['collection_rate'],
                'plan_fulfillment': c_info['plan_fulfillment']
            })
        else:
            # Месячный отчет: разбиваем сумму и количество по существующим периодам этого месяца
            if not periods_list:
                # Если периодов нет, создаем дефолтный период "Все"
                entry = ensure_employee_period(data, employee, month, "Все")
                entry.update({
                    'collected_amount': c_info['collected_amount'],
                    'collected_count': c_info['collected_count'],
                    'collection_rate': c_info['collection_rate'],
                    'plan_fulfillment': c_info['plan_fulfillment']
                })
            else:
                by_day = c_info.get('by_day', {})
                num_periods = len(periods_list)
                default_split_amount = c_info['collected_amount'] / num_periods
                default_split_count = int(c_info['collected_count'] / num_periods)
                
                for entry in periods_list:
                    p_str = entry['period']
                    match = re.match(r"(\d+)-(\d+)", p_str)
                    
                    period_amount = 0.0
                    period_count = 0
                    has_matching_days = False
                    
                    if match:
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
                        entry['collected_amount'] = round(period_amount, 2)
                        entry['collected_count'] = period_count
                    else:
                        if by_day:
                            entry['collected_amount'] = 0.0
                            entry['collected_count'] = 0
                        else:
                            entry['collected_amount'] = round(default_split_amount, 2)
                            entry['collected_count'] = default_split_count
                        
                    entry['collection_rate'] = c_info['collection_rate']
                    entry['plan_fulfillment'] = c_info['plan_fulfillment']


def merge_crm_data(data: Dict[str, Any], crm_data: Dict[str, Any], month: str, period: str) -> None:
    for employee, crm_info in crm_data.items():
        if employee not in data:
            data[employee] = {"months": {}}
        if month not in data[employee]["months"]:
            data[employee]["months"][month] = {"periods": []}
            
        periods_list = data[employee]["months"][month]["periods"]
        
        if period != "Неизвестно":
            entry = ensure_employee_period(data, employee, month, period)
            entry.update(crm_info)
        else:
            # Месячный отчет: разбиваем числовые счетчики действий на существующие периоды
            if not periods_list:
                entry = ensure_employee_period(data, employee, month, "Все")
                entry.update(crm_info)
            else:
                num_periods = len(periods_list)
                raw_actions = crm_info['crm_actions']
                
                split_actions = {}
                for k, v in raw_actions.items():
                    if isinstance(v, (int, float)):
                        split_actions[k] = int(v / num_periods) if isinstance(v, int) else round(v / num_periods, 2)
                    else:
                        split_actions[k] = v
                        
                for entry in periods_list:
                    entry['crm_actions'] = split_actions.copy()
                    entry['crm_actions_summary'] = crm_info['crm_actions_summary']
                    entry['crm_behavior_pattern'] = crm_info['crm_behavior_pattern']


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
        
    # 1. Сначала считываем файлы качества звонков (Quality)
    quality_files = [f for f in xlsx_files if "Quality" in f.name]
    print(f"[INFO] found {len(quality_files)} Quality XLSX files")
    for xlsx_file in quality_files:
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
        
    # Финализация агрегатов по качеству
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

    # 2. Считываем файлы сборов (Сборы)
    collections_files = [f for f in xlsx_files if "Сборы" in f.name]
    print(f"[INFO] found {len(collections_files)} Collections XLSX files")
    for col_file in collections_files:
        month, period = extract_month_and_period(col_file.name)
        c_data = parse_collections_file(col_file)
        if c_data:
            merge_collections_data(data, c_data, month, period)
            print(f"[INFO] collections from {col_file.name} merged")

    # 3. Считываем файлы CRM-действий (CRM)
    crm_files = [f for f in xlsx_files if "CRM" in f.name]
    print(f"[INFO] found {len(crm_files)} CRM XLSX files")
    for crm_file in crm_files:
        month, period = extract_month_and_period(crm_file.name)
        crm_data = parse_crm_actions_file(crm_file)
        if crm_data:
            merge_crm_data(data, crm_data, month, period)
            print(f"[INFO] CRM actions from {crm_file.name} merged")
            
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
                has_tqs = period.get("tqs", 0) > 0 or period.get("_tqs_values")
                has_collections = period.get("collected_amount", 0) > 0
                if not has_tqs and not has_collections:
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
            Column("collected_amount", Float, default=0.0),
            Column("collected_count", Integer, default=0),
            Column("collection_rate", Float, default=0.0),
            Column("plan_fulfillment", Float, default=0.0),
            Column("crm_actions", JSON, default=dict),
            Column("crm_actions_summary", String, default=""),
            Column("crm_behavior_pattern", String, default=""),
            Column("created_at", DateTime),
            Column("updated_at", DateTime),
            extend_existing=True,
        )
        metadata.create_all(engine, checkfirst=True)

        # Run SQL migrations to ensure columns exist
        from sqlalchemy import text
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
            print(f"[WARN] Error running automatic database migrations in updater: {e}")

        with engine.begin() as conn:
            for employee_name, employee_data in data.items():
                for month, month_data in employee_data["months"].items():
                    for period_item in month_data["periods"]:
                        row = {
                            "employee_name": employee_name,
                            "month": month,
                            "period": period_item["period"],
                            "tqs": float(period_item.get("tqs", 0.0) or 0.0),
                            "aht": str(period_item.get("aht", "N/A")),
                            "activity_count": int(period_item.get("activity_count", 0)),
                            "svp_scores": period_item.get("svp", {}),
                            "raw_scores": period_item.get("raw_scores", {}),
                            "tendencies": period_item.get("tendencies", ""),
                            "recommendations": period_item.get("rec", ""),
                            "collected_amount": float(period_item.get("collected_amount", 0.0)),
                            "collected_count": int(period_item.get("collected_count", 0)),
                            "collection_rate": float(period_item.get("collection_rate", 0.0)),
                            "plan_fulfillment": float(period_item.get("plan_fulfillment", 0.0)),
                            "crm_actions": period_item.get("crm_actions", {}),
                            "crm_actions_summary": period_item.get("crm_actions_summary", ""),
                            "crm_behavior_pattern": period_item.get("crm_behavior_pattern", ""),
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

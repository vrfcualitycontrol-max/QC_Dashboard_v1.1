"""
Модуль парсинга файлов данных QC Dashboard.
Парсит XLSX (Quality, Сборы, CRM-действия) и PDF (Промежуточный отчёт).
Определяет тип файла АВТОМАТИЧЕСКИ по содержимому.
"""

import io
import re
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import pdfplumber

# === КОНСТАНТЫ ===
XLSX_SHEET_NAME = "Оценки звонков Soft Collection"
SVP_COLUMNS_INDICES = list(range(6, 15))
TQS_INDEX = 15
DURATION_INDEX = 5
EMPLOYEE_INDEX = 0

SVP_KEYS = [
    "Приветствие", "Этика", "CRM", "Легенда", "Задолж.",
    "Аргумент.", "Манипул.", "Требования", "Итоги",
]

MONTHS_MAP = {
    "01": "Январь 2026", "02": "Февраль 2026", "03": "Март 2026",
    "04": "Апрель 2026", "05": "Май 2026", "06": "Июнь 2026",
    "07": "Июль 2026", "08": "Август 2026", "09": "Сентябрь 2026",
    "10": "Октябрь 2026", "11": "Ноябрь 2026", "12": "Декабрь 2026"
}

# === NAME_MAP ===
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
    
    # --- Новые вариации кириллицы (обнаружены в Июнь 2026) ---
    "Исаков Давронбек":      "Исаков Даврон",
    "Исматиллаев Нодирбек":  "Исматиллайев Нодирбек",
    "Мамарайимов Фирдавс":   "Мамараимов Фирдавс",
    "Сабуров Огабек":         "Сабуров Оғабек",
    "Хакимов Умиджон":        "Хакимов Умид",
    "Шавкатов Гафур":         "Шавкатов Гофур",
    "Шавкат Гофур":           "Шавкатов Гофур",

    # --- Новые сотрудники (впервые появились в Июнь 2026) ---
    "Турсунова Лола":         "Турсунова Лола",
    "Сайрихонов Санжар":      "Сайрихонов Санжар",
    "Жанибеков Марат":        "Жанибеков Марат",
    "Камалиддинов Иззат":     "Камалиддинов Иззат",

    # --- Новые подробные латинские сопоставления ---
    "Alkarov Jamshid Berkin O'G'Li": "Алкаров Жамшид",
    "Alkarov Jamshid Berkin O":     "Алкаров Жамшид",
    "Sayrixonov Sanjar Azizxon O'G'Li": "Сайрихонов Санжар",
    "Sayrixonov Sanjar":            "Сайрихонов Санжар",
    "Qurolboyev Javohir Javlonbek O'G'Li": "Куролбоев Жавохир",
    "Isakov Davronbek Toxirjon O'G'Li": "Исаков Даврон",
    "Hakimov Umidjon Hamidjon O'G'Li": "Хакимов Умид",
    "Nadrullayeva Ruhsona Ulug'bek Qizi": "Надруллаева Рухсона",
    "Sabitova Navruza Xamidulla Qizi": "Сабитова Навруза",
    "Shavkat G'Ofur Alisher O'Gli": "Шавкатов Гофур",
    "Shamiyev Farrux Ziyodulla O'G'Li": "Шамиев Фаррух",
    "Tojiyev Shoxrux Fayzulla O'G'Li": "Тожиев Шохрух",
    "Janibekov Marat Allamurat O'G'Li": "Жанибеков Марат",
    "Nizomiddinov Asliddin Sharofiddinovich": "Низомиддинов Аслиддин",
    "Saburov Og'Abek Mansurbek O'G'Li": "Сабуров Оғабек",
    "Tursunova Lola Zokirjon Qizi": "Турсунова Лола",
    "Mamarayimov Firdavs Botirali O'G'Li": "Мамараимов Фирдавс",
    "Musayev Xurshid Odil O'G'Li": "Мусаев Хуршид",
    "Ismatillayev Nodirbek O'Ktam O'G'Li": "Исматиллайев Нодирбек",
}
for cyr in list(NAME_MAP.values()):
    NAME_MAP[cyr] = cyr

CHAR_NORMALIZE_MAP = {
    'Ғ': 'Г', 'ғ': 'г',
    'Қ': 'К', 'қ': 'к',
    'Ҳ': 'Х', 'ҳ': 'х',
    'Ў': 'У', 'ў': 'у',
    'Ё': 'Е', 'ё': 'е',
    'Ъ': '', 'ъ': '',
    '’': "'", '`': "'", '‘': "'",
}

def normalize_chars(text: str) -> str:
    """Нормализация спец. символов для сравнения."""
    for orig, repl in CHAR_NORMALIZE_MAP.items():
        text = text.replace(orig, repl)
    return text

def levenshtein_distance(s1: str, s2: str) -> int:
    """Вычисляет расстояние Левенштейна между двумя строками (без внешних библиотек)."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def fuzzy_match_name(name: str, known_names: list, threshold: int = 4) -> Optional[str]:
    """Нечёткое сопоставление ФИО."""
    name_parts = name.split()
    if not name_parts:
        return None
    
    surname = name_parts[0]
    given_name = name_parts[1] if len(name_parts) > 1 else ""
    
    best_match = None
    best_score = threshold + 1
    
    for known in known_names:
        known_parts = known.split()
        if not known_parts:
            continue
        
        known_surname = known_parts[0]
        known_given = known_parts[1] if len(known_parts) > 1 else ""
        
        # Сравнение фамилий
        surname_dist = levenshtein_distance(
            normalize_chars(surname.lower()),
            normalize_chars(known_surname.lower())
        )
        if surname_dist > 2:
            continue
        
        # Проверка начала имени
        given_lower = normalize_chars(given_name.lower())
        known_given_lower = normalize_chars(known_given.lower())
        
        if given_lower and known_given_lower:
            if given_lower.startswith(known_given_lower) or known_given_lower.startswith(given_lower):
                if surname_dist <= 1:
                    return known
        
        # Полное расстояние
        full_dist = levenshtein_distance(
            normalize_chars(name.lower()),
            normalize_chars(known.lower())
        )
        
        if full_dist < best_score:
            best_score = full_dist
            best_match = known
    
    return best_match if best_score <= threshold else None

def normalize_name(name: Any) -> str:
    """Нормализация имени сотрудника."""
    if pd.isna(name):
        return ""
    text = str(name).strip()
    if not text:
        return ""
    
    # 1. Прямой маппинг
    if text in NAME_MAP:
        return NAME_MAP[text]
    
    # 2. Поиск с нормализованными символами
    normalized_text = normalize_chars(text.lower())
    for key, canonical in NAME_MAP.items():
        if normalize_chars(key.lower()) == normalized_text:
            NAME_MAP[text] = canonical
            return canonical
    
    # 3. Fuzzy matching
    canonical_names = list(set(NAME_MAP.values()))
    best_match = fuzzy_match_name(text, canonical_names)
    if best_match:
        NAME_MAP[text] = best_match
        return best_match
    
    # 4. Не нашли
    return text

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
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
    if minutes <= 0:
        return "N/A"
    total_seconds = int(minutes * 60)
    mins = total_seconds // 60
    secs = total_seconds % 60
    return f"{mins:02d}:{secs:02d}"

def extract_month_and_period(filename: str) -> Tuple[str, str]:
    filename_lower = filename.lower()
    
    # Map Russian month names to month index and month string
    ru_months = {
        "янв": ("01", "Январь 2026"),
        "фев": ("02", "Февраль 2026"),
        "мар": ("03", "Март 2026"),
        "апр": ("04", "Апрель 2026"),
        "май": ("05", "Май 2026"),
        "июн": ("06", "Июнь 2026"),
        "июл": ("07", "Июль 2026"),
        "авг": ("08", "Август 2026"),
        "сен": ("09", "Сентябрь 2026"),
        "окт": ("10", "Октябрь 2026"),
        "ноя": ("11", "Ноябрь 2026"),
        "дек": ("12", "Декабрь 2026")
    }
    
    # 1. Match: "за период 1-8.02.26" or "за период 01-08.03.26"
    match_period_dot = re.search(r"(\d{1,2})[-_](\d{1,2})\.(\d{2})\.(\d{2,4})", filename)
    if match_period_dot:
        day1 = f"{int(match_period_dot.group(1)):02d}"
        day2 = f"{int(match_period_dot.group(2)):02d}"
        month_num = match_period_dot.group(3)
        month_str = MONTHS_MAP.get(month_num, f"Месяц {month_num} 2026")
        return month_str, f"{day1}-{day2}"
        
    # Match: "01-07 июнь 2026"
    match_week = re.search(r"(\d{1,2})[-_](\d{1,2})\s+([а-яА-Яa-zA-Z]+)", filename)
    if match_week:
        day1 = f"{int(match_week.group(1)):02d}"
        day2 = f"{int(match_week.group(2)):02d}"
        month_name = match_week.group(3).lower()
        found_month = "Неизвестно"
        for key, (num, val) in ru_months.items():
            if key in month_name:
                found_month = val
                break
        return found_month, f"{day1}-{day2}"

    # Match: "01.02.2026 - 08.02.2026"
    match_range_full = re.search(r"(\d{2})\.(\d{2})\.(\d{4})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})", filename)
    if match_range_full:
        month = MONTHS_MAP.get(match_range_full.group(2), f"Месяц {match_range_full.group(2)} 2026")
        period = f"{match_range_full.group(1)}-{match_range_full.group(4)}"
        return month, period

    # Match: "13-19.04.2026"
    match_range_short = re.search(r"(\d{2})-(\d{2})\.(\d{2})\.(\d{4})", filename)
    if match_range_short:
        month = MONTHS_MAP.get(match_range_short.group(3), f"Месяц {match_range_short.group(3)} 2026")
        period = f"{match_range_short.group(1)}-{match_range_short.group(2)}"
        return month, period

    # 2. Match: "февраль 2026" or just "февраль" (monthly file)
    for key, (num, val) in ru_months.items():
        if key in filename_lower:
            return val, "Все"

    # Match: "02.2026" or "02.26"
    match_num = re.search(r"(\d{2})\.(\d{2,4})", filename)
    if match_num:
        month_num = match_num.group(1)
        month = MONTHS_MAP.get(month_num, f"Месяц {month_num} 2026")
        return month, "Все"

    return "Неизвестно", "Неизвестно"


def generate_crm_summary(actions: dict, completed: int, created: int) -> str:
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
    total_keys = ['promised_to_pay', 'refused_payment', 'thinking', 'declared_payment', 'hung_up', 'refused_conversation', 'silence', 'other']
    total = sum(actions.get(k, 0) for k in total_keys)
    if total == 0: 
        return "balanced"
    
    promised = actions.get('promised_to_pay', 0)
    refused = actions.get('refused_payment', 0)
    avoidant_actions = actions.get('hung_up', 0) + actions.get('silence', 0)
    
    if promised / total > 0.4:
        return "negotiator"
    elif refused / total > 0.3:
        return "passive"
    elif avoidant_actions > total * 0.25:
        return "avoidant"
    else:
        return "balanced"

# === ОПРЕДЕЛЕНИЕ ТИПА ФАЙЛА ===
def detect_file_type(file_bytes: bytes, filename: str) -> str:
    lower_name = filename.lower()
    
    if lower_name.endswith('.pdf'):
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = ""
                for page in pdf.pages[:3]:
                    text += (page.extract_text() or "") + "\n"
            if re.search(r"Отчет\s+по\s+сотруднику", text, re.IGNORECASE):
                return "report"
        except Exception:
            pass
        return "unknown"
    
    if lower_name.endswith('.xlsx'):
        try:
            xls = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
            sheet_names = xls.sheet_names
            
            if XLSX_SHEET_NAME in sheet_names:
                return "quality"
            
            df = pd.read_excel(io.BytesIO(file_bytes), header=None, engine="openpyxl")
            
            for idx in range(min(5, len(df))):
                row_strs = [str(val).lower().strip() for val in df.iloc[idx] if pd.notna(val)]
                if any('названия строк' in s for s in row_strs):
                    return "crm"
            
            all_text = " ".join(str(val).lower() for val in df.values.flatten() if pd.notna(val))
            has_plan = 'план' in all_text and ('взысканию' in all_text or 'отработанных' in all_text)
            has_operator = any(
                'оператор' in str(df.iloc[0].iloc[c]).lower() or 'фио' in str(df.iloc[0].iloc[c]).lower()
                for c in range(min(3, df.shape[1]))
                if pd.notna(df.iloc[0].iloc[c])
            )
            if has_plan or has_operator:
                return "collections"
                
        except Exception:
            pass
        return "unknown"
    
    return "unknown"

# === ПАРСИНГ ИЗ BYTES ===
def parse_quality_bytes(file_bytes: bytes, filename: str) -> Tuple[str, str, Dict]:
    month, period = extract_month_and_period(filename)
    df = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=XLSX_SHEET_NAME,
        engine="openpyxl",
        header=2
    )
    
    raw_data = {}
    for _, row in df.iterrows():
        employee = normalize_name(row.iloc[EMPLOYEE_INDEX])
        if not employee:
            continue
        
        tqs = parse_score(row.iloc[TQS_INDEX])
        duration = parse_duration(row.iloc[DURATION_INDEX])
        svp_values = [parse_score(row.iloc[idx]) for idx in SVP_COLUMNS_INDICES]
        
        if employee not in raw_data:
            raw_data[employee] = {
                "_tqs_values": [],
                "_durations": [],
                "_activity_count": 0,
                "raw_scores": {key: [] for key in SVP_KEYS},
            }
        
        raw_data[employee]["_tqs_values"].append(tqs)
        raw_data[employee]["_durations"].append(duration)
        raw_data[employee]["_activity_count"] += 1
        for key, value in zip(SVP_KEYS, svp_values):
            raw_data[employee]["raw_scores"][key].append(value)
            
    result = {}
    for emp, emp_data in raw_data.items():
        tqs_avg = round(mean(emp_data["_tqs_values"]), 2) if emp_data["_tqs_values"] else 0.0
        aht_avg = format_duration(mean(emp_data["_durations"])) if emp_data["_durations"] else "N/A"
        svp = {}
        for key in SVP_KEYS:
            if emp_data["raw_scores"][key]:
                svp[key] = round(mean(emp_data["raw_scores"][key]), 2)
            else:
                svp[key] = 1.0
                
        result[emp] = {
            "tqs": tqs_avg,
            "aht": aht_avg,
            "svp": svp,
            "raw_scores": emp_data["raw_scores"],
            "activity_count": emp_data["_activity_count"],
        }
    return month, period, result

def parse_collections_bytes(file_bytes: bytes, filename: str) -> Tuple[str, str, Dict]:
    month, period = extract_month_and_period(filename)
    df = pd.read_excel(io.BytesIO(file_bytes), header=None, engine="openpyxl")
    
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
                    else:
                        day = col_idx
                    by_day[day] = by_day.get(day, 0.0) + num
            except (ValueError, TypeError):
                pass
                
        daily_collections[emp_name] = {
            'collected_amount': sum(amounts),
            'collected_count': len(amounts),
            'by_day': by_day
        }
        
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
    return month, period, result

def parse_crm_bytes(file_bytes: bytes, filename: str) -> Tuple[str, str, Dict]:
    month, period = extract_month_and_period(filename)
    df = pd.read_excel(io.BytesIO(file_bytes), header=None, engine="openpyxl")
    
    header_idx = None
    for idx, row in df.iterrows():
        row_strs = [str(val).lower().strip() for val in row if pd.notna(val)]
        if any('названия строк' in s or 'оператор' in s or 'фио' in s for s in row_strs):
            header_idx = idx
            break
            
    if header_idx is None:
        return month, period, {}
        
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
            
        for key in ['promised_to_pay', 'refused_payment', 'thinking', 'declared_payment', 'hung_up', 'refused_conversation', 'silence', 'other']:
            if key not in mapped_actions:
                mapped_actions[key] = 0
                
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
    return month, period, result

def extract_pdf_sections(text: str) -> List[str]:
    parts = re.split(r"Отчет\s+по\s+сотруднику\s*[:：]", text, flags=re.IGNORECASE)
    return [part.strip() for part in parts if part.strip()]

def extract_section_text(block: str, key: str) -> str:
    pattern = re.search(fr"{re.escape(key)}\s*[:：]?\s*", block, flags=re.IGNORECASE)
    if not pattern:
        return ""
    
    start_pos = pattern.end()
    remaining = block[start_pos:]
    
    if "рекомендаци" in key.lower():
        match_break = re.search(r"\n\s*\n", remaining)
        if match_break:
            text = remaining[:match_break.start()]
        else:
            text = remaining
    else:
        match_newline = re.search(r"\n", remaining)
        if match_newline:
            text = remaining[:match_newline.start()]
        else:
            text = remaining
            
    return text.strip().replace("\n", " ").replace("\r", " ")

def parse_report_pdf_bytes(file_bytes: bytes, filename: str) -> Tuple[str, str, Dict]:
    month, period = extract_month_and_period(filename)
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as exc:
        raise ValueError(f"Failed to parse PDF: {exc}")
        
    sections = extract_pdf_sections(text)
    result = {}
    for section in sections:
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        if not lines:
            continue
        employee = normalize_name(lines[0])
        if not employee:
            continue
        result[employee] = {
            "tendencies": extract_section_text(section, "Тенденции"),
            "rec": extract_section_text(section, "Рекомендации")
        }
    return month, period, result

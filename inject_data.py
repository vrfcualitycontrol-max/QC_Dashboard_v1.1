import os
import re
import json
import traceback
import pandas as pd
import pdfplumber

INDEX_HTML_PATH = "index.html"
DIRECTORY = "."

MONTHS_MAP = {
    "01": "Январь 2026", "02": "Февраль 2026", "03": "Март 2026", "04": "Апрель 2026",
    "05": "Май 2026", "06": "Июнь 2026", "07": "Июль 2026", "08": "Август 2026",
    "09": "Сентябрь 2026", "10": "Октябрь 2026", "11": "Ноябрь 2026", "12": "Декабрь 2026"
}

SVP_KEYS = [
    "Приветствие", "Этика", "CRM", "Легенда", "Задолж.",
    "Аргумент.", "Манипул.", "Требования", "Итоги"
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

def get_month_and_period(filename):
    match = re.search(r'(\d{1,2})\.(\d{2})\.\d{4}\s*-\s*(\d{1,2})\.\d{2}\.\d{4}', filename)
    if match:
        p1 = match.group(1).zfill(2)
        p2 = match.group(3).zfill(2)
        return MONTHS_MAP.get(match.group(2), "Неизвестно"), f"{p1}-{p2}"
    
    match = re.search(r'(\d{1,2})-(\d{1,2})\.(\d{2})\.\d{2,4}', filename)
    if match:
        p1 = match.group(1).zfill(2)
        p2 = match.group(2).zfill(2)
        return MONTHS_MAP.get(match.group(3), "Неизвестно"), f"{p1}-{p2}"
    
    return "Неизвестно", "Неизвестно"

dashboard_data = {}

def ensure_employee_month(emp_name, month):
    if emp_name not in dashboard_data:
        dashboard_data[emp_name] = {"months": {}}
    if month not in dashboard_data[emp_name]["months"]:
        dashboard_data[emp_name]["months"][month] = {"periods": []}
    return dashboard_data[emp_name]["months"][month]["periods"]

def process_excel(file_path):
    print(f"Reading EXCEL: {file_path}")
    month, period = get_month_and_period(os.path.basename(file_path))
    if month == "Неизвестно": return
    
    try:
        df = pd.read_excel(file_path, sheet_name="Оценки звонков Soft Collection", header=None)
    except:
        print("Failed to read excel")
        return
    
    emp_stats = {}
    for _, row in df.iterrows():
        raw_name = str(row[0]).strip()
        if raw_name in NAME_MAP:
            emp = NAME_MAP[raw_name]
            if emp not in emp_stats:
                emp_stats[emp] = {'tqs': [], 'aht': [], 'svp': {k: [] for k in SVP_KEYS}}
            
            try:
                tqs_val = float(row[15]) if pd.notna(row[15]) else 0.0
                emp_stats[emp]['tqs'].append(tqs_val)
                if pd.notna(row[5]):
                    emp_stats[emp]['aht'].append(str(row[5]))
                for idx, k in enumerate(SVP_KEYS):
                    v = row[6 + idx]
                    if pd.notna(v):
                        emp_stats[emp]['svp'][k].append(float(v))
            except Exception:
                pass

    for emp, stats in emp_stats.items():
        if not stats['tqs']: continue
        
        periods = ensure_employee_month(emp, month)
        # Check if period already exists, remove it if so (unlikely as we start fresh)
        p_data = {
            "period": period,
            "tqs": round(sum(stats['tqs']) / len(stats['tqs']) * 100, 1), # one decimal like 79.8
            "aht": stats['aht'][0] if stats['aht'] else "N/A",
            "svp": {},
            "raw_scores": {},
            "tendencies": "",
            "rec": ""
        }
        for k in SVP_KEYS:
            if stats['svp'][k]:
                p_data['svp'][k] = round(sum(stats['svp'][k]) / len(stats['svp'][k]), 2)
                p_data['raw_scores'][k] = stats['svp'][k]
            else:
                p_data['svp'][k] = 1.0 # Default missing to 1.0
                p_data['raw_scores'][k] = [1.0]
                
        periods.append(p_data)
        periods.sort(key=lambda x: x["period"])


def _extract_block(text, label_root, stop_roots):
    pattern = rf'{label_root}.*?(?=\n\s*(?:{"|".join(stop_roots)}))'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        content = match.group(0)
        content = re.sub(rf'^{label_root}.*?\n?', '', content, flags=re.IGNORECASE).strip()
        return content
    pattern_end = rf'{label_root}.*'
    match_end = re.search(pattern_end, text, re.DOTALL | re.IGNORECASE)
    if match_end:
        content = match_end.group(0)
        content = re.sub(rf'^{label_root}.*?\n?', '', content, flags=re.IGNORECASE).strip()
        return content
    return ""

def process_pdf(file_path):
    print(f"Reading PDF: {file_path}")
    month, period = get_month_and_period(os.path.basename(file_path))
    if month == "Неизвестно": return
    
    try:
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except:
        print("Failed to read pdf")
        return
        
    blocks = re.split(r'Отчет\s+по\s+сотруднику\s*[:\uff1a]\s*', text)
    for block in blocks[1:]:
        name_match = re.match(r'([A-Za-z\u0410-\u042f\u0401\u0430-\u044f\u0451\u0492\u0493\-\'\s]{3,50})', block)
        if not name_match: continue
            
        emp_name = name_match.group(1).strip()
        if emp_name in NAME_MAP:
            emp_name = NAME_MAP[emp_name]
        else: continue
        
        tendencies = _extract_block(block, r'Тенденци[\ияюей]', [r'Приоритет', r'Оценки', r'Рекомендац', r'Итог'])
        rec = _extract_block(block, r'Рекомендац[\ияюей]', [r'Приоритет', r'Оценки', r'Тенденци', r'Итог'])
        
        # Attach to existing period if found
        if emp_name in dashboard_data and month in dashboard_data[emp_name]["months"]:
            for p in dashboard_data[emp_name]["months"][month]["periods"]:
                if p["period"] == period:
                    p["tendencies"] = tendencies
                    p["rec"] = rec

def run():
    # 1. Gather files
    files = os.listdir(DIRECTORY)
    excels = [f for f in files if f.lower().endswith('.xlsx') and not f.startswith('~')]
    pdfs = [f for f in files if f.lower().endswith('.pdf') and not f.startswith('~')]
    
    for x in excels: process_excel(os.path.join(DIRECTORY, x))
    for p in pdfs: process_pdf(os.path.join(DIRECTORY, p))
    
    # 2. Inject to HTML
    with open(INDEX_HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_json = json.dumps(dashboard_data, ensure_ascii=False, indent=2)
    safe_json = new_json.replace('\\', '\\\\')
    
    marker_full_pattern = re.compile(
        r'// --- DATA START ---\s*\n.*?// --- DATA END ---',
        re.DOTALL
    )
    
    # Clean up MARCH_RAW if exists
    content = re.sub(r'const\s+MARCH_RAW\s*=\s*\{.*?\};\s*', '', content, flags=re.DOTALL)
    
    new_content = re.sub(
        marker_full_pattern,
        f'// --- DATA START ---\n    const DASHBOARD_DATA = {safe_json};\n// --- DATA END ---',
        content
    )
    
    with open(INDEX_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Done generating & injecting.")

if __name__ == "__main__":
    run()

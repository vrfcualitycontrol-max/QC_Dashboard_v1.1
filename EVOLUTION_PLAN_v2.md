# ИНСТРУКЦИЯ ДЛЯ АГЕНТА-ИСПОЛНИТЕЛЯ: Эволюция QC Dashboard SC v2.0

> **ВАЖНО:** Этот документ — пошаговая инструкция. Выполняй шаги ПОСЛЕДОВАТЕЛЬНО, не пропуская.
> После каждой фазы — проверяй результат перед переходом к следующей.

---

## ОГЛАВЛЕНИЕ

1. [Обзор проекта и текущее состояние](#1-обзор-проекта-и-текущее-состояние)
2. [Целевая архитектура](#2-целевая-архитектура)
3. [ФАЗА 1: Исправление дублирования сотрудников](#3-фаза-1-исправление-дублирования-сотрудников)
4. [ФАЗА 2: Перенос парсинга в бэкенд](#4-фаза-2-перенос-парсинга-в-бэкенд)
5. [ФАЗА 3: Встроенный интерфейс загрузки файлов](#5-фаза-3-встроенный-интерфейс-загрузки-файлов)
6. [ФАЗА 4: Переход фронтенда на API mode](#6-фаза-4-переход-фронтенда-на-api-mode)
7. [ФАЗА 5: Адаптивная мобильная версия](#7-фаза-5-адаптивная-мобильная-версия)
8. [ФАЗА 6: Деплой на VPS RackNerd](#8-фаза-6-деплой-на-vps-racknerd)
9. [ФАЗА 7: CI/CD — механизм обновления](#9-фаза-7-cicd--механизм-обновления)
10. [Чеклист финальной проверки](#10-чеклист-финальной-проверки)

---

## 1. Обзор проекта и текущее состояние

### Что это за проект

QC Dashboard SC — аналитический дашборд для отдела Quality Control подразделения Soft Collection. Показывает метрики операторов: TQS (качество звонков), AHT (среднее время), SVP (структура ведения переговоров), финансовые сборы, CRM-действия.

### Структура файлов проекта (ТЕКУЩАЯ)

```
Dashboard_SC/
├── index.html                    # Редирект на analytics.html
├── analytics.html                # Главная страница — аналитика
├── rating.html                   # Рейтинг сотрудников
├── forecast.html                 # Прогнозирование (заглушка)
├── objections_b2c.html           # База возражений B2C
├── objections_b2b.html           # База возражений B2B
├── svp_mechanism.html            # Порядок механизма СВП
├── svp_crm.html                  # CRM Soft Collection
├── law.html                      # Нормативная аргументация
├── instruments.html              # Инструментарий
├── manual.html                   # Мануал
├── reg_mechanics.html            # Механика оценки
├── reg_methodology.html          # Методология (9 крит.)
├── qc_regulations.html           # Регламент QC
├── reg_base.html, reg_rules.html # Доп. регламентные страницы
│
├── assets/
│   ├── css/style.css             # Единый файл стилей (~42KB)
│   └── js/
│       ├── data.js               # DASHBOARD_DATA (~1.1MB, генерируется auto_updater.py)
│       ├── app.js                # Основная логика фронтенда (~139KB, 2570 строк)
│       ├── core.js               # Тема + сайдбар (для info-страниц)
│       ├── sidebar.js            # Генерация sidebar навигации
│       ├── tactical-data.js      # Статические данные для тактических инструментов
│       └── tactical-pages.js     # Логика тактических страниц
│
├── backend/
│   ├── app.py                    # FastAPI бэкенд (547 строк)
│   ├── requirements.txt          # Зависимости бэкенда
│   ├── Dockerfile                # Docker-образ бэкенда
│   └── reports/                  # (пусто, bind mount к корневому reports/)
│
├── auto_updater.py               # Парсер XLSX/PDF → data.js + PostgreSQL (1032 строки)
├── reports/                      # Исходные файлы данных (51 файл)
│
├── docker-compose.yml            # PostgreSQL + Backend + Nginx
├── Dockerfile                    # Nginx для фронтенда
├── nginx.conf                    # Конфиг nginx (проксирование /api/)
├── .env                          # Переменные окружения
├── requirements.txt              # Зависимости auto_updater.py
├── logo/                         # Логотип
├── content/                      # Контент
├── docs/                         # Документация
├── scripts/                      # Скрипты
├── security/                     # Безопасность
├── tests/                        # Тесты
└── venv/                         # Виртуальное окружение Python
```

### Текущий flow данных (ПРОБЛЕМНЫЙ)

```
1. Пользователь кладёт файлы в reports/
2. Запускает auto_updater.py
3. auto_updater.py парсит файлы → записывает в assets/js/data.js (и в PostgreSQL)
4. Фронтенд читает DASHBOARD_DATA из data.js (1.1MB глобальная переменная)
5. Бэкенд (FastAPI) есть, но фронтенд его НЕ использует
```

### Файлы данных (reports/)

Четыре типа файлов за каждый недельный период:

| # | Тип | Пример имени файла | Формат | Что содержит |
|---|-----|---------------------|--------|-------------|
| 1 | Quality | `Quality 01.06.2026 - 07.06.2026.xlsx` | XLSX, лист "Оценки звонков Soft Collection" | TQS, SVP по 9 критериям, AHT |
| 2 | Сборы | `Сборы - 01-07 Июнь 2026.xlsx` | XLSX, таблица ежедневных сборов + план | Суммы собранных оплат, план |
| 3 | CRM-действия | `CRM-действия - 01-07 июнь 2026.xlsx` | XLSX, пивотная таблица | Типы действий операторов |
| 4 | Промежуточный отчёт | `Промежуточный отчет по сотрудникам SC за период 01-07.06.2026.pdf` | PDF | Тенденции и рекомендации |

---

## 2. Целевая архитектура

### Целевой flow данных (ПОСЛЕ ЭВОЛЮЦИИ)

```
1. Пользователь открывает дашборд в браузере → вкладка "Загрузка данных"
2. Drag & drop файлов → POST /api/upload → бэкенд определяет тип файла автоматически
3. Бэкенд парсит файл → записывает в PostgreSQL (с нормализацией имён)
4. Фронтенд запрашивает данные через GET /api/metrics
5. auto_updater.py и data.js больше не нужны
```

### Целевая инфраструктура (VPS RackNerd)

```
VPS RackNerd (Linux)
├── Docker Compose
│   ├── postgres:16-alpine      (PostgreSQL, данные на volume)
│   ├── qc-backend              (FastAPI + Uvicorn, парсинг встроен)
│   └── nginx                   (Фронтенд + реверс-прокси /api/ → backend)
├── Certbot/Let's Encrypt       (SSL/HTTPS)
├── Swap файл                   (подкачка для экономии RAM)
├── Systemd                     (автозапуск docker-compose)
└── Git repo                    (для деплоя обновлений)
```

### Оптимизация ресурсов VPS

- **Swap**: создать файл подкачки 2GB (для VPS с 1-2GB RAM)
- **PostgreSQL**: ограничить shared_buffers, work_mem
- **Backend**: один worker Uvicorn (не несколько)
- **Nginx**: статические файлы из кеша, gzip
- **Docker**: ограничить memory для контейнеров

---

## 3. ФАЗА 1: Исправление дублирования сотрудников [ВЫПОЛНЕНО]

### Проблема

В данных за период «01-07 Июнь 2026» обнаружены дубликаты сотрудников. Один и тот же человек фигурирует под разными вариантами написания ФИО (отличия в буквах кириллицы, сокращённые/полные имена). В итоге в интерфейсе появляются «призраки» — сотрудники с нулевыми TQS/AHT, но с данными по сборам.

### Обнаруженные дубликаты

| Каноническое имя (из Quality) | Дубликат (из Сборов/CRM) | Тип различия |
|---|---|---|
| `Исаков Даврон` | `Исаков Давронбек` | Краткое vs полное имя |
| `Исматиллайев Нодирбек` | `Исматиллаев Нодирбек` | Пропущена буква `й` |
| `Мамараимов Фирдавс` | `Мамарайимов Фирдавс` | `и` → `й` |
| `Сабуров Оғабек` | `Сабуров Огабек` | Спец. символ `Ғ` → обычная `Г` |
| `Хакимов Умид` | `Хакимов Умиджон` | Краткое vs полное имя |
| `Шавкатов Гофур` | `Шавкатов Гафур` и `Шавкат Гофур` | `о`→`а` в имени + фамилия без окончания |

### Что нужно сделать

#### Шаг 1.1: Реализовать функцию расстояния Левенштейна

В файле `auto_updater.py` (позже перенесётся в `backend/parser.py`), добавь функцию:

```python
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
```

#### Шаг 1.2: Реализовать таблицу эквивалентных символов

Некоторые буквы визуально похожи или являются вариациями:

```python
# Таблица замен для нормализации специфичных символов
CHAR_NORMALIZE_MAP = {
    'Ғ': 'Г', 'ғ': 'г',
    'Қ': 'К', 'қ': 'к',
    'Ҳ': 'Х', 'ҳ': 'х',
    'Ў': 'У', 'ў': 'у',
    'Ё': 'Е', 'ё': 'е',
    'Ъ': '', 'ъ': '',  # мягкий/твёрдый знак — убрать для сравнения
}

def normalize_chars(text: str) -> str:
    """Нормализация спец. символов для сравнения."""
    for orig, repl in CHAR_NORMALIZE_MAP.items():
        text = text.replace(orig, repl)
    return text
```

#### Шаг 1.3: Расширить NAME_MAP всеми известными вариациями

Открой `auto_updater.py`, найди `NAME_MAP` (строки 100-131). **Добавь** следующие записи:

```python
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
```

#### Шаг 1.4: Переписать функцию normalize_name() с fuzzy fallback

Замени текущую `normalize_name()` (строка 133-137 в auto_updater.py):

```python
def normalize_name(name: Any) -> str:
    """
    Нормализация имени сотрудника.
    1. Прямой поиск в NAME_MAP
    2. Поиск с нормализацией спец. символов
    3. Fuzzy matching по расстоянию Левенштейна
    """
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
            NAME_MAP[text] = canonical  # кэшируем для следующих вызовов
            return canonical
    
    # 3. Fuzzy matching — ищем ближайшее совпадение среди каноничных имён
    canonical_names = list(set(NAME_MAP.values()))
    best_match = fuzzy_match_name(text, canonical_names)
    if best_match:
        NAME_MAP[text] = best_match  # кэшируем
        return best_match
    
    # 4. Не нашли — возвращаем как есть (новый сотрудник)
    return text


def fuzzy_match_name(name: str, known_names: list, threshold: int = 4) -> Optional[str]:
    """
    Нечёткое сопоставление ФИО.
    Правила:
    - Фамилия (первое слово) должна совпадать с порогом ≤ 2
    - Полное ФИО должно совпадать с порогом ≤ threshold
    - Одно имя может быть подстрокой другого (Даврон ⊂ Давронбек)
    """
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
        
        # Сравнение фамилий (с нормализацией спец. символов)
        surname_dist = levenshtein_distance(
            normalize_chars(surname.lower()),
            normalize_chars(known_surname.lower())
        )
        if surname_dist > 2:
            continue
        
        # Проверка: одно имя является началом другого (Даврон → Давронбек)
        given_lower = normalize_chars(given_name.lower())
        known_given_lower = normalize_chars(known_given.lower())
        
        if given_lower and known_given_lower:
            if given_lower.startswith(known_given_lower) or known_given_lower.startswith(given_lower):
                # Совпадение по подстроке — высокий приоритет
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
```

#### Шаг 1.5: Проверка

После внесения изменений, запусти `auto_updater.py` и проверь:

```bash
cd c:\Проекты\Dashboard_SC
python auto_updater.py
```

Открой `assets/js/data.js` и убедись:
- НЕТ записей `"Исаков Давронбек"`, `"Исматиллаев Нодирбек"`, `"Мамарайимов Фирдавс"`, `"Сабуров Огабек"`, `"Хакимов Умиджон"`, `"Шавкатов Гафур"`, `"Шавкат Гофур"`
- У `"Исаков Даврон"` в месяце `"Июнь 2026"` есть данные `collected_amount > 0`
- Аналогично для всех остальных каноничных имён

---

## 4. ФАЗА 2: Перенос парсинга в бэкенд [ВЫПОЛНЕНО]

### Что нужно сделать

Вся логика парсинга из `auto_updater.py` переносится в `backend/parser.py`. Это нужно, чтобы парсинг мог запускаться из HTTP-эндпоинта при загрузке файлов через UI.

#### Шаг 2.1: Создать файл `backend/parser.py`

Создай новый файл `backend/parser.py`. Перенеси в него ВСЕ следующие функции из `auto_updater.py`:

```python
# backend/parser.py
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

# === КОНСТАНТЫ (перенести из auto_updater.py) ===

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

# === NAME_MAP — полная таблица нормализации (перенести из auto_updater.py + новые записи) ===
NAME_MAP = {
    # ... ВСЕ записи из auto_updater.py ...
    # ... ПЛЮС новые записи из Шага 1.3 ...
}
# Добавить обратные записи для кириллицы:
for cyr in list(NAME_MAP.values()):
    NAME_MAP[cyr] = cyr

CHAR_NORMALIZE_MAP = { ... }  # Из Шага 1.2

# === ФУНКЦИИ НОРМАЛИЗАЦИИ (из Шагов 1.1 - 1.4) ===
def levenshtein_distance(s1, s2): ...
def normalize_chars(text): ...
def normalize_name(name): ...
def fuzzy_match_name(name, known_names, threshold=4): ...

# === ФУНКЦИИ ПАРСИНГА (перенести из auto_updater.py) ===
def parse_score(value): ...          # строка 140-151
def parse_duration(value): ...       # строка 154-187
def format_duration(minutes): ...    # строка 190-197
def extract_month_and_period(filename): ...  # строка 200-236

# === ОПРЕДЕЛЕНИЕ ТИПА ФАЙЛА ===

def detect_file_type(file_bytes: bytes, filename: str) -> str:
    """
    Определяет тип файла по его СОДЕРЖИМОМУ (не по имени!).
    
    Возвращает одну из строк:
    - "quality"     — файл оценок звонков (Quality)
    - "collections" — файл сборов
    - "crm"         — файл CRM-действий
    - "report"      — промежуточный отчёт PDF
    - "unknown"     — не удалось определить
    """
    lower_name = filename.lower()
    
    # PDF — определяем по тексту
    if lower_name.endswith('.pdf'):
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = ""
                for page in pdf.pages[:3]:  # Достаточно первых 3 страниц
                    text += (page.extract_text() or "") + "\n"
            if re.search(r"Отчет\s+по\s+сотруднику", text, re.IGNORECASE):
                return "report"
        except Exception:
            pass
        return "unknown"
    
    # XLSX — определяем по содержимому
    if lower_name.endswith('.xlsx'):
        try:
            xls = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
            sheet_names = xls.sheet_names
            
            # 1. Quality — есть лист "Оценки звонков Soft Collection"
            if XLSX_SHEET_NAME in sheet_names:
                return "quality"
            
            # 2. Читаем первый лист для анализа
            df = pd.read_excel(io.BytesIO(file_bytes), header=None, engine="openpyxl")
            
            # 3. CRM — пивотная таблица с "Названия строк" в заголовке
            for idx in range(min(5, len(df))):
                row_strs = [str(val).lower().strip() for val in df.iloc[idx] if pd.notna(val)]
                if any('названия строк' in s for s in row_strs):
                    return "crm"
            
            # 4. Сборы — есть раздел "план" и числовые данные в ячейках
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

# === ПАРСИНГ ФАЙЛОВ (адаптировать из auto_updater.py для работы с bytes) ===

def parse_quality_bytes(file_bytes: bytes, filename: str) -> Tuple[str, str, Dict]:
    """
    Парсинг Quality XLSX файла из bytes.
    Возвращает: (month, period, data_dict)
    data_dict: { "ИмяСотрудника": { tqs, aht, svp, raw_scores, activity_count } }
    """
    month, period = extract_month_and_period(filename)
    df = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=XLSX_SHEET_NAME,
        engine="openpyxl",
        header=2
    )
    
    data = {}
    for _, row in df.iterrows():
        employee = normalize_name(row.iloc[EMPLOYEE_INDEX])
        if not employee:
            continue
        
        tqs = parse_score(row.iloc[TQS_INDEX])
        duration = parse_duration(row.iloc[DURATION_INDEX])
        svp_values = [parse_score(row.iloc[idx]) for idx in SVP_COLUMNS_INDICES]
        
        if employee not in data:
            data[employee] = {
                "_tqs_values": [],
                "_durations": [],
                "_activity_count": 0,
                "raw_scores": {key: [] for key in SVP_KEYS},
            }
        
        data[employee]["_tqs_values"].append(tqs)
        data[employee]["_durations"].append(duration)
        data[employee]["_activity_count"] += 1
        for key, value in zip(SVP_KEYS, svp_values):
            data[employee]["raw_scores"][key].append(value)
    
    # Агрегация
    result = {}
    for emp, emp_data in data.items():
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
    """
    Парсинг Сборы XLSX из bytes.
    Возвращает: (month, period, data_dict)
    Используй логику из auto_updater.py parse_collections_file(), но читай из BytesIO.
    """
    month, period = extract_month_and_period(filename)
    # ... Перенеси логику parse_collections_file из auto_updater.py ...
    # Замени pd.read_excel(filepath, ...) на pd.read_excel(io.BytesIO(file_bytes), ...)
    # Замени normalize_name вызовы на новую функцию
    # Верни данные в формате { "ИмяСотрудника": { collected_amount, collected_count, collection_rate, plan_fulfillment } }
    pass


def parse_crm_bytes(file_bytes: bytes, filename: str) -> Tuple[str, str, Dict]:
    """
    Парсинг CRM-действия XLSX из bytes.
    Возвращает: (month, period, data_dict)
    Используй логику из auto_updater.py parse_crm_actions_file(), но читай из BytesIO.
    """
    month, period = extract_month_and_period(filename)
    # ... Перенеси логику parse_crm_actions_file из auto_updater.py ...
    pass


def parse_report_pdf_bytes(file_bytes: bytes, filename: str) -> Tuple[str, str, Dict]:
    """
    Парсинг промежуточного отчёта PDF из bytes.
    Возвращает: (month, period, data_dict)
    data_dict: { "ИмяСотрудника": { tendencies, rec } }
    Используй логику extract_pdf_sections, extract_section_text из auto_updater.py.
    """
    month, period = extract_month_and_period(filename)
    # ... Перенеси логику read_pdf_files из auto_updater.py ...
    pass
```

> **КРИТИЧЕСКИ ВАЖНО:**
> - Все функции `parse_*_bytes` принимают `bytes` вместо пути к файлу
> - Используют `io.BytesIO(file_bytes)` вместо открытия файла с диска
> - Используют обновлённую `normalize_name()` с fuzzy matching
> - Возвращают кортеж `(month, period, data_dict)`

#### Шаг 2.2: Обновить `backend/requirements.txt`

```
fastapi==0.115.6
uvicorn[standard]==0.32.1
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
httpx>=0.27.0
python-multipart>=0.0.18
pandas>=2.0.0
openpyxl>=3.1.0
pdfplumber>=0.11.0
gunicorn>=21.0.0
```

#### Шаг 2.3: Проверка

```bash
cd backend
python -c "from parser import detect_file_type, parse_quality_bytes; print('OK')"
```

---

## 5. ФАЗА 3: Встроенный интерфейс загрузки файлов [ВЫПОЛНЕНО]

### Что нужно сделать

Добавить в `analytics.html` вкладку «Загрузка данных» с drag & drop зоной и чеклистом полноты.

#### Шаг 3.1: Добавить API endpoints в `backend/app.py`

Добавь в `backend/app.py` следующие эндпоинты:

```python
from backend.parser import (
    detect_file_type, parse_quality_bytes, parse_collections_bytes,
    parse_crm_bytes, parse_report_pdf_bytes, normalize_name
)

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
    
    return count


@app.get("/api/upload/status")
def upload_status():
    """
    Возвращает статус загруженных данных по периодам.
    Для каждого (month, period) показывает, какие типы данных загружены.
    """
    if not engine:
        return {"periods": []}
    
    with Session(engine) as session:
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
            
            # Проверяем наличие данных каждого типа
            check_stmt = select(employee_scores).where(
                employee_scores.c.month == month,
                employee_scores.c.period == period,
            ).limit(50)
            records = session.execute(check_stmt).fetchall()
            
            has_quality = any(r.tqs and r.tqs > 0 for r in records)
            has_collections = any(r.collected_amount and r.collected_amount > 0 for r in records)
            has_crm = any(r.crm_actions and len(r.crm_actions) > 0 for r in records)
            has_report = any(r.tendencies and len(r.tendencies) > 0 for r in records)
            
            periods.append({
                "month": month,
                "period": period,
                "has_quality": has_quality,
                "has_collections": has_collections,
                "has_crm": has_crm,
                "has_report": has_report,
                "employees_count": len(records),
            })
        
        return {"periods": periods}


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
```

#### Шаг 3.2: Обновить эндпоинт `/api/metrics` для совместимости с фронтендом

Текущий `/api/metrics` в `backend/app.py` возвращает данные в формате, отличном от `DASHBOARD_DATA`. Нужно добавить эндпоинт, возвращающий данные в **точно таком же формате**, как `DASHBOARD_DATA`:

```python
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
```

#### Шаг 3.3: Добавить UI загрузки в `analytics.html`

В файле `analytics.html`, в секции фильтров (строка ~43-50), добавь кнопку «Загрузка данных»:

```html
<!-- ПОСЛЕ существующих вкладок "Команда" / "Сотрудник" -->
<div class="cat-tab" id="tab-view-upload" onclick="setViewMode('upload')">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:4px;">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="17 8 12 3 7 8"></polyline>
    <line x1="12" y1="3" x2="12" y2="15"></line>
  </svg>
  Загрузка
</div>
```

Добавь секцию загрузки (после секции `section-operations`):

```html
<div id="section-upload" class="section" style="padding:20px;">
  <div class="page-title">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
      <polyline points="17 8 12 3 7 8"></polyline>
      <line x1="12" y1="3" x2="12" y2="15"></line>
    </svg>
    Загрузка данных
  </div>
  <div class="page-sub">Загрузите файлы для обновления дашборда. Система автоматически определит тип каждого файла.</div>

  <!-- Чеклист полноты данных -->
  <div class="card" style="margin-bottom:20px;padding:20px;">
    <div class="card-title">Полнота данных текущего периода</div>
    <div id="upload-checklist" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:12px;">
      <!-- Заполняется из JS -->
    </div>
    <div id="upload-progress-bar" style="margin-top:16px;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;">
      <div id="upload-progress-fill" style="height:100%;width:0%;background:linear-gradient(90deg,#a78bfa,#6366f1);border-radius:3px;transition:width 0.3s;"></div>
    </div>
    <div id="upload-progress-text" style="margin-top:6px;font-size:11px;color:#94a3b8;font-weight:600;"></div>
  </div>

  <!-- Drag & Drop зона -->
  <div class="card" style="margin-bottom:20px;padding:0;">
    <div id="drop-zone" style="padding:60px 40px;text-align:center;border:2px dashed rgba(167,139,250,0.3);border-radius:12px;cursor:pointer;transition:all 0.2s;">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="1.5" style="margin-bottom:16px;">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="17 8 12 3 7 8"></polyline>
        <line x1="12" y1="3" x2="12" y2="15"></line>
      </svg>
      <div style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:8px;">Перетащите файлы сюда</div>
      <div style="font-size:12px;color:#94a3b8;">или нажмите для выбора файлов</div>
      <div style="font-size:11px;color:#64748b;margin-top:12px;">Поддерживаются: XLSX (Quality, Сборы, CRM) и PDF (Промежуточный отчёт)</div>
      <input type="file" id="file-input" multiple accept=".xlsx,.pdf" style="display:none;">
    </div>
  </div>

  <!-- Лог загрузки -->
  <div class="card" id="upload-log-card" style="display:none;margin-bottom:20px;padding:16px;">
    <div class="card-title">Результат обработки</div>
    <div id="upload-log" style="max-height:300px;overflow-y:auto;font-family:monospace;font-size:12px;line-height:1.8;margin-top:10px;"></div>
  </div>
</div>
```

#### Шаг 3.4: Добавить JavaScript для загрузки в `app.js`

Добавь в конец `app.js` модуль `FileUploader`:

```javascript
// ========== FILE UPLOAD MODULE ==========

const FileUploader = {
    init() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        if (!dropZone || !fileInput) return;

        // Click to select
        dropZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));

        // Drag & drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#a78bfa';
            dropZone.style.background = 'rgba(167,139,250,0.08)';
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.style.borderColor = 'rgba(167,139,250,0.3)';
            dropZone.style.background = 'transparent';
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'rgba(167,139,250,0.3)';
            dropZone.style.background = 'transparent';
            this.handleFiles(e.dataTransfer.files);
        });

        // Загрузить статус данных
        this.refreshChecklist();
    },

    async handleFiles(fileList) {
        if (!fileList || fileList.length === 0) return;

        const logCard = document.getElementById('upload-log-card');
        const logEl = document.getElementById('upload-log');
        logCard.style.display = 'block';
        logEl.innerHTML = '';

        this.log('📤 Начинаю загрузку ' + fileList.length + ' файлов...', 'info');

        const formData = new FormData();
        for (const file of fileList) {
            formData.append('files', file);
            this.log('📎 ' + file.name + ' (' + (file.size / 1024).toFixed(0) + ' KB)', 'info');
        }

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                this.log('❌ Ошибка сервера: ' + response.status, 'error');
                return;
            }

            const data = await response.json();

            for (const result of data.results) {
                if (result.status === 'ok') {
                    const typeNames = {
                        quality: '📊 Quality (оценки)',
                        collections: '💰 Сборы',
                        crm: '📋 CRM-действия',
                        report: '📄 Промежуточный отчёт'
                    };
                    this.log(
                        '✅ ' + result.filename + ' → ' +
                        (typeNames[result.type] || result.type) +
                        ' | ' + result.month + ' ' + result.period +
                        ' | ' + result.employees_count + ' сотрудников',
                        'success'
                    );
                } else {
                    this.log('❌ ' + result.filename + ': ' + result.message, 'error');
                }
            }

            this.log('🔄 Обновляю дашборд...', 'info');
            await this.refreshChecklist();

            // Перезагрузить данные дашборда
            if (typeof updateDashboard === 'function') {
                await updateDashboard();
            }
            this.log('✅ Дашборд обновлён!', 'success');

        } catch (err) {
            this.log('❌ Ошибка: ' + err.message, 'error');
        }
    },

    async refreshChecklist() {
        try {
            const response = await fetch('/api/upload/status');
            const data = await response.json();
            this.renderChecklist(data.periods);
        } catch (e) {
            console.error('Failed to load upload status:', e);
        }
    },

    renderChecklist(periods) {
        const container = document.getElementById('upload-checklist');
        const progressFill = document.getElementById('upload-progress-fill');
        const progressText = document.getElementById('upload-progress-text');
        if (!container) return;

        // Берём самый свежий период
        const latest = periods && periods.length > 0 ? periods[0] : null;

        const items = [
            { key: 'has_quality', label: 'Quality (оценки звонков)', icon: '📊' },
            { key: 'has_collections', label: 'Сборы (финансы)', icon: '💰' },
            { key: 'has_crm', label: 'CRM-действия', icon: '📋' },
            { key: 'has_report', label: 'Промежуточный отчёт (PDF)', icon: '📄' },
        ];

        let loaded = 0;
        container.innerHTML = items.map(item => {
            const done = latest && latest[item.key];
            if (done) loaded++;
            return `
                <div style="display:flex;align-items:center;gap:10px;padding:10px 14px;
                    background:${done ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.08)'};
                    border:1px solid ${done ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.2)'};
                    border-radius:8px;">
                    <span style="font-size:18px;">${done ? '☑' : '☐'}</span>
                    <div>
                        <div style="font-size:12px;font-weight:600;color:${done ? '#4ade80' : '#f87171'};">
                            ${item.icon} ${item.label}
                        </div>
                        <div style="font-size:10px;color:#64748b;">
                            ${done ? 'Загружен' : 'Не загружен'}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        const percent = (loaded / items.length) * 100;
        if (progressFill) progressFill.style.width = percent + '%';
        if (progressText) {
            progressText.textContent = latest
                ? `${latest.month} · ${latest.period} · ${loaded}/4 файла загружено · ${latest.employees_count} сотрудников`
                : 'Нет загруженных данных';
        }
    },

    log(message, type) {
        const logEl = document.getElementById('upload-log');
        if (!logEl) return;
        const colors = { info: '#94a3b8', success: '#4ade80', error: '#f87171' };
        const div = document.createElement('div');
        div.style.color = colors[type] || '#94a3b8';
        div.textContent = message;
        logEl.appendChild(div);
        logEl.scrollTop = logEl.scrollHeight;
    }
};
```

#### Шаг 3.5: Добавить CSS стили для загрузки

В `assets/css/style.css` добавь:

```css
/* === Upload Section === */
#drop-zone:hover {
    border-color: #a78bfa !important;
    background: rgba(167, 139, 250, 0.05) !important;
}
#drop-zone.dragover {
    border-color: #a78bfa !important;
    background: rgba(167, 139, 250, 0.1) !important;
    transform: scale(1.01);
}
```

---

## 6. ФАЗА 4: Переход фронтенда на API mode [ВЫПОЛНЕНО]

### Что нужно сделать

Заменить чтение `DASHBOARD_DATA` из `data.js` на `fetch()` к `/api/dashboard-data`.

#### Шаг 4.1: Добавить API-загрузчик данных в `app.js`

В НАЧАЛЕ `app.js`, после блока `// ========== 1. DASHBOARD DATA ==========`, добавь:

```javascript
// ========== 1. DASHBOARD DATA ==========
let DASHBOARD_DATA = {};  // Будет загружено из API
let DATA_LOADED = false;

async function loadDashboardDataFromAPI() {
    try {
        const response = await fetch('/api/dashboard-data');
        if (!response.ok) throw new Error('API error: ' + response.status);
        DASHBOARD_DATA = await response.json();
        DATA_LOADED = true;
        console.log('[INFO] Dashboard data loaded from API, employees:', Object.keys(DASHBOARD_DATA).length);
        return true;
    } catch (err) {
        console.error('[ERROR] Failed to load from API, trying fallback data.js:', err);
        // Fallback: если data.js уже загружен как <script>
        if (typeof window.DASHBOARD_DATA_FALLBACK !== 'undefined') {
            DASHBOARD_DATA = window.DASHBOARD_DATA_FALLBACK;
            DATA_LOADED = true;
            return true;
        }
        return false;
    }
}
```

#### Шаг 4.2: Обновить инициализацию дашборда

Найди в `app.js` функцию `pageInit` или блок `DOMContentLoaded`. Оберни инициализацию в асинхронную загрузку:

```javascript
// Обновить pageInit или блок инициализации
async function pageInit() {
    // Показать loading
    showLoading(true);
    
    // Загрузить данные из API
    await loadDashboardDataFromAPI();
    
    // Инициализация фильтров и дашборда
    initFilters();
    initHeatmapModeTabs();
    updateDashboard();
    
    // Инициализация модуля загрузки файлов
    if (typeof FileUploader !== 'undefined') {
        FileUploader.init();
    }
    
    showLoading(false);
}

function showLoading(show) {
    let loader = document.getElementById('dashboard-loader');
    if (!loader && show) {
        loader = document.createElement('div');
        loader.id = 'dashboard-loader';
        loader.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                height:300px;color:#a78bfa;font-size:14px;font-weight:600;">
                <div class="spinner" style="width:40px;height:40px;border:3px solid rgba(167,139,250,0.2);
                    border-top-color:#a78bfa;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:16px;">
                </div>
                Загрузка данных...
            </div>
        `;
        const main = document.getElementById('main');
        if (main) main.prepend(loader);
    }
    if (loader) loader.style.display = show ? 'block' : 'none';
}
```

#### Шаг 4.3: Обновить `analytics.html` и `rating.html`

В обоих файлах:

1. **УБРАТЬ** строку `<script src="assets/js/data.js"></script>`
2. **ОБНОВИТЬ** блок инициализации:

```html
<!-- УБРАТЬ: <script src="assets/js/data.js"></script> -->
<script src="assets/js/sidebar.js"></script>
<script src="assets/js/app.js"></script>
<script>
    document.addEventListener('DOMContentLoaded', async () => {
        initSidebar('analytics');  // или 'rating'
        initTheme();
        await pageInit();
    });
</script>
```

#### Шаг 4.4: Начальная загрузка БД из файлов `reports/`

Создай скрипт `backend/seed_db.py` для начальной загрузки данных из `reports/`:

```python
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
from app import engine, metadata, employee_scores, init_db

def seed_from_reports():
    init_db()
    
    reports_dir = Path(__file__).parent.parent / "reports"
    if not reports_dir.exists():
        print(f"[ERROR] reports/ directory not found at {reports_dir}")
        return
    
    files = sorted(list(reports_dir.glob("*.xlsx")) + list(reports_dir.glob("*.pdf")))
    print(f"[INFO] Found {len(files)} files in reports/")
    
    # Импортируем write_parsed_data_to_db из app
    from app import write_parsed_data_to_db
    
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
            print(f"[OK] {file_path.name} → {file_type} | {month} {period} | {count} employees")
            
        except Exception as e:
            print(f"[ERROR] {file_path.name}: {e}")
    
    print("[DONE] Seed complete!")

if __name__ == "__main__":
    seed_from_reports()
```

#### Шаг 4.5: Удалить `auto_updater.py` и `data.js`

После успешной миграции:
- Удали `auto_updater.py` из корня проекта
- Удали `assets/js/data.js` (1.1MB)

---

## 7. ФАЗА 5: Адаптивная мобильная версия [ВЫПОЛНЕНО]

### Что нужно сделать

Добавить responsive CSS и мобильный sidebar.

#### Шаг 5.1: Добавить CSS media queries в `style.css`

Добавь в КОНЕЦ `assets/css/style.css`:

```css
/* ============================================================
   RESPONSIVE: MOBILE (< 768px)
   ============================================================ */

@media (max-width: 768px) {
    /* Sidebar — overlay на мобильных */
    #sidebar {
        position: fixed;
        left: -280px;
        top: 0;
        bottom: 0;
        width: 260px;
        z-index: 1000;
        transition: left 0.3s ease;
        overflow-y: auto;
    }
    #sidebar.mobile-open {
        left: 0;
    }
    #sidebar.collapsed {
        left: -280px;
    }
    
    /* Backdrop при открытом sidebar */
    .sidebar-backdrop {
        display: none;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 999;
    }
    .sidebar-backdrop.active {
        display: block;
    }
    
    /* Main — полная ширина */
    #main, #main.collapsed {
        margin-left: 0 !important;
        width: 100% !important;
    }
    
    /* Hamburger — видимая на мобильных */
    .mobile-hamburger {
        display: flex !important;
        position: fixed;
        top: 12px;
        left: 12px;
        z-index: 998;
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 8px;
        cursor: pointer;
        color: #f97316;
    }
    
    /* KPI карточки — одна колонка */
    .section > div[style*="grid-template-columns: repeat(auto-fit"] {
        grid-template-columns: 1fr 1fr !important;
    }
    
    /* Графики — полная ширина */
    div[style*="grid-template-columns: 1fr 1fr"],
    div[style*="grid-template-columns: 2fr 1fr"] {
        grid-template-columns: 1fr !important;
    }
    
    /* Таблицы — горизонтальный скролл */
    table {
        display: block;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    
    /* Фильтры — вертикальная раскладка */
    div[style*="display:flex"][style*="flex-wrap:wrap"] {
        flex-direction: column;
        align-items: stretch !important;
    }
    
    /* Загрузка — адаптация */
    #drop-zone {
        padding: 40px 20px !important;
    }
    
    /* Upload checklist — одна колонка */
    #upload-checklist {
        grid-template-columns: 1fr !important;
    }
}

@media (max-width: 480px) {
    .section > div[style*="grid-template-columns"] {
        grid-template-columns: 1fr !important;
    }
    
    .kpi-value {
        font-size: 22px !important;
    }
    
    .page-title {
        font-size: 16px !important;
    }
}

/* Desktop — скрыть мобильные элементы */
@media (min-width: 769px) {
    .mobile-hamburger {
        display: none !important;
    }
    .sidebar-backdrop {
        display: none !important;
    }
}

/* Spinner animation */
@keyframes spin {
    to { transform: rotate(360deg); }
}
```

#### Шаг 5.2: Обновить `sidebar.js` для мобильных

Добавь в `sidebar.js`:

```javascript
// Добавить мобильный hamburger и backdrop
function initMobileSidebar() {
    // Hamburger button
    if (!document.querySelector('.mobile-hamburger')) {
        const btn = document.createElement('div');
        btn.className = 'mobile-hamburger';
        btn.innerHTML = '☰';
        btn.onclick = () => toggleMobileSidebar();
        document.body.appendChild(btn);
    }
    
    // Backdrop
    if (!document.querySelector('.sidebar-backdrop')) {
        const backdrop = document.createElement('div');
        backdrop.className = 'sidebar-backdrop';
        backdrop.onclick = () => closeMobileSidebar();
        document.body.appendChild(backdrop);
    }
}

function toggleMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.querySelector('.sidebar-backdrop');
    sidebar.classList.toggle('mobile-open');
    backdrop.classList.toggle('active');
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.querySelector('.sidebar-backdrop');
    sidebar.classList.remove('mobile-open');
    backdrop.classList.remove('active');
}

// Вызвать из initSidebar()
// В конце функции initSidebar(activeId) добавь:
//   initMobileSidebar();
```

---

## 8. ФАЗА 6: Деплой на VPS RackNerd [ВЫПОЛНЕНО]

### Предварительные условия

Пользователь предоставит:
- IP-адрес VPS
- SSH доступ (root или sudo)
- Доменное имя (если есть)

### Шаг 6.1: Настройка VPS (первоначальная)

Подключись к VPS по SSH и выполни:

```bash
# 1. Обновление системы
apt update && apt upgrade -y

# 2. Установка необходимых пакетов
apt install -y docker.io docker-compose git curl ufw nano htop

# 3. Запуск Docker
systemctl enable docker
systemctl start docker

# 4. Создание swap-файла (2GB — для VPS с 1-2GB RAM)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 5. Оптимизация swappiness (чтобы swap использовался только при необходимости)
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p

# 6. Настройка файрвола
ufw allow 22      # SSH
ufw allow 80      # HTTP
ufw allow 443     # HTTPS
ufw enable

# 7. Создание директории проекта
mkdir -p /opt/qc-dashboard
cd /opt/qc-dashboard
```

### Шаг 6.2: Клонирование проекта

```bash
# Если проект на GitHub:
git clone https://github.com/YOUR_REPO/Dashboard_SC.git /opt/qc-dashboard

# Если нет — загрузить через scp:
# scp -r c:\Проекты\Dashboard_SC\* root@YOUR_VPS_IP:/opt/qc-dashboard/
```

### Шаг 6.3: Создать production docker-compose.yml

Создай `/opt/qc-dashboard/docker-compose.prod.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: qc_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-qc_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-qc_dashboard}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # НЕ ВЫСТАВЛЯТЬ порт наружу в продакшене!
    networks:
      - qc_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-qc_user} -d ${POSTGRES_DB:-qc_dashboard}"]
      interval: 10s
      timeout: 5s
      retries: 5
    # Ограничение ресурсов
    deploy:
      resources:
        limits:
          memory: 256M

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: qc_backend
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+psycopg2://${POSTGRES_USER:-qc_user}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-qc_dashboard}
      DATA_MODE: api
    networks:
      - qc_network
    # Ограничение ресурсов
    deploy:
      resources:
        limits:
          memory: 512M

  nginx:
    image: nginx:alpine
    container_name: qc_nginx
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "80:80"
      - "443:443"
    networks:
      - qc_network
    volumes:
      - ./nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro
      - ./analytics.html:/usr/share/nginx/html/analytics.html:ro
      - ./rating.html:/usr/share/nginx/html/rating.html:ro
      - ./forecast.html:/usr/share/nginx/html/forecast.html:ro
      - ./index.html:/usr/share/nginx/html/index.html:ro
      - ./objections_b2c.html:/usr/share/nginx/html/objections_b2c.html:ro
      - ./objections_b2b.html:/usr/share/nginx/html/objections_b2b.html:ro
      - ./svp_mechanism.html:/usr/share/nginx/html/svp_mechanism.html:ro
      - ./svp_crm.html:/usr/share/nginx/html/svp_crm.html:ro
      - ./law.html:/usr/share/nginx/html/law.html:ro
      - ./instruments.html:/usr/share/nginx/html/instruments.html:ro
      - ./manual.html:/usr/share/nginx/html/manual.html:ro
      - ./reg_mechanics.html:/usr/share/nginx/html/reg_mechanics.html:ro
      - ./reg_methodology.html:/usr/share/nginx/html/reg_methodology.html:ro
      - ./reg_base.html:/usr/share/nginx/html/reg_base.html:ro
      - ./reg_rules.html:/usr/share/nginx/html/reg_rules.html:ro
      - ./qc_regulations.html:/usr/share/nginx/html/qc_regulations.html:ro
      - ./assets:/usr/share/nginx/html/assets:ro
      - ./logo:/usr/share/nginx/html/logo:ro
      - ./content:/usr/share/nginx/html/content:ro
      - certbot_certs:/etc/letsencrypt:ro
      - certbot_www:/var/www/certbot:ro
    deploy:
      resources:
        limits:
          memory: 64M

  # Certbot для SSL (опционально, если есть домен)
  certbot:
    image: certbot/certbot
    container_name: qc_certbot
    volumes:
      - certbot_certs:/etc/letsencrypt
      - certbot_www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

volumes:
  postgres_data:
  certbot_certs:
  certbot_www:

networks:
  qc_network:
    driver: bridge
```

### Шаг 6.4: Создать production nginx конфиг

Создай `/opt/qc-dashboard/nginx.prod.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip сжатие
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1000;

    # Кеширование статики
    location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # Фронтенд
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API → backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Увеличить лимит для загрузки файлов (50MB)
        client_max_body_size 50M;
        proxy_read_timeout 120s;
    }

    # Certbot challenge (для SSL)
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}
```

### Шаг 6.5: Создать production .env

Создай `/opt/qc-dashboard/.env.prod`:

```bash
POSTGRES_USER=qc_user
POSTGRES_PASSWORD=СГЕНЕРИРУЙ_НАДЁЖНЫЙ_ПАРОЛЬ_32_СИМВОЛА
POSTGRES_DB=qc_dashboard
DATA_MODE=api
```

### Шаг 6.6: Запуск

```bash
cd /opt/qc-dashboard

# Скопировать .env
cp .env.prod .env

# Запустить контейнеры
docker-compose -f docker-compose.prod.yml up -d --build

# Проверить статус
docker-compose -f docker-compose.prod.yml ps

# Проверить логи
docker-compose -f docker-compose.prod.yml logs -f backend

# Начальная загрузка данных из reports/
docker-compose -f docker-compose.prod.yml exec backend python seed_db.py

# Проверить API
curl http://localhost/api/health
```

### Шаг 6.7: Настройка SSL (если есть домен)

```bash
# Заменить server_name _ на ваш домен в nginx.prod.conf
# Например: server_name qc-dashboard.example.com;

# Получить сертификат
docker-compose -f docker-compose.prod.yml run --rm certbot \
    certonly --webroot --webroot-path=/var/www/certbot \
    -d qc-dashboard.example.com --email your@email.com --agree-tos

# Добавить SSL в nginx.prod.conf (443 блок)
# Перезапустить nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Шаг 6.8: Автозапуск при перезагрузке VPS

```bash
# Создать systemd сервис
cat > /etc/systemd/system/qc-dashboard.service << 'EOF'
[Unit]
Description=QC Dashboard Docker Compose
Requires=docker.service
After=docker.service

[Service]
WorkingDirectory=/opt/qc-dashboard
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable qc-dashboard
systemctl start qc-dashboard
```

---

## 9. ФАЗА 7: CI/CD — механизм обновления [ВЫПОЛНЕНО]

### Как обновлять проект на VPS

#### Вариант A: Ручной деплой (рекомендуется для начала)

Создай скрипт `/opt/qc-dashboard/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🔄 Pulling latest changes..."
cd /opt/qc-dashboard
git pull origin main

echo "🏗️ Rebuilding containers..."
docker-compose -f docker-compose.prod.yml up -d --build

echo "🧹 Cleaning old images..."
docker image prune -f

echo "✅ Deploy complete!"
echo "📊 Status:"
docker-compose -f docker-compose.prod.yml ps
```

```bash
chmod +x /opt/qc-dashboard/deploy.sh
```

**Для обновления:**
1. Внеси изменения в коде локально
2. `git add . && git commit -m "описание" && git push`
3. На VPS: `/opt/qc-dashboard/deploy.sh`

#### Вариант B: Агент-исполнитель деплоит напрямую

Если агент имеет SSH доступ к VPS, он может:

```bash
# Из локального проекта:
scp -r . root@VPS_IP:/opt/qc-dashboard/
ssh root@VPS_IP "cd /opt/qc-dashboard && docker-compose -f docker-compose.prod.yml up -d --build"
```

---

## 10. Чеклист финальной проверки

### После ФАЗЫ 1 (Дубликаты)
- [x] Запустить `auto_updater.py`
- [x] В `data.js` нет записей-дубликатов (Исаков Давронбек, Исматиллаев Нодирбек и т.д.)
- [x] У каноничных имён есть данные по сборам в Июнь 2026

### После ФАЗЫ 2 (Парсер в бэкенде)
- [x] `backend/parser.py` импортируется без ошибок
- [x] `detect_file_type()` корректно определяет все 4 типа файлов
- [x] Каждая функция `parse_*_bytes()` возвращает корректные данные

### После ФАЗЫ 3 (UI загрузки)
- [x] В analytics.html отображается вкладка «Загрузка»
- [x] Drag & drop работает
- [x] Файлы загружаются и парсятся
- [x] Чеклист полноты обновляется

### После ФАЗЫ 4 (API mode)
- [x] `data.js` удалён
- [x] Фронтенд загружает данные через `/api/dashboard-data`
- [x] Все графики, таблицы, рейтинг работают корректно
- [x] Loading-спиннер отображается при загрузке

### После ФАЗЫ 5 (Мобильная версия)
- [x] На экране < 768px sidebar скрыт, hamburger-кнопка видна
- [x] Графики не вылезают за экран
- [x] Таблицы скроллируются горизонтально
- [x] Drag & drop зона адаптивна

### После ФАЗЫ 6 (Деплой на VPS)
- [x] `docker-compose ps` — все 3 контейнера running
- [x] `curl http://VPS_IP/api/health` — 200 OK
- [x] Дашборд открывается в браузере по IP
- [x] Swap активен: `free -h` показывает swap
- [x] Systemd: `systemctl status qc-dashboard` — active

### После ФАЗЫ 7 (CI/CD)
- [x] `deploy.sh` существует и исполняется
- [x] После `git push + deploy.sh` изменения видны в браузере

### После ФАЗЫ 8 (Корректировки и исправления)
- [x] Ошибка 413 (Payload Too Large) устранена добавлением client_max_body_size в nginx.conf
- [x] Файлы настроек Nginx примонтированы в docker-compose.yml для динамической работы
- [x] Загрузка CRM (~2MB) и отчетов PDF за 4 периода проходит успешно (HTTP 200)
- [x] Все цветные SVG иконки на страницах переведены в традиционный вид (stroke="currentColor")

---

## ВАЖНЫЕ ЗАМЕЧАНИЯ ДЛЯ АГЕНТА

1. **НЕ УДАЛЯЙ** старые файлы (`auto_updater.py`, `data.js`) до тех пор, пока API mode не будет полностью работоспособен и проверен.

2. **Сохраняй** все существующие комментарии и документацию в коде — они содержат важный бизнес-контекст.

3. **Тестируй** каждую фазу ЛОКАЛЬНО перед переходом к следующей (через `docker-compose up`).

4. **Корреляции и бизнес-логика** — при переносе функций из `auto_updater.py` в `backend/parser.py` СОХРАНИ ВСЮ бизнес-логику:
   - `generate_crm_summary()` — генерация текстового вывода
   - `identify_behavior_pattern()` — определение паттерна
   - `calculate_efficiency_ratio()` — корреляция TQS → деньги
   - `calculate_crm_consistency()` — дисциплина CRM
   - `calculate_correlation()` — коэффициент Пирсона

5. **RAM оптимизация на VPS:**
   - PostgreSQL: `shared_buffers = 64MB`, `work_mem = 4MB` (добавить через docker environment или custom postgresql.conf)
   - Uvicorn: один worker (`--workers 1`)
   - Nginx: `worker_processes 1`

6. **Имена файлов НЕ ВАЖНЫ** для определения типа. Система определяет тип по СОДЕРЖИМОМУ файла. Но если имя файла содержит дату/период — извлекай из него `month` и `period`.

7. **При добавлении нового сотрудника** — если его имя не в `NAME_MAP`, fuzzy matching попытается найти совпадение. Если не найдёт — создаст новую запись. Это нормальное поведение.

# CHANGELOG — QC Dashboard v1.2

Все изменения с версией, датой и описанием.

---

## [1.2.0] — 10 апреля 2026

### 🆕 Docker-контейнеризация
- `backend/app.py` — FastAPI приложение (REST API + парсер)
- `backend/Dockerfile` — образ backend
- `backend/requirements.txt` — зависимости Python
- `backend/init_db.py` — инициализация БД (индексы + представления)
- `docker-compose.yml` — оркестрация: nginx + fastapi + postgres
- `nginx.conf` — reverse proxy + раздача статики
- `init_db.sql` — SQL инициализация (удалён, заменён на Python)
- `.dockerignore` — исключения для Docker

### 🆕 API эндпоинты
| Эндпоинт | Описание |
|----------|----------|
| `GET /api/health` | Проверка здоровья сервиса |
| `GET /api/employees` | Статистика всех сотрудников |
| `GET /api/leaderboard` | Рейтинг сотрудников (с трендами) |
| `GET /api/leaderboard/best-worst` | Топ-5 лучших/худших (с fuzzy match имён) |
| `GET /api/correlation/{name}` | Корреляция TQS/AHT (Пирсон) |
| `GET /api/compare/{name}` | Сравнение 2 периодов с дельтами |
| `GET /api/history/{name}` | Полная история сотрудника (mode: detailed/summary) |
| `GET /api/trends` | Общие тренды по периодам |
| `GET /api/trends/forecast` | Тренды + прогноз (Holt's Exponential Smoothing) |
| `GET /api/logs` | Логи парсинга |
| `GET /api/recommendations/{name}` | Рекомендации для сотрудника |
| `POST /api/upload/xlsx` | Загрузка XLSX файла |
| `POST /api/upload/pdf` | Загрузка PDF файла |

### 🆕 SVP Heatmap Pro — Алгоритм диагнозов
- 7 уровней цветовой индикации по процентным диапазонам
- Документ: `Алгоритм диагнозов SVP Heatmap Pro.md`
- CSS классы: `range-0-24`, `range-25-49`, `range-50-64`, `range-65-74`, `range-75-84`, `range-85-99`, `range-100`

### 🆕 Аналитика v1.2 — 3 инструмента
- `analytics-v2.js` — фронтенд аналитики
- **История**: таблица TQS/AHT/Звонков, режимы «Детальный»/«Совокупный»
- **Сравнение**: выбор сотрудника + 2 периода → дельты по всем метрикам
- **Тренды + Прогноз**: Chart.js график, R², рекомендации, лучшие/худшие

### 🐛 Исправления
| # | Проблема | Решение |
|---|----------|---------|
| 1 | Дубликат эндпоинта `/api/compare` | Удалён старый, оставлен новый с полной структурой |
| 2 | Ячейки SVP не окрашены (белые) | Заменён `${diagnosis.severity}` → `${diagnosis.cssClass}` |
| 3 | Хаотичный порядок периодов | Сортировка `_sort_periods_chronological()` — новые первыми |
| 4 | Дубликаты Шавкатов Гафур/Гофур | `normalize_employee_name()` + fuzzy match в leaderboard |
| 5 | R² = undefined | Добавлен в ответ API `/api/trends/forecast` |
| 6 | AHT формат `3:71` (невозможно) | Конвертация в `ММ:СС` через `formatAHT()` |
| 7 | Звонков 378/459/108 (нереально) | Дедупликация + `SUM` уникальных недель |
| 8 | `hist` not defined в trends/forecast | Заменён на `historical` |

### 📦 Зависимости backend
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
pandas==2.2.0
openpyxl==3.1.2
pdfplumber==0.10.3
python-multipart==0.0.6
pydantic==2.5.3
```

---

## [1.1.0] — 31 марта 2026

- Боковое выдвижное меню (sidebar v2 — сворачиваемое)
- Тёмная/светлая тема
- Тепловая карта СВП
- Динамика TQS
- Выработка по критериям
- Распределение оценок
- Персональные рекомендации из PDF
- AHT мониторинг
- `auto_updater.py` — парсер XLSX/PDF
- `index.html` — основной дашборд

---

## [1.0.0] — Базовая версия

- Начальная реализация дашборда

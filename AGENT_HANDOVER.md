# AGENT HANDOVER — QC Dashboard v1.2

> **Для любого AI-агента**, который продолжает работу над проектом.
> Прочитай этот файл ПЕРВЫМ перед началом работы.

---

## 📋 Что это за проект

**QC Dashboard v1.2** — аналитический дашборд для отдела Quality Control компании Soft Collection (Variant Retail Finance).

**Назначение:** Визуализация и анализ показателей качества работы сотрудников колл-центра.

---

## 🏗️ Архитектура проекта

### Docker-контейнеры (3 сервиса)
```
┌─────────────────────────────────────────┐
│  nginx (reverse proxy + static files)   │  :80
│  → Раздаёт index.html и статику         │
│  → Проксирует /api/* → backend           │
├─────────────────────────────────────────┤
│  fastapi (backend API + парсер)         │  :8000
│  → REST API для аналитики               │
│  → Парсинг XLSX/PDF                     │
│  → Прогнозирование (Holt's method)      │
├─────────────────────────────────────────┤
│  postgres (база данных)                 │  :5432
│  → Хранит историю оценок                │
│  → Рекомендации из PDF                  │
│  → Логи парсинга                        │
└─────────────────────────────────────────┘
```

### Ключевые файлы
| Файл | Описание |
|------|----------|
| `backend/app.py` | FastAPI приложение — вся серверная логика |
| `index.html` | Основной дашборд (frontend) |
| `analytics-v2.js` | JS модуль аналитики (История, Сравнение, Тренды) |
| `docker-compose.yml` | Оркестрация контейнеров |
| `nginx.conf` | Конфигурация Nginx |

---

## 🚀 Как запускать

### Запуск всех сервисов
```bash
cd c:\Users\user\AppData\Local\Programs\Microsoft VS Code\Dashboard_QC
docker-compose up -d --build
```

### Проверка работоспособности
```bash
# Статус контейнеров
docker-compose ps

# Health check
curl http://localhost/api/health

# Дашборд
# Открыть браузер: http://localhost
```

### Перезапуск backend (после изменений кода)
```bash
docker-compose restart backend
# Подождать 5-8 секунд для запуска
```

### Логи
```bash
docker-compose logs -f backend   # Backend
docker-compose logs -f postgres  # БД
docker-compose logs -f nginx     # Proxy
```

---

## 📊 Структура БД (PostgreSQL)

### Таблицы
| Таблица | Описание |
|---------|----------|
| `employee_scores` | Оценки сотрудников за период (TQS, AHT, 9 критериев СВП) |
| `pdf_recommendations` | Рекомендации из PDF отчётов |
| `parsing_logs` | Логи парсинга файлов |
| `tqs_aht_correlation` | Корреляция TQS и AHT |

### Подключение к БД
```bash
docker exec -it qc_postgres psql -U qc_user -d qc_dashboard
```

---

## 🔧 Важные правила

### 🚫 НЕ ДОПУСКАЙ «одно лечим — другое калечим»
- Каждое изменение тестируй изолированно
- Проверяй, что смежные функции НЕ сломались
- Используй `docker-compose ps` и `curl http://localhost/api/health` после изменений

### 📝 Форматирование AHT
- AHT хранится в минутах (float): `3.54` = 3 минуты 32 секунды
- Отображение: `ММ:СС` → функция `formatAHT()` в `analytics-v2.js`
- НИКОГДА не показывай AHT как десятичное число с «мин»

### 🧑 Нормализация имён
- Функция `normalize_employee_name()` в `backend/app.py`
- Исправляет опечатки: `Шавкатов Гафур` → `Шавкатов Гофур`
- При добавлении новых сотрудников — добавляй коррекции сюда

### 📅 Сортировка периодов
- Формат: `дд-дд Мес ГГГГ` (например `01-05 Апр 2026`)
- Функция: `_sort_periods_chronological()` — новые первыми
- НЕ использовать алфавитную сортировку

### 🔢 Дедупликация данных
- При парсинге XLSX создаются дубликаты записей
- В API `/api/history` — дедупликация по `(period, tqs)`
- В `/api/leaderboard/best-worst` — fuzzy match имён

---

## 🧪 Как тестировать API

```bash
# Health
curl http://localhost/api/health

# Leaderboard
curl http://localhost/api/leaderboard

# История сотрудника
curl "http://localhost/api/history/Абдувалиева%20Зарифа?mode=detailed"

# Сравнение периодов
curl "http://localhost/api/compare/Абдувалиева%20Зарифа?period1=01-08%20Фев%202026&period2=23-31%20Мар%202026"

# Тренды с прогнозом
curl http://localhost/api/trends/forecast

# Лучшие/худшие
curl "http://localhost/api/leaderboard/best-worst?limit=3"
```

---

## 📁 Полный список файлов

```
Dashboard_QC/
├── index.html                      # Основной дашборд
├── analytics-v2.js                 # Модуль аналитики (История, Сравнение, Тренды)
├── auto_updater.py                 # Legacy парсер (не используется в Docker)
├── docker-compose.yml              # Оркестрация контейнеров
├── nginx.conf                      # Nginx reverse proxy
├── init_db.sql                     # SQL инициализация (устарел, заменён на backend/init_db.py)
├── .dockerignore                   # Docker исключения
├── requirements.txt                # Legacy зависимости
│
├── backend/
│   ├── app.py                      # FastAPI приложение (основной серверный код)
│   ├── requirements.txt            # Python зависимости для Docker
│   ├── init_db.py                  # Инициализация БД (индексы + представления)
│   └── Dockerfile                  # Образ backend
│
├── reports/                        # Папка с отчётами (монтируется в контейнер)
│   ├── Quality *.xlsx             # XLSX файлы с оценками звонков
│   └── Промежуточный отчет *.pdf  # PDF файлы с рекомендациями
│
├── README.md                       # Документация проекта
├── CHANGELOG.md                    # История всех изменений
├── INSTRUCTION.md                  # Инструкция по Git
├── Алгоритм диагнозов SVP Heatmap Pro.md  # Документация алгоритма диагнозов
└── QC Dashboard v1.2's upcoming plans.md  # План развития (roadmap)
```

---

## ⚠️ Известные проблемы и решения

| Проблема | Решение |
|----------|---------|
| Backend не отвечает после restart | Подождать 5-10 сек, проверить `docker logs qc_backend` |
| 403 на http://localhost | Nginx не нашёл index.html — проверить volume mount |
| Дубликаты в БД | Парсер запускается多次 — дедупликация в API |
| Порт 80 занят | Изменить в docker-compose.yml: `8080:80` |

---

## 📌 Критические эндпоинты (НЕ ЛОМАТЬ)

| Эндпоинт | Зависимости |
|----------|-------------|
| `GET /api/health` | Мониторинг |
| `GET /api/leaderboard` | SVP Heatmap, Тренды |
| `GET /api/history/{name}` | История, Сравнение |
| `GET /api/compare/{name}` | Сравнение периодов |
| `GET /api/trends/forecast` | Тренды + Прогноз |
| `GET /api/leaderboard/best-worst` | Виджет под трендами |

---

## 🔄 Рабочий цикл разработки

1. Внести изменения в файлы
2. `docker-compose restart backend` (если менял backend/app.py)
3. Подождать 5-8 секунд
4. `curl http://localhost/api/health` — проверить работоспособность
5. Открыть http://localhost в браузере — проверить UI
6. Протестировать затронутые функции

---

**Последнее обновление:** 10 апреля 2026
**Версия проекта:** 1.2.0

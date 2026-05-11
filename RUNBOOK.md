# RUNBOOK - QC Dashboard v1.1

Операционная документация для развертывания, обслуживания и диагностики Dashboard SC.

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Конфигурация](#конфигурация)
3. [Обновление данных (API Mode)](#обновление-данных-api-mode)
4. [Бэкапы и восстановление](#бэкапы-и-восстановление)
5. [Диагностика](#диагностика)
6. [Частые проблемы](#частые-проблемы)

---

## Быстрый старт

### Требования

- Docker и Docker Compose
- Python 3.11+ (для локальных скриптов)

### Запуск проекта

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd Dashboard_SC

# 2. Создать .env из примера
cp .env.example .env

# 3. Отредактировать .env (изменить пароли при необходимости)
nano .env

# 4. Запустить проект
docker compose up -d --build

# 5. Проверить статус
docker compose ps

# 6. Открыть в браузере
# Frontend: http://localhost/
# API health: http://localhost:8000/api/health
```

### Остановка проекта

```bash
docker compose down

# Полная очистка (включая volumes)
docker compose down -v
```

---

## Конфигурация

### Переменные окружения (.env)

| Переменная | Описание | Пример |
|------------|----------|--------|
| `POSTGRES_USER` | Пользователь PostgreSQL | `qc_user` |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | `change_me` |
| `POSTGRES_DB` | Имя базы данных | `qc_dashboard` |
| `DATABASE_URL` | URL подключения к БД | `postgresql+psycopg2://qc_user:change_me@postgres:5432/qc_dashboard` |
| `REPORTS_SOURCE` | Путь к отчетам | `./reports` |
| `BACKEND_API_URL` | URL backend API | `http://backend:8000` |
| `DATA_MODE` | Режим данных: `api` или `static` | `api` |
| `ENABLE_BACKEND_SYNC` | Включить синхронизацию с backend | `1` |

### Структура проекта

```
Dashboard_SC/
├── backend/           # FastAPI backend
│   ├── app.py        # Основное приложение
│   ├── Dockerfile    # Docker образ backend
│   └── requirements.txt
├── assets/           # Фронтенд ресурсы
│   ├── css/          # Стили
│   └── js/           # Скрипты и данные
│       ├── data.js   # Данные dashboard (static mode)
│       └── tactical-data.js # Данные тактических страниц
├── content/          # Markdown контент для тактических страниц
│   ├── law/          # Законодательные документы
│   ├── reglament/    # Регламенты
│   └── tactical/     # Тактические материалы
├── scripts/          # Вспомогательные скрипты
│   ├── build_tactical_data.py # Генератор tactical-data.js
│   └── check_frontend_security.py
├── reports/          # Папка для отчетов (XLSX/PDF)
├── docker-compose.yml
├── Dockerfile        # Frontend (nginx)
├── auto_updater.py   # Скрипт обновления данных
└── .env.example      # Пример конфигурации
```

---

## Обновление данных (Static Mode — текущий режим)

### Автоматическое/Ручное обновление

`auto_updater.py` парсит XLSX/PDF из `reports/` и обновляет `assets/js/data.js`.
Он также параллельно отправляет агрегированные данные в PostgreSQL, если включено `ENABLE_BACKEND_SYNC=1`.

1. Положите отчеты в папку `reports/`:
   - `Quality DD.MM.YYYY - DD.MM.YYYY.xlsx` - оценки звонков
   - `Промежуточный отчет по сотрудникам SC за период DD-MM-YYYY.pdf` - рекомендации

2. Запустите обновление:
```bash
python auto_updater.py
```

3. Файл `assets/js/data.js` будет обновлен автоматически, и графики на сайте изменятся.
   - Данные будут также записаны в PostgreSQL (если `ENABLE_BACKEND_SYNC=1`).
   
4. Если вы работаете в Docker среде, после изменения `data.js` нужно обновить контейнер nginx (т.к. статика запекается в образ):
```bash
docker compose build nginx
docker compose up -d nginx
```

### Обновление данных (API Mode) [ПЛАНИРУЕТСЯ]

Для перехода на этот режим необходимо обновить фронтенд для чтения из `/api/metrics`.

```bash
# Загрузить XLSX
curl -X POST -F "file=@reports/Quality_01.04.2026.xlsx" http://localhost:8000/api/upload/xlsx

# Загрузить PDF
curl -X POST -F "file=@reports/Отчет.pdf" http://localhost:8000/api/upload/pdf

# Запустить обработку
curl -X POST http://localhost:8000/api/process-reports
```

### Генерация tactical-data.js

При изменении контента в `content/`:

```bash
python scripts/build_tactical_data.py
```

---

## Бэкапы и восстановление

### Бэкап PostgreSQL

```bash
# Создать бэкап
docker exec qc_postgres pg_dump -U qc_user qc_dashboard > backup_$(date +%Y%m%d).sql

# Сжать бэкап
gzip backup_$(date +%Y%m%d).sql
```

### Восстановление из бэкапа

```bash
# Распаковать (если сжат)
gunzip backup_20260508.sql.gz

# Восстановить
docker exec -i qc_postgres psql -U qc_user qc_dashboard < backup_20260508.sql
```

### Бэкап данных dashboard

Данные хранятся в PostgreSQL. Для экспорта в JSON:

```bash
# Через API (работает только после начала накопления данных в PostgreSQL при ENABLE_BACKEND_SYNC=1)
curl http://localhost:8000/api/metrics > dashboard_backup_$(date +%Y%m%d).json
```

---

## Диагностика

### Проверка состояния

```bash
# Health check API
curl http://localhost:8000/api/health

# Проверка контейнеров
docker compose ps

# Проверка логов
docker compose logs -f nginx
docker compose logs -f backend
docker compose logs -f postgres
```

### Интерпретация health check

| Статус | Database | Описание |
|--------|----------|----------|
| 200 | connected | Все работает |
| 200 | not_configured | DATABASE_URL не задан |
| 503 | error | Ошибка подключения к БД |

### Просмотр данных в БД

```bash
# Подключиться к PostgreSQL
docker exec -it qc_postgres psql -U qc_user qc_dashboard

# Посмотреть таблицы
\dt

# Посмотреть данные
SELECT employee_name, month, period, tqs FROM employee_scores ORDER BY created_at DESC LIMIT 10;

# Выйти
\q
```

### Отладка auto_updater.py

```bash
# Запустить с подробным выводом
python -u auto_updater.py

# Проверить синтаксис
python -m compileall auto_updater.py
```

---

## Частые проблемы

### Контейнеры не запускаются

```bash
# Проверить логи
docker compose logs

# Пересоздать контейнеры
docker compose down
docker compose up -d --build
```

### Ошибка подключения к БД

1. Проверьте `.env`:
```bash
cat .env | grep DATABASE_URL
```

2. Убедитесь, что PostgreSQL запущен:
```bash
docker compose ps postgres
```

3. Проверьте логи PostgreSQL:
```bash
docker compose logs postgres
```

### Данные не обновляются

1. Проверьте права на папку `reports/`:
```bash
ls -la reports/
```

2. Проверьте логи auto_updater:
```bash
# Запуск auto_updater происходит локально в терминале
# Смотрите вывод в терминале. Контейнер auto_updater в docker-compose не предусмотрен.
```

3. Убедитесь, что файлы соответствуют ожидаемому формату:
   - XLSX: лист "Оценки звонков Soft Collection"
   - PDF: содержит "Отчет по сотруднику"

### Frontend не показывает данные

1. Проверьте API:
```bash
curl http://localhost:8000/api/metrics
```

2. Проверьте консоль браузера (F12) на ошибки

3. Убедитесь, что nginx запущен:
```bash
docker compose ps nginx
```

### Сброс проекта к начальному состоянию

```bash
# Полная очистка
docker compose down -v

# Удалить все данные
rm -rf reports/*.xlsx reports/*.pdf

# Запустить заново
docker compose up -d --build
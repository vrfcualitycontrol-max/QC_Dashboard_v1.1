# Dashboard SC

Аналитический dashboard для контроля качества звонков (Soft Collection Unit).

## Текущий статус

Актуальное состояние проекта описано в `CURRENT_STATE.md`.  
Если есть расхождения между документами, приоритет у `CURRENT_STATE.md`.

## Быстрый старт (Docker)

Требования:

- Docker + Docker Compose

Запуск:

```bash
docker compose up -d --build
```

Проверка:

```bash
docker compose ps
```

Доступ:

- Frontend: `http://localhost/index.html`
- API health: `http://localhost:8000/api/health`

Остановка:

```bash
docker compose down
```

## Структура

- Frontend: `*.html`, `assets/`
- Backend: `backend/`
- Infrastructure: `docker-compose.yml`, `nginx.conf`
- Data update scripts: `auto_updater.py` и вспомогательные `*.py`
- Reports mount dir: `reports/`
- Tactical content source: `content/` (см. `content/CONTENT_SUBMISSION.md`)

## Важно

- Репозиторий настроен как самодостаточный: backend находится внутри проекта.
- Для локальных нестандартных путей можно использовать переменные:
  - `BACKEND_CONTEXT`
  - `BACKEND_SOURCE`
  - `REPORTS_SOURCE`

## Автоматические проверки качества и безопасности

Добавлен CI workflow: `.github/workflows/quality-and-security.yml`

Проверки:

- синтаксис Python (`compileall`);
- smoke-тесты backend API (`tests/test_backend_smoke.py`);
- security-скан backend (`bandit -r backend`);
- baseline-check фронтенд-безопасности (`scripts/check_frontend_security.py`);
- валидация `docker compose config`.

## Тактические страницы: статус

Интеграция и интерактивный рендер выполнены для страниц:

- `law.html`
- `instruments.html`
- `manual.html`

Рендер выполнен через изолированный модуль `assets/js/tactical-pages.js`, чтобы не затрагивать рабочие аналитические функции.

Что реализовано:

- карточная навигация и постраничный просмотр длинных материалов;
- интерактивные плитки тем в `manual.html` ("Граф процесса");
- быстрый переход к теме по названию (dropdown) в manual-секциях;
- поиск по ключевым словам в `instruments.html`;
- рендер markdown-таблиц и базовая очистка нечитабельных символов.

Для наполнения контентом используйте Markdown-шаблоны:

- `content/CONTENT_SUBMISSION.md`

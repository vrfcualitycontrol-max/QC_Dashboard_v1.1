# Changelog

Все значимые технические изменения по стабилизации проекта фиксируются здесь.

## 2026-04-23

### 1) Репозиторий самодостаточный
- `docker-compose.yml` переведен на локальные пути backend/reports по умолчанию.
- Добавлен локальный backend-контур: `backend/app.py`, `backend/Dockerfile`, `backend/requirements.txt`.
- Добавлена папка `reports/` для стабильного bind-mount.

### 2) Унификация документации и архитектуры
- Добавлен единый источник правды: `CURRENT_STATE.md`.
- Добавлен актуальный `README.md` с рабочим запуском.
- В исторических документах добавлены дисклеймеры и ссылка на `CURRENT_STATE.md`:
  - `PROJECT_STATUS.md`
  - `GENERAL_PLAN.md`
  - `FINAL_REPORT.md`
  - `AGENT_BRIEF.md`

### 3) Автопроверки качества и безопасности
- Добавлены backend smoke-тесты: `tests/test_backend_smoke.py`.
- Добавлен CI workflow: `.github/workflows/quality-and-security.yml`.
- В CI включены syntax check, smoke tests, Bandit scan, проверка `docker compose config`.

### 4) Hardening-пакет
- В CI закреплены версии инструментов: `pytest==9.0.3`, `bandit==1.9.4`.
- Добавлена baseline-проверка фронтенд-безопасности:
  - `security/frontend-security-baseline.json`
  - `scripts/check_frontend_security.py`

### 5) Тактические разделы: каркас + sidebar
- Добавлен изолированный модуль `assets/js/tactical-pages.js` для страниц:
  - `law.html`
  - `instruments.html`
  - `manual.html`
- Добавлены каркасы страниц с безопасными fallback-сценариями при пустом контенте.
- Sidebar переведен на SVG-иконки в минималистичном стиле, выровнен compact-режим.
- Добавлена инструкция по передаче контента: `content/CONTENT_SUBMISSION.md`.

# CURRENT STATE — Dashboard SC

Дата обновления: 23 апреля 2026  
Статус документа: ЕДИНЫЙ ИСТОЧНИК ПРАВДЫ ПО ТЕКУЩЕМУ СОСТОЯНИЮ

## 1) Фактическая архитектура (as-is)

Проект работает как multi-page frontend с backend в текущем репозитории.

- Frontend: статические HTML-страницы + общий JS/CSS
- Backend: `backend/app.py` (FastAPI, базовые API endpoints)
- Infra: `docker-compose.yml` + `nginx.conf`
- DB: PostgreSQL контейнер

Текущая схема:

`nginx:80 -> backend:8000 -> postgres:5432`

## 2) Что реально есть в репозитории

- Документы и отчеты: `*.md` в корне
- Frontend: `*.html`, `assets/js/*`, `assets/css/*`
- Backend (внутри проекта): `backend/app.py`, `backend/Dockerfile`, `backend/requirements.txt`
- Инструменты обновления данных: `auto_updater.py` и вспомогательные python-скрипты
- Папка отчетов для bind-mount: `reports/`

## 3) Что уже сделано

- Репозиторий сделан самодостаточным для запуска docker-compose без внешнего backend-пути.
- В `docker-compose.yml` backend/reports переведены на локальные пути по умолчанию.
- Добавлен минимальный backend-контур API для безопасного развития без регрессий.
- Внедрен quality/security контур (CI + smoke-тесты + frontend security baseline).
- Реализован каркас тактических страниц: `law.html`, `instruments.html`, `manual.html`.
- Добавлен изолированный модуль тактических страниц: `assets/js/tactical-pages.js`.
- Sidebar переведен на минималистичные SVG-иконки и выровнен в compact-режиме.

## 4) Ограничения текущего состояния

- Backend реализован в минимальной версии (каркас endpoints), а не в полном объеме, описанном в старых отчетах.
- Страницы `law.html`, `manual.html`, `instruments.html` готовы как каркас и ожидают пользовательский контент из Markdown.
- Часть страниц остается в статусе "В разработке": `reg_base.html`, `reg_rules.html`.
- Исторические документы содержат устаревшие и конфликтующие статусы (production/crisis/recovery).

## 4.1) Передача материалов для контента

Формат передачи материалов: Markdown.

Инструкция и шаблоны:

- `content/CONTENT_SUBMISSION.md`

## 5) Правило чтения документации

1. Текущая фактическая картина: читать этот файл (`CURRENT_STATE.md`) первым.
2. Операционные инструкции по запуску: `README.md`.
3. Исторический контекст и хронология: `GENERAL_PLAN.md`, `FINAL_REPORT.md`, `AUDIT_EXECUTIVE_SUMMARY.md`, `AGENT_BRIEF.md`.

## 6) Критерий актуальности

Любое изменение архитектуры/запуска/структуры репозитория должно сопровождаться обновлением:

- `CURRENT_STATE.md`
- `README.md`

Без этих обновлений изменение считается неполностью зафиксированным.

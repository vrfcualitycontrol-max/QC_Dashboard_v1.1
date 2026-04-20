# README_AGENT — Dashboard QC

## Краткий статус

- **Текущий проект:** Dashboard Quality Control (Soft Collection Unit)
- **Рабочая папка:** `d:\Doc\Doc\Doc\Оценка качества звонков\Отчеты\Итоговый отчет\Dashboard_SC`
- **Стабильность:** backend восстановлен, nginx исправлен, PostgreSQL работает на `postgres:16-alpine`
- **Основные файлы:** `index.html`, `docker-compose.yml`, `nginx.conf`, `backend/app.py`, `backend/init_db.py`

## Что уже сделано

1. Исправлен `docker-compose.yml`:
   - `postgres` образ обновлён до `postgres:16-alpine`
   - том данных сохранён как `external: true` с именем `dashboard_qc_postgres_data`
   - `backend` и `nginx` монтируют правильные пути
2. Исправлен `nginx.conf`:
   - `location / { try_files $uri $uri/ /index.html; }`
   - `location /api/` проксирует на `http://backend:8000`
3. Восстановлен backend и проверены API:
   - `http://localhost:8000/api/health` → 200
   - `http://localhost:8000/api/employees` → 200
4. Проверено работоспособность frontend через nginx:
   - `http://localhost/` → 200

## Что важно знать

### Данные и структура

- `Dashboard_SC` содержит основной фронтенд и отчёты.
- `Dashboard_QC/backend` содержит backend-код, который запускается в контейнере `qc_backend`.
- `reports/` в `Dashboard_SC` монтируется в backend как `/app/reports`.
- PostgreSQL том уже содержит данные, совместимые с PostgreSQL 16.

### Ключевой баг, который был устранён

- **Причина 502/500**: nginx proxy пытался обращаться к backend, который был не запущен или некорректно настроен.
- **Причина падения PostgreSQL**: контейнер запускался на `postgres:15`, тогда как данные были созданы PostgreSQL 16.

### Важно для следующего агента

- Не трать время на переизучение `index.html` как единственного источника правды — основной backend и nginx уже восстановлены.
- При любых изменениях проверяй `docker-compose.yml`, `nginx.conf` и `backend/app.py` в первую очередь.
- Если нужен контекст, сначала читай `AGENT_BRIEF.md` и `README_AGENT.md`.

## Быстрые команды

```powershell
cd "d:\Doc\Doc\Doc\Оценка качества звонков\Отчеты\Итоговый отчет\Dashboard_SC"
docker compose up -d

docker ps -a

docker logs qc_backend --tail 50
docker logs qc_nginx --tail 50
docker logs qc_postgres --tail 50

docker restart qc_backend
docker restart qc_nginx

curl http://localhost:8000/api/health
curl http://localhost:8000/api/employees
curl http://localhost/
```

## Контекст и память

- Сохраняй важные факты в документацию, а не только в переписке.
- Следующий агент или новая сессия может потерять краткосрочный контекст, но файл остаётся.
- Не удаляй эту страницу: она должна быть первым файлом для чтения.

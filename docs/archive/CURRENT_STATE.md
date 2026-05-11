# Current State - QC Dashboard v1.1

**Дата обновления:** 2026-05-08  
**Статус:** API Mode активирован

## Текущее состояние проекта

### Режим данных: API Mode

Проект переведен на **API Mode** - данные хранятся в PostgreSQL и передаются через backend API.

### Архитектура

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│  FastAPI    │────▶│ PostgreSQL  │
│  (Frontend) │     │  (Backend)  │     │  (Database) │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│   HTML/JS   │     │ auto_updater│
│   (Assets)  │     │   (Parser)  │
└─────────────┘     └─────────────┘
```

### Компоненты

1. **Frontend (Nginx)**
   - Статические HTML страницы
   - assets/js/data.js - данные dashboard
   - assets/js/tactical-data.js - тактические материалы
   - assets/css/ - стили

2. **Backend (FastAPI)**
   - `/api/health` - проверка состояния
   - `/api/metrics` - все данные dashboard
   - `/api/employees` - список сотрудников
   - `/api/history/{name}` - история сотрудника
   - `/api/upload/xlsx` - загрузка XLSX
   - `/api/upload/pdf` - загрузка PDF
   - `/api/data-mode` - текущий режим данных

3. **Database (PostgreSQL)**
   - Таблица `employee_scores` - оценки сотрудников
   - Таблица `employees` - информация о сотрудниках

4. **Data Pipeline**
   - `auto_updater.py` - парсинг XLSX/PDF и запись в БД
   - `scripts/build_tactical_data.py` - генерация tactical-data.js

### Что было изменено (стабилизация)

#### Фаза A: Переносимость
- ✅ Убран хардкодный Windows путь из docker-compose.yml
- ✅ Создан `.env.example` с конфигурацией
- ✅ `.env` добавлен в `.gitignore`
- ✅ PostgreSQL volume сделан не-external
- ✅ nginx теперь собирается из Dockerfile (без bind-mount)

#### Фаза B: API Mode
- ✅ Реализованы API endpoints в backend/app.py
- ✅ Обновлен auto_updater.py для работы с API
- ✅ Создан scripts/build_tactical_data.py
- ✅ Документирован режим API Mode

#### Фаза C: Backend
- ✅ Добавлены production-ready endpoints
- ✅ Реализована загрузка файлов (upload)
- ✅ Добавлены CORS middleware
- ✅ Обновлены тесты backend

#### Фаза E: Документация
- ✅ Создан RUNBOOK.md с полной инструкцией
- ✅ Обновлен README.md с информацией об API Mode

### Известные ограничения

1. **Frontend еще не обновлен для работы с API**
   - Текущий frontend все еще читает данные из `assets/js/data.js`
   - Для полного перехода на API Mode нужно обновить JavaScript на страницах

2. **Прогнозирование (forecast)**
   - Endpoint `/api/trends/forecast` возвращает placeholder
   - ML-модель не реализована

3. **Безопасность**
   - Нет аутентификации/авторизации
   - API открыт для всех запросов

### Следующие шаги

1. **Обновить frontend для работы с API**
   - Изменить JavaScript для загрузки данных из `/api/metrics`
   - Сохранить тактические страницы без fetch() (требование стабильности)

2. **Добавить аутентификацию**
   - Реализовать JWT или session-based auth
   - Защитить API endpoints

3. **Реализовать прогнозирование**
   - Добавить ML-модель для прогноза показателей

4. **Оптимизировать базу данных**
   - Добавить индексы
   - Настроить автоматические бэкапы

### Проверка состояния

```bash
# Проверка здоровья API
curl http://localhost:8000/api/health

# Проверка данных
curl http://localhost:8000/api/metrics

# Запуск тестов
pytest tests/test_backend_smoke.py

# Валидация docker-compose
docker compose config
```

### Ссылки

- [RUNBOOK.md](../../RUNBOOK.md) - операционная документация
- [STABILIZATION_PLAN.md](../../STABILIZATION_PLAN.md) - план стабилизации
- [README.md](../../README.md) - основная документация
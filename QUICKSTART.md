# QC Dashboard v1.2.1 — Команда быстрого старта

> **Для AI-агента:** Если ты впервые работаешь с этим проектом — выполни шаги ниже.

---

## 🚀 Быстрый старт (3 команды)

### 1. Запусти Docker
```bash
cd c:\Users\user\AppData\Local\Programs\Microsoft VS Code\Dashboard_QC
docker-compose up -d
```

### 2. Проверь работоспособность
```bash
# Подожди 10 секунд
timeout /t 10

# Health check
curl http://localhost/api/health

# Проверка дашборда
curl -s -o nul -w "HTTP Status: %{http_code}" http://localhost
```

### 3. Прочитай контекст
```
Открой файл: AGENT_HANDOVER.md
```

---

## 📋 Что проверить перед работой

| Проверка | Команда | Ожидаемый результат |
|----------|---------|---------------------|
| Контейнеры | `docker-compose ps` | Все 3 запущены (healthy) |
| API | `curl http://localhost/api/health` | `{"status":"healthy"}` |
| Дашборд | `curl -s -o nul -w "%{http_code}" http://localhost` | `200` |

---

## 🔧 Если что-то не работает

```bash
# Логи backend
docker-compose logs -f backend

# Перезапуск
docker-compose restart backend

# Пересборка
docker-compose up -d --build

# Полный сброс (данные удалятся!)
docker-compose down -v && docker-compose up -d --build
```

---

## 📁 Ключевые файлы

| Файл | Зачем |
|------|-------|
| `AGENT_HANDOVER.md` | Полная документация для агента |
| `PROJECT_STATUS.md` | Текущее состояние проекта |
| `CHANGELOG.md` | История изменений |
| `backend/app.py` | Весь серверный код |
| `index.html` | Фронтенд дашборда |
| `analytics-v2.js` | Модуль аналитики |
| `auto_updater.py` | Локальный парсер XLSX/PDF |

---

## ⚠️ Критические правила

1. **НЕ ломай смежные функции** — после изменений тестируй все затронутые компоненты
2. **AHT в формате ММ:СС** — никогда не показывай как десятичное число с "мин"
3. **Нормализация имён** — при добавлении новых сотрудников обновляй `NAME_CORRECTIONS` в `auto_updater.py` и `normalize_employee_name()` в `backend/app.py`
4. **Сортировка периодов** — новые первыми, используй `_sort_periods_chronological()`
5. **Дедупликация** — в API `/api/history` дедупликация по `(period, tqs)`

---

**Версия:** 1.2.1
**Дата:** 10 апреля 2026
**GitHub:** https://github.com/vrfcualitycontrol-max/QC_Dashboard_v1.1

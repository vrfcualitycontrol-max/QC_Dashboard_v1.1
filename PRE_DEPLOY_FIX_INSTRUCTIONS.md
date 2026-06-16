# ИНСТРУКЦИИ ДЛЯ АГЕНТА-ИСПОЛНИТЕЛЯ: Финальная отладка перед деплоем

> **КРИТИЧЕСКИ ВАЖНО:** Этот документ содержит ТОЧНЫЕ инструкции по исправлению всех обнаруженных проблем.
> Каждая задача имеет чёткое указание на файл, номер строки и конкретный код для изменения.
> **НЕ МЕНЯЙ** ничего за пределами описанного. **НЕ УДАЛЯЙ** существующие комментарии.
> После каждой группы изменений — проверяй, что ничего не сломалось.

---

## ОГЛАВЛЕНИЕ

1. [КРИТИЧЕСКИЕ БАГИ — Графики и визуализация](#1-критические-баги--графики-и-визуализация)
2. [Навигация «Загрузка → Аналитика»](#2-навигация-загрузка--аналитика)
3. [CSS-исправления для графиков](#3-css-исправления-для-графиков)
4. [UX-улучшения](#4-ux-улучшения)
5. [Мелкие баги и неудобства](#5-мелкие-баги-и-неудобства)
6. [Чеклист проверки](#6-чеклист-проверки)

---

## СТАТУС EVOLUTION_PLAN_v2.md

Все 7 фаз + фаза 8 (корректировки) отмечены как `[ВЫПОЛНЕНО]`. Все чеклист-пункты — `[x]`. Архитектура реализована правильно: бэкенд (FastAPI + PostgreSQL), фронтенд (API mode через `/api/dashboard-data` и `/api/metrics`), загрузка файлов (drag & drop → POST /api/upload), Docker Compose (prod + dev), CI/CD (deploy.sh). Код парсера перенесён в `backend/parser.py` с нормализацией имён (Левенштейн + fuzzy). Мобильная адаптация базово реализована.

**Ниже — обнаруженные БАГИ и недоработки, требующие исправления перед деплоем.**

---

## 1. КРИТИЧЕСКИЕ БАГИ — Графики и визуализация

### ЗАДАЧА 1.1: CRM-диаграмма — заменить столбчатый график на круговую (doughnut) диаграмму

**Файл:** `assets/js/app.js`
**Строки:** ~2324–2407 (внутри функции `buildCorrelationCharts()`)
**Проблема:** Столбчатый bar-график плохо визуализирует распределение CRM-действий. Пользователь хочет круговую диаграмму. Кроме того, при смене оператора столбики не обновляются, а в режиме команды не показываются совокупные данные.

**ЧТО ДЕЛАТЬ:**

Найди блок `// 2. CRM conversion bar chart` (строка ~2324). Замени ВЕСЬ блок от `if (barEl) {` до закрывающей `}` после создания `crmBarChartInstance` (строка ~2407) на следующий код:

```javascript
      // 2. CRM conversion doughnut chart
      if (barEl) {
        const ctx = barEl.getContext('2d');
        if (crmBarChartInstance) crmBarChartInstance.destroy();
        
        const totals = {
          promised_to_pay: 0,
          refused_payment: 0,
          thinking: 0,
          declared_payment: 0,
          hung_up: 0,
          refused_conversation: 0,
          silence: 0
        };
        
        // Маппинг ключей — на случай если в БД ключи на русском
        const CRM_KEY_MAP = {
          'Обещание оплаты': 'promised_to_pay',
          'Отказ от оплаты': 'refused_payment', 
          'Обещание/Думает': 'thinking',
          'Думает': 'thinking',
          'Заявленный платёж': 'declared_payment',
          'Заявленный платеж': 'declared_payment',
          'Бросил трубку': 'hung_up',
          'Отказ от разговора': 'refused_conversation',
          'Тишина/Молчание': 'silence',
          'Тишина': 'silence',
          'promised_to_pay': 'promised_to_pay',
          'refused_payment': 'refused_payment',
          'thinking': 'thinking',
          'declared_payment': 'declared_payment',
          'hung_up': 'hung_up',
          'refused_conversation': 'refused_conversation',
          'silence': 'silence'
        };
        
        let targetName = "";
        if (currentViewMode === 'personal' && selectedEmployee) {
          const op = list.find(x => x.employee_name === selectedEmployee);
          if (op && op.crm_actions) {
            Object.entries(op.crm_actions).forEach(([k, v]) => {
              const mapped = CRM_KEY_MAP[k] || k;
              if (mapped in totals) totals[mapped] += v || 0;
            });
            targetName = selectedEmployee;
          }
        } else {
          // TEAM MODE — суммируем по всем операторам
          list.forEach(op => {
            if (op.crm_actions) {
              Object.entries(op.crm_actions).forEach(([k, v]) => {
                const mapped = CRM_KEY_MAP[k] || k;
                if (mapped in totals) totals[mapped] += v || 0;
              });
            }
          });
        }
        
        const titleEl = document.getElementById('title-crm-chart');
        if (titleEl) {
          if (currentViewMode === 'personal' && targetName) {
            titleEl.textContent = 'CRM-действия: ' + shortN(targetName);
          } else {
            titleEl.textContent = 'Распределение CRM-действий команды';
          }
        }
        
        const labels = ['Обещание платежа', 'Отказ от оплаты', 'Думает', 'Заявленный платеж', 'Бросил трубку', 'Отказ от разговора', 'Тишина'];
        const values = [totals.promised_to_pay, totals.refused_payment, totals.thinking, totals.declared_payment, totals.hung_up, totals.refused_conversation, totals.silence];
        const dColors = ['#22c55e', '#ef4444', '#facc15', '#06b6d4', '#ea580c', '#ec4899', '#94a3b8'];
        
        // Отфильтровать нулевые значения для чистой диаграммы
        const filtered = labels.map((l, i) => ({ label: l, value: values[i], color: dColors[i] }))
          .filter(item => item.value > 0);
        
        const total = filtered.reduce((s, item) => s + item.value, 0);
        
        if (filtered.length === 0) {
          // Если данных нет — показать пустую диаграмму
          crmBarChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: { labels: ['Нет данных'], datasets: [{ data: [1], backgroundColor: [thmC('#232b3e', '#e5e7eb')], borderWidth: 0 }] },
            options: { responsive: true, maintainAspectRatio: false, cutout: '55%', plugins: { legend: { display: false }, tooltip: { enabled: false } } }
          });
          return;
        }
        
        crmBarChartInstance = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: filtered.map(f => f.label),
            datasets: [{
              data: filtered.map(f => f.value),
              backgroundColor: filtered.map(f => f.color),
              borderColor: thmC('#0f172a', '#ffffff'),
              borderWidth: 2,
              hoverOffset: 8
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '55%',
            plugins: {
              legend: {
                position: window.innerWidth < 768 ? 'bottom' : 'right',
                labels: {
                  color: thmC('#94a3b8', '#52525b'),
                  font: { size: 11 },
                  padding: 12,
                  usePointStyle: true,
                  pointStyleWidth: 10,
                  generateLabels: function(chart) {
                    var dd = chart.data;
                    return dd.labels.map(function(label, i) {
                      var val = dd.datasets[0].data[i];
                      var pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
                      return {
                        text: label + ': ' + val + ' (' + pct + '%)',
                        fillStyle: dd.datasets[0].backgroundColor[i],
                        strokeStyle: dd.datasets[0].borderColor,
                        lineWidth: 1,
                        hidden: false,
                        index: i,
                        pointStyle: 'circle'
                      };
                    });
                  }
                }
              },
              tooltip: {
                backgroundColor: thmC('#1e2435', '#ffffff'),
                borderColor: thmC('#2d3748', '#e4e4e7'),
                borderWidth: 1,
                titleColor: thmC('#f1f5f9', '#27272a'),
                bodyColor: thmC('#94a3b8', '#52525b'),
                callbacks: {
                  label: function(context) {
                    var val = context.parsed;
                    var pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
                    return ' ' + context.label + ': ' + val + ' (' + pct + '%)';
                  }
                }
              }
            }
          }
        });
      }
```

> **ВАЖНО:** Переменная `crmBarChartInstance` остаётся прежней — не переименовывай её.

---

### ЗАДАЧА 1.2: Выпадающий список оператора — привязка onchange для обновления ВСЕХ графиков

**Файл:** `assets/js/app.js`
**Строки:** ~1130–1166 (функция `updateEmployeeSelect`)
**Проблема:** При выборе оператора из выпадающего списка графики могут не обновляться, если `onchange` вызывает только `showEmployee()`, а не `updateDashboard()`.

**ЧТО ПРОВЕРИТЬ И ИСПРАВИТЬ:**

Открой функцию `updateEmployeeSelect()`. Убедись, что обработчик `onchange` у select-а вызывает `updateDashboard()`. Вот правильная версия:

```javascript
      // КРИТИЧЕСКИ ВАЖНО: привязать onchange для обновления всех графиков
      select.onchange = function() {
        selectedEmployee = this.value;
        updateDashboard();
      };
```

Если в текущем коде `onchange` вызывает что-то другое (например, только `showEmployee()`) — замени на код выше. `updateDashboard()` вызовет `buildCorrelationCharts()`, `buildLineChart()`, `buildCharts()`, `renderKPIs()` и `showEmployee()` — все графики обновятся.

---

### ЗАДАЧА 1.3: buildCharts() — TQS bar не реагирует на personal mode

**Файл:** `assets/js/app.js`
**Строки:** ~2175–2209 (функция `buildCharts()`)
**Проблема:** Функция `buildCharts()` всегда рисует ВСЕ операторов, независимо от `currentViewMode`. В режиме «Сотрудник» она должна подсвечивать выбранного.

**ЧТО ДЕЛАТЬ:**

Замени функцию `buildCharts()` (от `function buildCharts() {` до закрывающей `}`) на:

```javascript
    function buildCharts() {
      const trendEl = document.getElementById('trendChart');
      if (!trendEl) return;
      const ctx = trendEl.getContext('2d');
      if (trendChart) trendChart.destroy();
      let labels = [], data = [], colors = [], borderWidths = [];
      Object.keys(DASHBOARD_DATA).sort().forEach(name => {
        if(name.includes('Промежуточный')) return;
        const m = DASHBOARD_DATA[name]?.months?.[currentMonth]; if (!m) return;
        const d = _getEffectiveData(m);
        if (!d || !d.svp) return;
        const t = (d.tqs || 0) * 100;
        labels.push(shortN(name)); data.push(t);
        
        // Подсветка выбранного оператора в personal mode
        const isSelected = currentViewMode === 'personal' && selectedEmployee === name;
        if (isSelected) {
          colors.push('#a78bfa');
          borderWidths.push(3);
        } else {
          colors.push(t >= 75 ? '#22c55e' : (t >= 60 ? '#eab308' : '#f87171'));
          borderWidths.push(0);
        }
      });
      if (!labels.length) return;
      trendChart = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'TQS %', data, backgroundColor: colors, borderColor: colors.map(function(c, i) { return borderWidths[i] > 0 ? '#ffffff' : 'transparent'; }), borderWidth: borderWidths, borderRadius: 4 }] },
        options: {
          responsive: true, maintainAspectRatio: false,
          scales: {
            y: { min: 0, max: 100, grid: { color: thmC('#232b3e', 'rgba(0,0,0,0.03)'), lineWidth: thmC(1, 0.5) }, ticks: { color: thmC('#64748b', '#71717a'), callback: function(v) { return v + '%'; } } },
            x: { grid: { display: false }, ticks: { color: thmC('#64748b', '#71717a'), font: { size: 10 }, maxRotation: 45 } }
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: thmC('#1e2435', '#ffffff'),
              borderColor: thmC('#2d3748', '#e4e4e7'),
              borderWidth: 1,
              titleColor: thmC('#f1f5f9', '#27272a'),
              bodyColor: thmC('#94a3b8', '#52525b')
            }
          }
        }
      });
    }
```

---

### ЗАДАЧА 1.4: Scatter chart — подсветка выбранного оператора в personal mode

**Файл:** `assets/js/app.js`
**Строки:** ~2236–2260 (внутри `buildCorrelationCharts`)
**Проблема:** Scatter chart (TQS vs Collections) не выделяет выбранного оператора.

**ЧТО ДЕЛАТЬ:**

Найди строку ~2236 (где создаётся `scatterData`). Замени:

```javascript
        const scatterData = list.map(op => ({
          x: Math.round((op.tqs || 0) * 100 * 10) / 10,
          y: op.collected_amount || 0,
          name: op.employee_name,
          pattern: op.crm_behavior_pattern || 'balanced'
        }));
```

На:

```javascript
        const scatterData = list.map(op => ({
          x: Math.round((op.tqs || 0) * 100 * 10) / 10,
          y: op.collected_amount || 0,
          name: op.employee_name,
          pattern: op.crm_behavior_pattern || 'balanced',
          isSelected: currentViewMode === 'personal' && selectedEmployee === op.employee_name
        }));
```

Затем найди `pointRadius: 6` и `pointHoverRadius: 8` (строки ~2258-2259) и замени на:

```javascript
              pointRadius: function(ctx) {
                var item = ctx.raw;
                return item && item.isSelected ? 12 : 6;
              },
              pointHoverRadius: function(ctx) {
                var item = ctx.raw;
                return item && item.isSelected ? 14 : 8;
              },
              pointBorderWidth: function(ctx) {
                var item = ctx.raw;
                return item && item.isSelected ? 3 : 1.5;
              },
```

---

### ЗАДАЧА 1.5: Progress Wave — контейнер с фиксированной высотой

**Файл:** `analytics.html`
**Строка:** 77
**Проблема:** Карточка `height:450px` с `padding:20px` — при двустрочной легенде Chart.js переполняется.

**ЧТО ДЕЛАТЬ:**

Строка 77 — замени:
```html
<div class="card" style="margin-bottom:20px;padding:20px;height:450px;">
```
На:
```html
<div class="card" style="margin-bottom:20px;padding:20px;min-height:420px;">
```

---

## 2. Навигация «Загрузка → Аналитика»

### ЗАДАЧА 2.1: Автоматический возврат в оперативное пространство после загрузки

**Файл:** `assets/js/app.js`
**Строки:** ~2884 (внутри `FileUploader.handleFiles()`)
**Проблема:** После успешной загрузки файлов пользователь застревает в секции загрузки.

**ЧТО ДЕЛАТЬ:**

После строки `this.log('✅ Дашборд обновлён!', 'success');` (строка ~2884) добавь:

```javascript
                // Автоматический переход в оперативное пространство через 2 секунды
                this.log('🔄 Переключение в аналитику через 2 секунды...', 'info');
                setTimeout(function() {
                  setViewMode('team');
                }, 2000);
```

---

### ЗАДАЧА 2.2: Добавить кнопку «Вернуться к аналитике» в секцию загрузки

**Файл:** `analytics.html`
**Строки:** после строки 173 (после `<div class="page-sub">...`)

**ЧТО ДЕЛАТЬ:**

После строки 173 (после `<div class="page-sub">...</div>`) добавь:

```html
      <button onclick="setViewMode('team')" style="margin-top:12px;margin-bottom:12px;padding:8px 18px;background:linear-gradient(90deg,#6366f1,#4f46e5);color:white;border:none;border-radius:8px;font-weight:700;font-size:12px;cursor:pointer;transition:all 0.2s;display:inline-flex;align-items:center;gap:6px;" onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align:middle;"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
        Вернуться к аналитике
      </button>
```

---

## 3. CSS-исправления для графиков

### ЗАДАЧА 3.1: Добавить overflow:hidden на .card

**Файл:** `assets/css/style.css`
**Строки:** ~272–278 (класс `.card`)

**ЧТО ДЕЛАТЬ:**

Найди блок `.card {` и добавь `overflow: hidden;`:

```css
.card {
  background: rgba(30, 36, 53, 0.65);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  overflow: hidden;
}
```

> **ВНИМАНИЕ:** Если это обрезает tooltips или dropdown-меню в карточках, используй `overflow: visible` через inline style на конкретных карточках, где нужны tooltips, а не графики.

---

### ЗАДАЧА 3.2: Улучшить .chart-wrap

**Файл:** `assets/css/style.css`
**Строки:** ~592–595

**ЧТО ДЕЛАТЬ:**

Замени:
```css
.chart-wrap {
  position: relative;
  height: 320px;
}
```

На:
```css
.chart-wrap {
  position: relative;
  height: 320px;
  width: 100%;
  overflow: hidden;
}
```

---

### ЗАДАЧА 3.3: Адаптивные высоты графиков на мобильных

**Файл:** `assets/css/style.css`
**Строки:** внутри `@media (max-width: 768px)` (перед закрывающей `}` этого блока)

**ЧТО ДОБАВИТЬ:**

```css
    /* Адаптивные высоты графиков */
    .chart-wrap {
      height: 250px !important;
    }
```

Внутри `@media (max-width: 480px)` добавь:

```css
    .chart-wrap {
      height: 200px !important;
    }
```

---

## 4. UX-улучшения

### ЗАДАЧА 4.1: Подзаголовок страницы — убрать хардкод даты

**Файл:** `analytics.html`, строка 27
**Проблема:** Захардкожен текст `Февраль–Март 2026` — устаревает.

**ЧТО ДЕЛАТЬ:**

Замени строку 27:
```html
      <div class="page-sub">Динамика команды Soft Collection · Февраль–Март 2026</div>
```
На:
```html
      <div class="page-sub" id="page-subtitle">Динамика команды Soft Collection</div>
```

В `app.js`, в функции `updateDashboard()` (после строки `renderKPIs(dataPayload);`, примерно строка 1189) добавь:

```javascript
        // Обновить подзаголовок с текущим периодом
        const subtitleEl = document.getElementById('page-subtitle');
        if (subtitleEl) {
          subtitleEl.textContent = 'Динамика команды Soft Collection \u00b7 ' + currentMonth + (currentPeriod && currentPeriod !== 'Все' && currentPeriod !== 'Все периоды' ? ' \u00b7 ' + currentPeriod : '');
        }
```

---

### ЗАДАЧА 4.2: Sidebar footer — убрать хардкод даты

**Файл:** `assets/js/sidebar.js`
**Проблема:** Текст `Февраль–Апрель 2026` захардкожен.

**ЧТО ДЕЛАТЬ:**

Найди `<div>Февраль–Апрель 2026</div>` внутри sidebar HTML и замени на:
```html
<div>QC Dashboard SC</div>
```

---

### ЗАДАЧА 4.3: При смене месяца — обновить чеклист загрузки

**Файл:** `assets/js/app.js`
**Строки:** Внутри `initFilters()` — обработчик `monthSelect.onchange`

**ЧТО ПРОВЕРИТЬ:**

Найди, где привязывается `onchange` к `monthSelect`. После вызова `updateDashboard()` (или `updatePeriodTabs()`) добавь:

```javascript
      if (window.FileUploader) {
        window.FileUploader.refreshChecklist();
      }
```

---

## 5. Мелкие баги и неудобства

### ЗАДАЧА 5.1: Forecast chart — min Y жёстко на 40%

**Файл:** `assets/js/app.js`
**Строки:** ~1389 (внутри `buildAreaForecastChart`)

**ЧТО ДЕЛАТЬ:**

Найди `min: 40` в настройках forecast chart и замени на:

```javascript
            min: Math.max(0, Math.min.apply(null, historyData.filter(function(v) { return v > 0; })) - 10),
```

---

### ЗАДАЧА 5.2: Tendencies (тенденции) не отображаются в drilldown

**Файл:** `assets/js/app.js`
**Строки:** внутри `showEmployee()` (~1640–1941)

**ЧТО ДЕЛАТЬ:**

В `showEmployee()`, найди где используется `op.tendencies` или `op.recommendations`. Перед этим блоком добавь fallback к DASHBOARD_DATA:

```javascript
      // Fallback tendencies из DASHBOARD_DATA
      var tendencies = op.tendencies || op.recommendations || '';
      if (!tendencies && DASHBOARD_DATA[name]) {
        var empData = DASHBOARD_DATA[name]?.months?.[currentMonth];
        if (empData) {
          var pd = _getEffectiveData(empData);
          if (pd) {
            tendencies = pd.tendencies || pd.rec || '';
          }
        }
      }
```

И используй эту переменную `tendencies` вместо `op.tendencies`.

---

### ЗАДАЧА 5.3: Файлы reg_base.html и reg_rules.html — не привязаны к навигации

**Файл:** `assets/js/sidebar.js`
**Проблема:** Файлы существуют, но нет ссылок в sidebar.

**ЧТО ДЕЛАТЬ:**
Если файлы содержат полезный контент — добавь в sidebar в секцию РЕГЛАМЕНТ. Если файлы — заглушки, **НЕ ТРОГАЙ**.

---

## 6. Чеклист проверки

### Функциональные проверки

- [x] **CRM doughnut chart:** В режиме «Команда» — показывает совокупные CRM-данные всех операторов
- [x] **CRM doughnut chart:** В режиме «Сотрудник» — показывает CRM-данные выбранного оператора
- [x] **CRM doughnut chart:** Смена оператора → диаграмма обновляется мгновенно
- [x] **CRM doughnut chart:** Если данных нет — показывает "Нет данных" (серый круг)
- [x] **Progress Wave chart:** Линии TQS и Сборов не выходят за карточку
- [x] **Progress Wave chart:** В режиме «Сотрудник» — показывает данные выбранного оператора
- [x] **TQS по операторам:** В режиме «Сотрудник» — выбранный оператор подсвечен фиолетовым
- [x] **Scatter chart:** В режиме «Сотрудник» — точка выбранного оператора увеличена
- [x] **Upload → Team:** После загрузки — автопереход в аналитику через ~2 сек
- [x] **Кнопка «Вернуться»:** Отображается и работает
- [x] **Подзаголовок:** Обновляется при смене месяца

### Визуальные проверки

- [x] Десктоп (1920x1080): все графики в карточках
- [x] Планшет (768px): графики в одну колонку, читаемы
- [x] Мобильный (375px): графики уменьшены, doughnut легенда снизу
- [x] Тёмная тема: контраст достаточный
- [x] Светлая тема: контраст достаточный

---

## КАРТА ФАЙЛОВ И ИЗМЕНЕНИЙ

| Файл | Задачи | Тип изменений |
|------|--------|--------------|
| `assets/js/app.js` | 1.1, 1.2, 1.3, 1.4, 2.1, 4.1, 4.3, 5.1, 5.2 | Замена chart type, подсветка selected, навигация, UX |
| `analytics.html` | 1.5, 2.2, 4.1 | Высоты контейнеров, кнопка «назад», подзаголовок |
| `assets/css/style.css` | 3.1, 3.2, 3.3 | overflow:hidden, .chart-wrap, адаптивные высоты |
| `assets/js/sidebar.js` | 4.2, 5.3 | Хардкод даты, опционально навигация |

---

## ПОРЯДОК ВЫПОЛНЕНИЯ

1. **Сначала CSS** (задачи 3.1, 3.2, 3.3) — безопасные изменения
2. **Затем HTML** (задачи 1.5, 2.2, 4.1) — структурные изменения
3. **Затем JS — графики** (задачи 1.1, 1.3, 1.4) — замена chart type и подсветка
4. **Затем JS — данные** (задача 1.2) — исправление onchange
5. **Затем JS — навигация** (задачи 2.1, 4.3) — UX flow
6. **Последними — мелочи** (задачи 5.1, 5.2, 4.2)
7. **В конце — полный чеклист** (раздел 6)

---

> **НАПОМИНАНИЕ:** Проект использует Chart.js v4.4.0 (CDN в analytics.html).
> Не устанавливай дополнительных зависимостей.
> Все изменения — чисто фронтенд (JS + CSS + HTML).
> Бэкенд (backend/app.py и backend/parser.py) НЕ ТРОГАЙ, если не указано иное.
> **НЕ УДАЛЯЙ** существующие комментарии и docstrings.

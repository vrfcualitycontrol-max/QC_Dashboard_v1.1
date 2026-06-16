// ========== GLOBAL ERROR BOUNDARY ==========
window.onerror = function(msg, src, line, col, err) {
  console.error('[QC Dashboard Error]', msg, 'at', src, line + ':' + col, err);
  return true;
};

window.addEventListener('unhandledrejection', function(e) {
  console.error('[QC Dashboard Promise Error]', e.reason);
});

    // ========== 1. DASHBOARD DATA ==========
    let DASHBOARD_DATA = {};
    let DATA_LOADED = false;

    function isValidEmployeeName(name) {
      if (!name) return false;
      const lower = name.toLowerCase().trim();
      if (lower === 'admin' || lower.includes('названия строк') || lower.includes('количество по полю') || lower.includes('период') || lower.includes('промежуточный')) {
        return false;
      }
      const hasCyrillic = /[а-яёА-ЯЁ]/;
      if (!hasCyrillic.test(name)) {
        return false;
      }
      return true;
    }
    window.isValidEmployeeName = isValidEmployeeName;

    async function loadDashboardDataFromAPI() {
      try {
        const response = await fetch('/api/dashboard-data');
        if (!response.ok) throw new Error('API error: ' + response.status);
        const rawData = await response.json();
        DASHBOARD_DATA = {};
        Object.entries(rawData).forEach(([name, data]) => {
          if (isValidEmployeeName(name)) {
            DASHBOARD_DATA[name] = data;
          }
        });
        DATA_LOADED = true;
        console.log('[INFO] Dashboard data loaded from API, employees:', Object.keys(DASHBOARD_DATA).length);
        window.DASHBOARD_DATA = DASHBOARD_DATA; // make globally accessible
        return true;
      } catch (err) {
        console.error('[ERROR] Failed to load from API, trying fallback:', err);
        // Fallback to window.DASHBOARD_DATA_FALLBACK if present
        if (typeof window.DASHBOARD_DATA_FALLBACK !== 'undefined') {
          const rawData = window.DASHBOARD_DATA_FALLBACK;
          DASHBOARD_DATA = {};
          Object.entries(rawData).forEach(([name, data]) => {
            if (isValidEmployeeName(name)) {
              DASHBOARD_DATA[name] = data;
            }
          });
          DATA_LOADED = true;
          window.DASHBOARD_DATA = DASHBOARD_DATA;
          return true;
        }
        return false;
      }
    }

    function showLoading(show) {
      let loader = document.getElementById('dashboard-loader');
      if (!loader && show) {
        loader = document.createElement('div');
        loader.id = 'dashboard-loader';
        loader.innerHTML = `
          <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
              height:300px;color:#a78bfa;font-size:14px;font-weight:600;">
              <div class="spinner" style="width:40px;height:40px;border:3px solid rgba(167,139,250,0.2);
                  border-top-color:#a78bfa;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:16px;">
              </div>
              Загрузка данных...
          </div>
        `;
        const main = document.getElementById('main');
        if (main) main.prepend(loader);
      }
      if (loader) loader.style.display = show ? 'block' : 'none';
    }
    
    // ========== 2. STATIC DATA ==========
    const CRITERIA = [
      { n: 1, name: 'Приветствие, идентификация и прощание', weight: 5, color: '#6366f1', desc: 'Соблюдение официального протокола входа в контакт.' },
      { n: 2, name: 'Этика общения', weight: 5, color: '#8b5cf6', desc: 'Отсутствие конфликтогенов, соблюдение норм делового этикета.' },
      { n: 3, name: 'Работа в системе (CRM)', weight: 10, color: '#a78bfa', desc: 'Соответствие статуса в CRM фактическому итогу.' },
      { n: 4, name: 'Легендирование', weight: 15, color: '#7c3aed', desc: 'Тактическое использование сценариев: «компетенция» + «эскалация».' },
      { n: 5, name: 'Информирование о задолженности', weight: 10, color: '#4f46e5', desc: 'Точность и полнота данных о суммах, сроках DPD.' },
      { n: 6, name: 'Аргументация', weight: 20, color: '#ec4899', desc: 'Глубина и логика работы с отказами. НПА РУз.' },
      { n: 7, name: 'Манипуляция', weight: 10, color: '#f59e0b', desc: 'Применение психологических триггеров давления.' },
      { n: 8, name: 'Выставление требований', weight: 15, color: '#10b981', desc: 'Чёткость: конкретный срок, сумма, способ оплаты.' },
      { n: 9, name: 'Подведение итогов (Якунлаш)', weight: 10, color: '#06b6d4', desc: 'Резюмирование + фиксация разговора.' },
    ];

    const SVP_STAGES_REG = [
      { num: 'Этап 1', title: 'Фаза входа в контакт', desc: 'Приветствие · Идентификация · Легендирование', detail: 'Установление стандартов приветствия. Тактическое легендирование: «компетенция» + «эскалация».' },
      { num: 'Этап 2', title: 'Информационный блок', desc: 'Информирование о долге · DPD · Открытые вопросы', detail: 'Озвучивание суммы и срока. Диагностика ситуации через открытые вопросы.' },
      { num: 'Этап 3', title: 'Блок активного взыскания', desc: 'Аргументация · Манипуляция · РсВ', detail: 'Переход от стандартных доводов к нормативной аргументации (НПА и условия Оферты).' },
      { num: 'Этап 4', title: 'Фиксация обязательств', desc: 'Требования · Итоги (Якунлаш) · Прощание', detail: 'Стандартизация требований: конкретный срок PTP, полная сумма, способы оплаты.' },
      { num: 'Этап 5', title: 'Интеграция в систему QC', desc: 'Весовые коэффициенты · TQS', detail: 'Увязка каждого этапа СВП с весовыми коэффициентами (5–20%) в оценочном листе QC.' },
    ];

    const LAWS = [
      { art: 'Ст. 236', name: 'Надлежащее исполнение', text: 'Обязательства должны исполняться надлежащим образом в соответствии с условиями договора.', use: '«Согласно ст. 236 ГК РУз, Вы обязаны исполнить обязательства в точном соответствии с условиями оферты...»' },
      { art: 'Ст. 237', name: 'Запрет одностороннего отказа', text: 'Односторонний отказ от исполнения обязательства и одностороннее изменение его условий не допускаются.', use: '«Согласно ст. 237 ГК РУз, Вы не вправе в одностороннем порядке отказаться от исполнения договорных обязательств...»' },
      { art: 'Ст. 333', name: 'Ответственность за неисполнение', text: 'Отсутствие у должника денежных средств само по себе не освобождает его от ответственности.', use: '«Ст. 333 ГК РУз прямо указывает: отсутствие денег не снимает с Вас обязательств...»' },
      { art: 'Ст. 421', name: 'Залог до полной оплаты', text: 'Товар, проданный в кредит, находится в залоге у продавца до момента его полной оплаты.', use: '«В соответствии со ст. 421 ГК РУз приобретённый Вами товар является залоговым имуществом VRF...»' },
    ];

    const OBJECTIONS = [
      { id: 1, cat: 'Финансы', q: '«Нет денег / не могу заплатить»', script: `Понимаю вашу ситуацию. Однако согласно ст. 333 ГК РУз, отсутствие денежных средств само по себе не освобождает должника от ответственности. Подскажите: когда именно вы сможете внести платёж?`, laws: ['Ст. 333'] },
      { id: 2, cat: 'Финансы', q: '«Сейчас нет возможности / зарплата придёт позже»', script: `Согласно ст. 236 ГК РУз, обязательства по договору должны исполняться в установленный срок. Назовите конкретную дату — я внесу PTP.`, laws: ['Ст. 236'] },
      { id: 3, cat: 'Финансы', q: '«Я уже оплатил / это ошибка»', script: `Предоставьте подтверждение оплаты. Платёж по системе не поступал. По регламенту п. 5.4 Оферты платёж считается принятым после отражения в системе.`, laws: [] },
      { id: 4, cat: 'Финансы', q: '«Почему так много пени?»', script: `Сумма формируется из: основного долга, пени (п. 5.10 Оферты) и затрат на взыскание (ст. 324 ГК РУз). Погасив сегодня, вы зафиксируете текущий размер долга.`, laws: ['Ст. 324'] },
      { id: 5, cat: 'Финансы', q: '«Я не знал о штрафах»', script: `Согласно п. 4.1.6 Оферты, при просрочке более 60 дней сумма увеличивается. Ст. 324 ГК РУз подтверждает право на возмещение убытков.`, laws: ['Ст. 324'] },
      { id: 6, cat: 'Личные обстоятельства', q: '«Почему вы звоните мне на работу / в махаллю?»', script: `Подписывая договор, вы предоставили Компании право уведомлять (п. 4.1.7 Договора). Самый быстрый способ прекратить — погасить задолженность.`, laws: [] },
      { id: 7, cat: 'Личные обстоятельства', q: '«Я не давал согласия на запись»', script: `Обработка данных производится в целях исполнения Договора (ст. 18 ЗРУ «О персональных данных»). Запись — внутренний регламент QC.`, laws: [] },
      { id: 8, cat: 'Товар', q: '«Я продал/подарил товар»', script: `По ст. 421 ГК РУз товар в залоге до полной оплаты. Отчуждение — ст. 168 УК РУз (мошенничество) и ст. 233 УК РУз.`, laws: ['Ст. 421'] },
      { id: 9, cat: 'Товар', q: '«Товар бракованный»', script: `Факт приёмки подтверждает исправность. По ст. 417 ГК РУз все риски перешли к вам. Претензии — отдельный процесс.`, laws: [] },
      { id: 10, cat: 'Товар', q: '«Товар сломался — не плачу»', script: `По п. 5.6 Договора выплаты независимы от состояния товара (ст. 236 ГК РУз). Гарантия — через Магазин.`, laws: ['Ст. 236'] },
      { id: 11, cat: 'Юридические вопросы', q: '«Пусть подают в суд»', script: `По п. 9.4 Договора и ПКМ № 26 — бесспорный порядок через нотариуса. БПИ арестует счета немедленно.`, laws: [] },
      { id: 12, cat: 'Юридические вопросы', q: '«Оферта — не договор»', script: `Договор — публичная оферта (ст. 369 ГК РУз). SMS-код = акцепт (ст. 360, 107 ГК РУз).`, laws: ['Ст. 237'] },
      { id: 13, cat: 'Юридические вопросы', q: '«Почему сразу всю сумму?»', script: `При просрочке 30+ дней — досрочное погашение (п. 9.3 Договора, ст. 422 ГК РУз).`, laws: ['Ст. 236'] },
      { id: 14, cat: 'Юридические вопросы', q: '«Мне угрожают уголовной ответственностью»', script: `Сотрудники информируют о законных последствиях. Добровольное погашение устранит правовые риски.`, laws: [] },
      { id: 15, cat: 'Юридические вопросы', q: '«БПИ придёт не скоро»', script: `Ст. 23 ЗРУ — постановление в течение 1 рабочего дня. Расходы растут ежедневно.`, laws: [] },
      { id: 16, cat: 'Личные обстоятельства', q: '«Я болен / в больнице»', script: `По ст. 237 ГК РУз обязательства не прекращаются. Кто из близких может оплатить через Payme/Click?`, laws: ['Ст. 237'] },
      { id: 17, cat: 'Личные обстоятельства', q: '«Я в другом городе/стране»', script: `Payme, Click, Paynet — дистанционно. Местонахождение не влияет на обязательства (ст. 236).`, laws: ['Ст. 236'] },
      { id: 18, cat: 'Личные обстоятельства', q: '«Я не тот человек»', script: `ФИО, дата рождения совпадают. SMS-акцепт = электронная подпись (ст. 107, 369 ГК РУз).`, laws: [] },
      { id: 19, cat: 'Финансы', q: '«Готов платить частями»', script: `Частичная оплата не останавливает пени (п. 5.10). Но снизит базу. Готовы к оплате сегодня?`, laws: ['Ст. 333'] },
      { id: 20, cat: 'Юридические вопросы', q: '«Подам жалобу / в суд / к прокурору»', script: `Ваше право. Компания действует в рамках закона (ст. 360, 369 ГК РУз, ПКМ № 26). Обязательства продолжают действовать.`, laws: ['Ст. 236', 'Ст. 237'] },
    ];

    const SVP_STAGES_B2B = [{"stage": "DPD 1-10", "title": "Зеленый уровень", "desc": "Лояльность и Репутация", "detail": "Цель: Профилактика просрочки, акцент на добросовестности (ст. 9 ГК РУз) и сохранении доступа к кредитным инструментам."}, {"stage": "DPD 10-20", "title": "Желтый уровень", "desc": "Финансовое давление и Убытки – потеря контроля", "detail": "Цель: Обозначение существенного характера нарушения и подготовка к принудительным мерам."}, {"stage": "DPD 20-30", "title": "Красный уровень", "desc": "Принудительное взыскание", "detail": "Цель: Ультимативное требование, трансляция неизбежности расторжения сотрудничества, возможного изъятия имущества и краха репутации."}];
    const LAWS_B2B = [{"art": "Ст. 236", "name": "Надлежащее исполнение", "text": "Обязательства должны исполняться надлежащим образом в соответствии с условиями обязательства и требованиями законодательства.", "use": "Используется для аргументации соблюдения графика платежей."}, {"art": "Ст. 237", "name": "Недопустимость отказа", "text": "Односторонний отказ от исполнения обязательств и одностороннее изменение его условий не допускаются.", "use": "Сотрудник не имеет права нарушать договоренности."}, {"art": "Ст. 14, 324", "name": "Взыскание убытков", "text": "Лицо, право которого нарушено, может требовать полного возмещения причиненных ему убытков.", "use": "Для предупреждения о дополнительных финансовых потерях при суде."}, {"art": "Ст. 736", "name": "Досрочное взыскание", "text": "Кредитор вправе потребовать досрочного возврата всей оставшейся суммы долга вместе с причитающимися процентами.", "use": "При нарушении сроков возврата кредита."}, {"art": "Ст. 259", "name": "Взыскание на имущество", "text": "Обязательства могут погашаться за счет реализации имущества должника.", "use": "Информирование о крайней мере взыскания."}, {"art": "Ст. 293", "name": "Солидарная ответственность", "text": "Поручитель и должник отвечают перед кредитором солидарно.", "use": "Используется при работе с поручителем."}, {"art": "Ст. 48", "name": "Ответственность юрлиц", "text": "Юридические лица несут ответственность по обязательствам всем своим имуществом.", "use": "Давление на активы предприятия."}, {"art": "Ст. 100", "name": "Защита чести", "text": "Защита чести, достоинства и деловой репутации.", "use": "Аргументация риска для деловой репутации должника."}];
    const OBJECTIONS_B2B = [
  {
    "id": 1,
    "cat": "Бизнес-риски",
    "q": "Сначала взыскивайте с основного должника (от поручителя)",
    "script": "Договор устанавливает солидарный характер ответственности. Кредитор наделен правом требовать исполнения от любого из ответчиков по своему усмотрению, не соблюдая очередность. Вы отвечаете в полном объеме наравне с заемщиком.",
    "laws": [
      "Ст. 293"
    ]
  },
  {
    "id": 2,
    "cat": "Финансы",
    "q": "У меня нет денежных средств и ликвидного имущества",
    "script": "Ваше финансовое положение не является основанием для невыплаты (Ст. 333 ГК РУз). Вы несете ответственность по своим обязательствам всем принадлежащим имуществом, включая то, которое будет приобретено в будущем (Ст. 48 ГК РУз).",
    "laws": [
      "Ст. 48",
      "Ст. 333"
    ]
  },
  {
    "id": 3,
    "cat": "Условия",
    "q": "Я думал иначе/не понимал условия договора",
    "script": "Подписывая договор, вы подтвердили факт волеизъявления и понимание условий. Субъективное непонимание при наличии вашей подписи не освобождает от обязательств.",
    "laws": [
      "Ст. 101",
      "Ст. 108",
      "Ст. 365"
    ]
  },
  {
    "id": 4,
    "cat": "Отговорки",
    "q": "Я выступал лишь в качестве свидетеля",
    "script": "Понятие «свидетель» отсутствует в кредитных правоотношениях. Подписав договор поручительства, вы взяли на себя обязанность исполнить обязательство за должника в полном объеме.",
    "laws": [
      "Ст. 292"
    ]
  },
  {
    "id": 5,
    "cat": "Условия",
    "q": "Я требую сначала закрывать основной долг",
    "script": "Законом установлена строгая очередность погашения, при которой штрафы гасятся после основного долга и процентов, и этот порядок обязателен для всех.",
    "laws": [
      "Ст. 248"
    ]
  },
  {
    "id": 6,
    "cat": "Финансы",
    "q": "В связи с кризисом я не имею возможности платить",
    "script": "Односторонний отказ недопустим. Изменение финансового положения или рыночной конъюнктуры не является законным основанием для прекращения выплат.",
    "laws": [
      "Ст. 237"
    ]
  },
  {
    "id": 7,
    "cat": "Условия",
    "q": "Я буду платить частями по своим возможностям",
    "script": "Обязательство должно исполняться надлежащим образом — в полном объеме и в сроки по графику. Иное частичное исполнение не является надлежащим.",
    "laws": [
      "Ст. 234",
      "Ст. 236"
    ]
  },
  {
    "id": 8,
    "cat": "Отговорки",
    "q": "Банк должен войти в положение и подождать",
    "script": "Вы обязаны полностью соблюдать график платежей. Отсутствие денег не является непреодолимой силой, и банк вправе требовать возврата долга со штрафами.",
    "laws": [
      "Ст. 333",
      "Ст. 327"
    ]
  }
];
    let currentObjMode = 'B2C';

    function setObjMode(mode) {
      currentObjMode = mode;
      const b2c = document.getElementById('btn-b2c');
      const b2b = document.getElementById('btn-b2b');
      if(b2c) b2c.className = 'cat-tab' + (mode === 'B2C' ? ' active' : '');
      if(b2b) {
          b2b.className = 'cat-tab' + (mode === 'B2B' ? ' active' : '');
          b2b.style.background = mode === 'B2B' ? '#eab308' : 'rgba(234,179,8,0.1)';
          b2b.style.color = mode === 'B2B' ? '#0f1117' : '#facc15';
      }
      
      currentCat = 'Все';
      renderSVP();
      renderLaws();
      renderCatTabs();
      renderObjList();
    }

    const CATEGORIES = ['Все', 'Финансы', 'Товар', 'Юридические вопросы', 'Личные обстоятельства'];
    const CAT_COLORS = { 'Финансы': { bg: 'rgba(74,222,128,0.15)', color: '#4ade80' }, 'Товар': { bg: 'rgba(251,146,60,0.15)', color: '#fb923c' }, 'Юридические вопросы': { bg: 'rgba(167,139,250,0.15)', color: '#a78bfa' }, 'Личные обстоятельства': { bg: 'rgba(96,165,250,0.15)', color: '#60a5fa' } };

    // ========== 3. GRADING ALGORITHM ==========
    const SVP_KEYS = ["Приветствие", "Этика", "CRM", "Легенда", "Задолж.", "Аргумент.", "Манипул.", "Требования", "Итоги"];

    function getDiagnosticForCriterion(allPeriods, criterion) {
      if (!allPeriods || !allPeriods.length) return { text: 'Нет данных', bg: '#64748b', rank: -1 };

      // Собираем процентные значения по критерию из всех периодов
      const percents = [];
      allPeriods.forEach(p => {
        if (p?.svp && p.svp[criterion] !== undefined) {
          percents.push(p.svp[criterion] * 100);
        } else if (p?.raw_scores && p.raw_scores[criterion]) {
          // Если есть raw_scores, конвертируем в процент
          const rawVals = p.raw_scores[criterion];
          if (rawVals.length > 0) {
            const avg = rawVals.reduce((a, b) => a + b, 0) / rawVals.length;
            percents.push(avg * 100);
          }
        }
      });

      const n = percents.length;
      if (n === 0) return { text: 'Нет данных', bg: '#64748b', rank: -1 };

      // Используем средний процент для диагностики (алгоритм Pro)
      const avgPercent = percents.reduce((a, b) => a + b, 0) / n;
      
      if (avgPercent <= 24) return { text: 'Несоответствие СВП', bg: '#ef4444', rank: 6 };
      if (avgPercent <= 49) return { text: 'Критическая просадка', bg: '#ef4444', rank: 5 };
      if (avgPercent <= 64) return { text: 'Систематическая недоработка', bg: '#eab308', rank: 4 };
      if (avgPercent <= 74) return { text: 'Недоработка критерия', bg: '#eab308', rank: 3 };
      if (avgPercent <= 84) return { text: 'Нестабильная отработка', bg: '#eab308', rank: 2 };
      if (avgPercent <= 99) return { text: 'Критерий требует внимания', bg: '#eab308', rank: 1 };
      return { text: 'Полное соответствие', bg: '#22c55e', rank: 0 };
    }

    // ========== 4. UI ENGINE ==========
    
    function isLight() { return document.body.classList.contains('light-mode'); }
    function thmC(dark, light) { return isLight() ? light : dark; }

    const SVG_ICONS = {
      money: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>`,
      activity: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>`,
      target: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="vertical-align:middle;margin-right:4px;"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>`,
      warning: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="vertical-align:middle;margin-right:4px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
      info: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="vertical-align:middle;margin-right:4px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`,
      success: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="vertical-align:middle;margin-right:4px;"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
      danger: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="vertical-align:middle;margin-right:4px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
      brain: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>`,
      trend: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>`,
      help: `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align:middle;margin-right:3px;"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
      refresh: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>`
    };


    let currentViewMode = localStorage.getItem('view-mode') || 'team';
    if (currentViewMode === 'upload') {
      currentViewMode = 'team';
    }
    let currentMonth = localStorage.getItem('current-month') || null;
    let currentPeriod = "Все";
    // Для страницы Rating
    let currentRatingPeriod = "Все"; // внутримесячный период для рейтинга
    let selectedEmployee = null;
    let trendChart = null;
    let currentHeatmapMode = localStorage.getItem('heatmap-mode') || 'heatmap';

    window.setViewMode = function(mode) {
      currentViewMode = mode;
      localStorage.setItem('view-mode', mode);
      
      const tabTeam = document.getElementById('tab-view-team');
      const tabPersonal = document.getElementById('tab-view-personal');
      const tabUpload = document.getElementById('tab-view-upload');
      const select = document.getElementById('employeeSelect');
      const sectionOperations = document.getElementById('section-operations');
      const sectionUpload = document.getElementById('section-upload');
      
      if (tabTeam && tabPersonal) {
        tabTeam.classList.remove('active');
        tabPersonal.classList.remove('active');
        if (tabUpload) tabUpload.classList.remove('active');
        
        if (mode === 'team') {
          tabTeam.classList.add('active');
          if (select) select.style.display = 'none';
          if (sectionOperations) sectionOperations.style.display = 'block';
          if (sectionUpload) sectionUpload.style.display = 'none';
          updateDashboard();
        } else if (mode === 'personal') {
          tabPersonal.classList.add('active');
          if (select) select.style.display = 'block';
          if (sectionOperations) sectionOperations.style.display = 'block';
          if (sectionUpload) sectionUpload.style.display = 'none';
          updateDashboard();
        } else if (mode === 'upload') {
          if (tabUpload) tabUpload.classList.add('active');
          if (select) select.style.display = 'none';
          if (sectionOperations) sectionOperations.style.display = 'none';
          if (sectionUpload) sectionUpload.style.display = 'block';
        }
      }
    };

    function showSection(id) {
      document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      document.getElementById('section-' + id).classList.add('active');
      const navs = document.querySelectorAll('.nav-item');
      navs.forEach(n => { if (n.getAttribute('onclick') && n.getAttribute('onclick').includes(id)) n.classList.add('active'); });
      if (id === 'objections') { if (!document.getElementById('catTabs').children.length) { renderCatTabs(); renderObjList(); } if (!document.getElementById('svpContainer').children.length) { renderSVP(); renderLaws(); } }
      if (id === 'reglament' && !document.getElementById('criteriaGrid').children.length) { renderCriteria(); }
      if (id === 'operations' && !trendChart) buildCharts();
    }

function getThemeIcon(isLight) {
  if (isLight) {
    return '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4.5"></circle><path d="M12 2.5v2.2"></path><path d="M12 19.3v2.2"></path><path d="M4.9 4.9l1.6 1.6"></path><path d="M17.5 17.5l1.6 1.6"></path><path d="M2.5 12h2.2"></path><path d="M19.3 12h2.2"></path><path d="M4.9 19.1l1.6-1.6"></path><path d="M17.5 6.5l1.6-1.6"></path></svg>';
  }
  return '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M20.8 14.2A8.8 8.8 0 1 1 9.8 3.2a7.2 7.2 0 0 0 11 11z"></path><circle cx="17.2" cy="6.3" r="0.8" fill="currentColor" stroke="none"></circle><circle cx="14.9" cy="4.5" r="0.55" fill="currentColor" stroke="none"></circle></svg>';
}

    function initTheme() {
  const urlParams = new URLSearchParams(window.location.search);
  let theme = urlParams.get('theme');
  if (!theme) theme = localStorage.getItem('sc-theme');
  if (!theme) theme = 'light';

  localStorage.setItem('sc-theme', theme);

  if (theme === 'light') {
    document.body.classList.add('light-mode');
    const btn = document.getElementById('theme-toggle');
    if (btn) btn.innerHTML = getThemeIcon(true);
  } else {
    document.body.classList.remove('light-mode');
    const btn = document.getElementById('theme-toggle');
    if (btn) btn.innerHTML = getThemeIcon(false);
  }

  // Handle Sidebar State
  let sidebarState = urlParams.get('sidebar');
  if (!sidebarState) sidebarState = localStorage.getItem('sc-sidebar');
  if (!sidebarState) sidebarState = 'expanded';

  localStorage.setItem('sc-sidebar', sidebarState);

  const sidebar = document.getElementById('sidebar');
  const main = document.getElementById('main');

  if (sidebar && main) {
    // Freeze transitions so the initial class application is instant (no jitter)
    sidebar.style.transition = 'none';
    main.style.transition = 'none';

    if (sidebarState === 'collapsed') {
      sidebar.classList.add('collapsed');
      main.classList.add('collapsed');
    } else {
      sidebar.classList.remove('collapsed');
      main.classList.remove('collapsed');
    }

    // Restore transitions after the browser has painted the new state
    requestAnimationFrame(function() {
      requestAnimationFrame(function() {
        sidebar.style.transition = '';
        main.style.transition = '';
      });
    });
  }
}

function toggleTheme() {
  const isLight = document.body.classList.toggle('light-mode');
  const theme = isLight ? 'light' : 'dark';
  localStorage.setItem('sc-theme', theme);
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.innerHTML = getThemeIcon(isLight);
  
  const url = new URL(window.location.href);
  url.searchParams.set('theme', theme);
  window.history.replaceState({}, '', url);

  if(typeof updateDashboard === 'function') updateDashboard();
}

    function initFilters() {
      const mSelect = document.getElementById('monthSelect');
      const months = new Set();
      Object.entries(DASHBOARD_DATA).forEach(([name, emp]) => {
        if (name.includes('Промежуточный')) return;
        if (emp?.months) {
          Object.keys(emp.months).forEach(m => {
            months.add(m);
          });
        }
      });
      // Календарная сортировка месяцев (Январь → Декабрь)
      const MONTH_ORDER = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
      const sorted = Array.from(months).sort((a, b) => {
        // Извлекаем название месяца из строки "Май 2026"
        const aMonth = a.split(' ')[0];
        const bMonth = b.split(' ')[0];
        const aIdx = MONTH_ORDER.indexOf(aMonth);
        const bIdx = MONTH_ORDER.indexOf(bMonth);
        // Сортируем по порядку месяцев, затем по году (обратный порядок для года)
        if (aIdx !== bIdx) return aIdx - bIdx;
        const aYear = parseInt(a.split(' ')[1]) || 0;
        const bYear = parseInt(b.split(' ')[1]) || 0;
        return bYear - aYear;
      }).reverse();
      if (!currentMonth && sorted.length) {
        currentMonth = sorted[0];
      } else if (currentMonth && !sorted.includes(currentMonth) && sorted.length) {
        currentMonth = sorted[0];
      }
      if(mSelect) {
          mSelect.innerHTML = '';
          sorted.forEach(m => { const o = document.createElement('option'); o.value = m; o.textContent = m; if (m === currentMonth) o.selected = true; mSelect.appendChild(o); });
          mSelect.onchange = (e) => { 
            currentMonth = e.target.value; 
            localStorage.setItem('current-month', currentMonth);
            currentPeriod = "Все"; 
            currentRatingPeriod = "Все периоды";
            selectedEmployee = null; 
            updatePeriodTabs(); 
            initRatingPeriodSelect();
            updateDashboard(); 
            if (window.FileUploader && typeof window.FileUploader.refreshChecklist === 'function') {
              window.FileUploader.refreshChecklist();
            }
          };
      }
      updatePeriodTabs();
      initRatingPeriodSelect();
    }

    function initHeatmapModeTabs() {
      const tabs = document.getElementById('heatmapModeTabs');
      if (!tabs) return;

      const modes = [
        { id: 'heatmap', label: 'Heatmap' },
        { id: 'pro', label: 'Pro' }
      ];

      tabs.innerHTML = '';
      modes.forEach(mode => {
        const btn = document.createElement('div');
        btn.className = 'cat-tab' + (currentHeatmapMode === mode.id ? ' active' : '');
        btn.textContent = mode.label;
        btn.onclick = () => {
          currentHeatmapMode = mode.id;
          localStorage.setItem('heatmap-mode', mode.id);
          initHeatmapModeTabs();
          renderHeatmapByMode();
        };
        tabs.appendChild(btn);
      });
    }

    function getProDiagnosticByPercent(percent) {
      const isL = isLight();
      if (percent <= 24) {
        return {
          text: 'Несоответствие СВП',
          rank: 6,
          bg: 'rgba(239, 68, 68, 0.22)',
          color: isL ? '#b91c1c' : '#f87171',
          border: 'rgba(239, 68, 68, 0.35)'
        };
      }
      if (percent <= 49) {
        return {
          text: 'Критическая просадка',
          rank: 5,
          bg: 'rgba(239, 68, 68, 0.14)',
          color: isL ? '#dc2626' : '#fca5a5',
          border: 'rgba(239, 68, 68, 0.22)'
        };
      }
      if (percent <= 64) {
        return {
          text: 'Систематическая недоработка',
          rank: 4,
          bg: 'rgba(234, 179, 8, 0.20)',
          color: isL ? '#a16207' : '#facc15',
          border: 'rgba(234, 179, 8, 0.35)'
        };
      }
      if (percent <= 74) {
        return {
          text: 'Недоработка критерия',
          rank: 3,
          bg: 'rgba(234, 179, 8, 0.13)',
          color: isL ? '#ca8a04' : '#fef08a',
          border: 'rgba(234, 179, 8, 0.22)'
        };
      }
      if (percent <= 84) {
        return {
          text: 'Нестабильная отработка',
          rank: 2,
          bg: 'rgba(234, 179, 8, 0.08)',
          color: isL ? '#d97706' : '#fef08a',
          border: 'rgba(234, 179, 8, 0.15)'
        };
      }
      if (percent <= 99) {
        return {
          text: 'Критерий требует внимания',
          rank: 1,
          bg: 'rgba(34, 197, 94, 0.15)',
          color: isL ? '#166534' : '#86efac',
          border: 'rgba(34, 197, 94, 0.25)'
        };
      }
      return {
        text: 'Полное соответствие',
        rank: 0,
        bg: 'rgba(34, 197, 94, 0.22)',
        color: isL ? '#14532d' : '#4ade80',
        border: 'rgba(34, 197, 94, 0.35)'
      };
    }

    function renderHeatmapByMode() {
      if (currentHeatmapMode === 'pro') {
        renderHeatmapPro();
      } else {
        renderHeatmap();
      }
    }

    function updatePeriodTabs() {
      const el = document.getElementById('periodTabs');
      if (!el) return;
      const periods = new Set();
      Object.entries(DASHBOARD_DATA).forEach(([name, emp]) => {
          if(name.includes('Промежуточный')) return;
          const m = emp.months?.[currentMonth];
          if (m && m.periods) {
              m.periods.forEach(p => {
                  if (p.period !== "Все" && p.period !== "Неизвестно") {
                      periods.add(p.period);
                  }
              });
          }
      });
      el.innerHTML = '';
      const allBtn = document.createElement('div'); allBtn.className = 'cat-tab' + (currentPeriod === "Все" ? ' active' : ''); allBtn.textContent = 'Сводка';
      allBtn.onclick = () => { 
        currentPeriod = "Все"; 
        updatePeriodTabs(); 
        updateDashboard(); 
        if (window.FileUploader && typeof window.FileUploader.refreshChecklist === 'function') {
          window.FileUploader.refreshChecklist();
        }
      };
      el.appendChild(allBtn);
      Array.from(periods).sort().forEach(p => { 
        const b = document.createElement('div'); 
        b.className = 'cat-tab' + (currentPeriod === p ? ' active' : ''); 
        b.textContent = p; 
        b.onclick = () => { 
          currentPeriod = p; 
          updatePeriodTabs(); 
          updateDashboard(); 
          if (window.FileUploader && typeof window.FileUploader.refreshChecklist === 'function') {
            window.FileUploader.refreshChecklist();
          }
        }; 
        el.appendChild(b); 
      });
    }

    // Инициализация periodSelect для страницы Rating
    function initRatingPeriodSelect() {
      const pSelect = document.getElementById('periodSelect');
      if (!pSelect) return;
      
      const periods = new Set();
      periods.add('Все периоды');
      
      Object.entries(DASHBOARD_DATA).forEach(([name, emp]) => {
        if (name.includes('Промежуточный')) return;
        const m = emp.months?.[currentMonth];
        if (m && m.periods) {
          m.periods.forEach(p => {
            if (p.period !== "Все" && p.period !== "Неизвестно") {
              periods.add(p.period);
            }
          });
        }
      });
      
      const sortedPeriods = Array.from(periods).sort((a, b) => {
        if (a === 'Все периоды') return -1;
        if (b === 'Все периоды') return 1;
        return a.localeCompare(b);
      });
      
      if (!currentRatingPeriod || currentRatingPeriod === 'Все') {
        currentRatingPeriod = 'Все периоды';
      }
      
      pSelect.innerHTML = '';
      sortedPeriods.forEach(p => {
        const o = document.createElement('option');
        o.value = p;
        o.textContent = p;
        if (p === currentRatingPeriod) o.selected = true;
        pSelect.appendChild(o);
      });
      
      pSelect.onchange = (e) => {
        currentRatingPeriod = e.target.value;
        buildLeaderboard();
        buildTopBottomCharts();
      };
    }

    // ── Вспомогательные функции агрегации ────────────────────────────────────
    function _ahtToSecs(t) {
      if (!t || t === 'N/A') return 0;
      const p = t.split(':');
      if (p.length === 3) {
        return parseInt(p[0] || 0, 10) * 3600 + parseInt(p[1] || 0, 10) * 60 + parseInt(p[2] || 0, 10);
      }
      return parseInt(p[0] || 0, 10) * 60 + parseInt(p[1] || 0, 10);
    }
    function _secsToAht(s) {
      const m = Math.floor(s / 60);
      const sec = s % 60;
      return m.toString().padStart(2, '0') + ':' + sec.toString().padStart(2, '0');
    }
    function _getEffectiveData(empMonthObj) {
      if (!empMonthObj) return null;
      if (currentPeriod === "Все") {
        const allPs = empMonthObj.periods || [];
        if (!allPs.length) return empMonthObj.summary || null;
        
        // Взвешенный расчет TQS по количеству звонков (activity_count)
        const tqsPs = allPs.filter(p => p?.tqs > 0);
        const weightedTqsData = tqsPs.reduce((acc, p) => {
          const cnt = Number(p.activity_count || 1);
          acc.totalTqs += (p.tqs || 0) * cnt;
          acc.totalCalls += cnt;
          return acc;
        }, { totalTqs: 0, totalCalls: 0 });
        const avgTqs = weightedTqsData.totalCalls ? Math.round(weightedTqsData.totalTqs / weightedTqsData.totalCalls * 100) / 100 : 0;
        
        // Взвешенный расчет AHT по количеству звонков
        const ahtPs = allPs.filter(p => p?.aht && p.aht !== 'N/A');
        const weightedAht = ahtPs.reduce((acc, p) => {
          const cnt = Number(p.activity_count || 1);
          acc.totalSecs += _ahtToSecs(p.aht) * cnt;
          acc.totalCalls += cnt;
          return acc;
        }, { totalSecs: 0, totalCalls: 0 });
        const avgSecs = weightedAht.totalCalls ? Math.floor(weightedAht.totalSecs / weightedAht.totalCalls) : 0;

        // Взвешенный расчет SVP по количеству звонков
        const avgSvp = {};
        SVP_KEYS.forEach(k => {
          let validSvpPeriods = allPs.filter(p => p?.svp && p.svp[k] !== undefined);
          if (validSvpPeriods.length > 0) {
            // Взвешенное среднее для каждого критерия SVP
            const weightedSvp = validSvpPeriods.reduce((acc, p) => {
              const cnt = Number(p.activity_count || 1);
              acc.total += p.svp[k] * cnt;
              acc.calls += cnt;
              return acc;
            }, { total: 0, calls: 0 });
            avgSvp[k] = weightedSvp.calls ? Math.round(weightedSvp.total / weightedSvp.calls * 100) / 100 : 1.0;
          } else {
            avgSvp[k] = 1.0;
          }
        });

        const allTend = allPs.map(p => p?.tendencies).filter(t => t && String(t).trim() !== '').join('<br><br>');
        const allRec = allPs.map(p => p?.rec).filter(r => r && String(r).trim() !== '').join('<br><br>');
        return {
          period: "Все",
          tqs: avgTqs,
          aht: _secsToAht(avgSecs),
          activity_count: weightedAht.totalCalls,
          svp: avgSvp,
          tendencies: allTend || 'Нет данных',
          rec: allRec || 'Нет системных рекомендаций'
        };
      }
      return empMonthObj.periods?.find(p => p?.period === currentPeriod) || null;
    }

    function getLocalMetrics(month, period) {
      const metricsList = [];
      
      Object.entries(DASHBOARD_DATA).forEach(([name, emp]) => {
        if (name.includes('Промежуточный')) return;
        const m = emp.months?.[month];
        if (!m) return;
        
        let periodsToAggregate = [];
        if (period === 'Все' || period === 'Все периоды' || !period) {
          const weekly = m.periods?.filter(x => x.period !== 'Все' && x.period !== 'Неизвестно') || [];
          if (weekly.length > 0) {
            periodsToAggregate = weekly;
          } else {
            periodsToAggregate = m.periods?.filter(x => x.period === 'Все') || [];
          }
        } else {
          const p = m.periods?.find(x => x.period === period);
          if (p) periodsToAggregate = [p];
        }
        
        if (periodsToAggregate.length === 0) return;
        
        let totalTqs = 0;
        let totalAhtSec = 0;
        let ahtCount = 0;
        let activityCount = 0;
        let collectedAmount = 0;
        let collectedCount = 0;
        let totalPlanFulfillment = 0;
        let totalCollectionRate = 0;
        
        const crmActions = {};
        let crmActionsSummary = "";
        let crmBehaviorPattern = "balanced";
        let recommendations = "";
        let svpScores = null;
        
        periodsToAggregate.forEach(p => {
          if (p.tqs > 0) {
            totalTqs += p.tqs;
          }
          activityCount += p.activity_count || 0;
          
          const ahtStr = p.aht;
          if (ahtStr && ahtStr !== 'N/A') {
            const parts = ahtStr.split(':');
            if (parts.length === 2) {
              totalAhtSec += parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
              ahtCount++;
            }
          }
          
          collectedAmount += p.collected_amount || 0;
          collectedCount += p.collected_count || 0;
          totalPlanFulfillment += p.plan_fulfillment || 0;
          totalCollectionRate += p.collection_rate || 0;
          
          if (p.crm_actions) {
            Object.entries(p.crm_actions).forEach(([k, v]) => {
              crmActions[k] = (crmActions[k] || 0) + parseInt(v || 0, 10);
            });
          }
          if (p.crm_actions_summary) crmActionsSummary = p.crm_actions_summary;
          if (p.crm_behavior_pattern) crmBehaviorPattern = p.crm_behavior_pattern;
          if (p.rec) recommendations = p.rec;
          if (p.svp) svpScores = p.svp;
        });
        
        const n = periodsToAggregate.length;
        const avgTqs = n > 0 ? totalTqs / n : 0;
        const avgAhtSec = ahtCount > 0 ? totalAhtSec / ahtCount : 0;
        let avgAht = "N/A";
        if (avgAhtSec > 0) {
          const mins = Math.floor(avgAhtSec / 60);
          const secs = Math.round(avgAhtSec % 60);
          avgAht = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        
        const avgPlan = n > 0 ? totalPlanFulfillment / n : 0;
        const avgRate = n > 0 ? totalCollectionRate / n : 0;
        
        const tqsNorm = Math.min(avgTqs, 1.0);
        const rateNorm = Math.min(avgRate / 100.0, 1.0);
        const activityFactor = Math.min(activityCount / 100.0, 1.5);
        const effRatio = Math.round(tqsNorm * rateNorm * activityFactor * 100.0 * 100) / 100;
        
        const created = crmActions.tasks_created || 0;
        const completed = crmActions.tasks_completed || 0;
        const crmConsistency = created === 0 ? (completed > 0 ? 1.0 : 0.0) : Math.round((completed / created) * 100) / 100;
        
        metricsList.push({
          "employee_name": name,
          "tqs": Math.round(avgTqs * 100) / 100,
          "aht": avgAht,
          "activity_count": activityCount,
          "svp_scores": svpScores || {},
          "recommendations": recommendations,
          
          "collected_amount": Math.round(collectedAmount * 100) / 100,
          "collected_count": collectedCount,
          "collection_rate": Math.round(avgRate * 100) / 100,
          "plan_fulfillment": Math.round(avgPlan * 100) / 100,
          
          "crm_actions": crmActions,
          "crm_actions_summary": crmActionsSummary || "Сбалансированная рабочая логика",
          "crm_behavior_pattern": crmBehaviorPattern || "balanced",
          
          "efficiency_ratio": effRatio,
          "crm_consistency_score": crmConsistency
        });
      });
      
      let teamTqs = 0;
      let totalAhtSec = 0;
      let ahtCount = 0;
      let totalCollected = 0;
      let totalRate = 0;
      let totalCrmRate = 0;
      
      metricsList.forEach(m => {
        teamTqs += m.tqs;
        totalCollected += m.collected_amount;
        totalRate += m.collection_rate;
        totalCrmRate += m.crm_consistency_score;
        
        const ahtStr = m.aht;
        if (ahtStr && ahtStr !== 'N/A') {
          const parts = ahtStr.split(':');
          if (parts.length === 2) {
            totalAhtSec += parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
            ahtCount++;
          }
        }
      });
      
      const avgTeamTqs = metricsList.length > 0 ? teamTqs / metricsList.length : 0;
      const avgTeamAhtSec = ahtCount > 0 ? totalAhtSec / ahtCount : 0;
      let avgTeamAht = "N/A";
      if (avgTeamAhtSec > 0) {
        const mins = Math.floor(avgTeamAhtSec / 60);
        const secs = Math.round(avgTeamAhtSec % 60);
        avgTeamAht = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      }
      const avgTeamRate = metricsList.length > 0 ? totalRate / metricsList.length : 0;
      const avgTeamCrmRate = metricsList.length > 0 ? totalCrmRate / metricsList.length : 0;
      
      const teamAverages = {
        "tqs": Math.round(avgTeamTqs * 100) / 100,
        "aht": avgTeamAht,
        "collected_amount": Math.round(totalCollected * 100) / 100,
        "collection_rate": Math.round(avgTeamRate * 100) / 100,
        "crm_completion_rate": Math.round(avgTeamCrmRate * 100) / 100
      };
      
      function calculateJSCorrelation(list, pathX, pathY) {
        function getNested(obj, path) {
          const parts = path.split('.');
          let current = obj;
          for (let part of parts) {
            if (current === null || current === undefined) return 0;
            current = current[part];
          }
          return current || 0;
        }
        
        const xs = list.map(item => getNested(item, pathX));
        const ys = list.map(item => getNested(item, pathY));
        
        const pairs = [];
        for (let i = 0; i < xs.length; i++) {
          if (xs[i] !== 0 || ys[i] !== 0) {
            pairs.push([xs[i], ys[i]]);
          }
        }
        
        if (pairs.length < 3) return 0.0;
        
        const filteredXs = pairs.map(p => p[0]);
        const filteredYs = pairs.map(p => p[1]);
        
        const meanX = filteredXs.reduce((a, b) => a + b, 0) / filteredXs.length;
        const meanY = filteredYs.reduce((a, b) => a + b, 0) / filteredYs.length;
        
        let cov = 0;
        let varX = 0;
        let varY = 0;
        
        for (let i = 0; i < pairs.length; i++) {
          const dx = filteredXs[i] - meanX;
          const dy = filteredYs[i] - meanY;
          cov += dx * dy;
          varX += dx * dx;
          varY += dy * dy;
        }
        
        if (varX === 0 || varY === 0) return 0.0;
        return Math.round((cov / Math.sqrt(varX * varY)) * 100) / 100;
      }
      
      const corrMetricsList = metricsList.map(m => {
        let ahtSec = 0;
        if (m.aht && m.aht !== 'N/A') {
          const parts = m.aht.split(':');
          if (parts.length === 2) {
            ahtSec = parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
          }
        }
        return { ...m, aht_numeric: ahtSec };
      });
      
      const correlations = {
        "tqs_vs_collections": calculateJSCorrelation(metricsList, "tqs", "collected_amount"),
        "crm_promised_vs_collections": calculateJSCorrelation(metricsList, "crm_actions.promised_to_pay", "collected_amount"),
        "aht_vs_collection_rate": calculateJSCorrelation(corrMetricsList, "aht_numeric", "collection_rate")
      };
      
      return {
        "period": period === "Все" ? month : `${month} - ${period}`,
        "team_averages": teamAverages,
        "correlations": correlations,
        "data": metricsList
      };
    }

    function renderKPIs(data) {
      const averages = data.team_averages || {};
      
      const titleTqs = document.getElementById('title-tqs');
      const titleAht = document.getElementById('title-aht');
      const titleRisk = document.getElementById('title-risk');
      const titleCollected = document.getElementById('title-collected');
      const titleCrm = document.getElementById('title-crm');
      const titleMainChart = document.getElementById('title-main-chart');
      
      let tqsValText = '-';
      let tqsBadgeHtml = '-';
      let ahtValText = '-';
      let riskValText = '-';
      let collectedValText = '-';
      let collectionRateHtml = '-';
      let crmCountValText = '-';
      let dominantActionText = '-';
      
      if (currentViewMode === 'team' || !selectedEmployee) {
        // TEAM MODE
        if (titleTqs) titleTqs.textContent = 'Командный TQS';
        if (titleAht) titleAht.textContent = 'Средний AHT';
        if (titleRisk) titleRisk.textContent = 'Приоритет «0»';
        if (titleCollected) titleCollected.innerHTML = `${SVG_ICONS.money}<span>Сборы команды</span>`;
        if (titleCrm) titleCrm.innerHTML = `${SVG_ICONS.activity}<span>CRM-активность команды</span>`;
        if (titleMainChart) titleMainChart.textContent = 'Progress Wave — Сравнение качества (TQS) и Сборов команды';
        
        tqsValText = averages.tqs ? (averages.tqs * 100).toFixed(1) + '%' : '-';
        tqsBadgeHtml = averages.tqs >= 0.75 ? 
          `${SVG_ICONS.target} Цель достигнута` : `${SVG_ICONS.warning} Ниже цели`;
        
        ahtValText = averages.aht || '-';
        
        let riskCount = 0;
        if (data.data) {
          data.data.forEach(op => {
            if (op.svp_scores) {
              const hasZeroSvp = Object.values(op.svp_scores).some(v => v === 0);
              if (hasZeroSvp) riskCount++;
            }
          });
        }
        riskValText = riskCount;
        
        const colVal = averages.collected_amount || 0;
        collectedValText = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'UZS', maximumFractionDigits: 0 }).format(colVal);
        
        const rate = averages.collection_rate || 0;
        collectionRateHtml = `${rate.toFixed(1)}%`;
        
        let totalActions = 0;
        if (data.data) {
          data.data.forEach(op => {
            if (op.crm_actions) {
              Object.entries(op.crm_actions).forEach(([k, v]) => {
                if (k !== 'tasks_created' && k !== 'tasks_completed' && k !== 'tasks_rolled_back' && k !== 'other') {
                  totalActions += v;
                }
              });
            }
          });
        }
        crmCountValText = totalActions;
        
        const patterns = {};
        if (data.data) {
          data.data.forEach(op => {
            const p = op.crm_behavior_pattern || 'balanced';
            patterns[p] = (patterns[p] || 0) + 1;
          });
        }
        let dominant = 'balanced';
        let maxCount = 0;
        Object.entries(patterns).forEach(([p, count]) => {
          if (count > maxCount) {
            maxCount = count;
            dominant = p;
          }
        });
        const patternLabels = {
          'negotiator': 'Лидер',
          'passive': 'Пассивный',
          'avoidant': 'Избегающий',
          'balanced': 'Норма'
        };
        dominantActionText = patternLabels[dominant] || 'Норма';
      } else {
        // PERSONAL MODE
        const op = data.data ? data.data.find(x => x.employee_name === selectedEmployee) : null;
        const shortName = shortN(selectedEmployee);
        
        if (titleTqs) titleTqs.textContent = `${shortName} - TQS`;
        if (titleAht) titleAht.textContent = `${shortName} - AHT`;
        if (titleRisk) titleRisk.textContent = `${shortName} - SVP`;
        if (titleCollected) titleCollected.innerHTML = `${SVG_ICONS.money}<span>Сборы: ${shortName}</span>`;
        if (titleCrm) titleCrm.innerHTML = `${SVG_ICONS.activity}<span>CRM: ${shortName}</span>`;
        if (titleMainChart) titleMainChart.textContent = `Progress Wave — Сравнение TQS и Сборов: ${shortName}`;
        
        if (op) {
          tqsValText = (op.tqs * 100).toFixed(1) + '%';
          tqsBadgeHtml = op.tqs >= 0.75 ? 
            `${SVG_ICONS.target} Цель достигнута` : `${SVG_ICONS.warning} Ниже цели`;
          
          ahtValText = op.aht || 'N/A';
          
          let criticalErrorsCount = 0;
          if (op.svp_scores) {
            criticalErrorsCount = Object.values(op.svp_scores).filter(v => v === 0).length;
          }
          riskValText = criticalErrorsCount === 0 ? 'В норме' : `${criticalErrorsCount} кр. ош.`;
          
          const colVal = op.collected_amount || 0;
          collectedValText = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'UZS', maximumFractionDigits: 0 }).format(colVal);
          
          collectionRateHtml = `${Math.round(op.plan_fulfillment || 0)}%`;
          
          let opActions = 0;
          if (op.crm_actions) {
            Object.entries(op.crm_actions).forEach(([k, v]) => {
              if (k !== 'tasks_created' && k !== 'tasks_completed' && k !== 'tasks_rolled_back' && k !== 'other') {
                opActions += v;
              }
            });
          }
          crmCountValText = opActions;
          
          const patternLabels = {
            'negotiator': 'Лидер',
            'passive': 'Пассивный',
            'avoidant': 'Избегающий',
            'balanced': 'Норма'
          };
          dominantActionText = patternLabels[op.crm_behavior_pattern] || 'Норма';
        }
      }
      
      const kpiTqs = document.getElementById('kpi-tqs');
      if (kpiTqs) kpiTqs.textContent = tqsValText;
      const badgeTqs = document.getElementById('badge-tqs');
      if (badgeTqs) {
        badgeTqs.innerHTML = tqsBadgeHtml;
        if (tqsBadgeHtml.includes('Цель достигнута')) {
          badgeTqs.style.background = 'rgba(34,197,94,0.15)';
          badgeTqs.style.color = '#4ade80';
        } else if (tqsBadgeHtml !== '-') {
          badgeTqs.style.background = 'rgba(239,68,68,0.15)';
          badgeTqs.style.color = '#f87171';
        } else {
          badgeTqs.style.background = 'none';
          badgeTqs.style.color = '#94a3b8';
        }
      }
      
      const kpiAht = document.getElementById('kpi-aht');
      if (kpiAht) kpiAht.textContent = ahtValText;
      
      const kpiRisk = document.getElementById('kpi-risk');
      if (kpiRisk) {
        kpiRisk.textContent = riskValText;
        if (riskValText === 'В норме' || riskValText === 0) {
          kpiRisk.style.color = '#4ade80';
        } else if (riskValText !== '-') {
          kpiRisk.style.color = '#f87171';
        }
      }
      
      const totalCollectedEl = document.getElementById('total-collected');
      if (totalCollectedEl) totalCollectedEl.textContent = collectedValText;
      
      const collectionRateEl = document.getElementById('collection-rate');
      if (collectionRateEl) {
        collectionRateEl.textContent = collectionRateHtml;
        const rateVal = parseFloat(collectionRateHtml);
        if (isNaN(rateVal)) {
          collectionRateEl.style.background = 'rgba(255,255,255,0.05)';
          collectionRateEl.style.color = '#94a3b8';
        } else if (rateVal >= 80) {
          collectionRateEl.style.background = 'rgba(34,197,94,0.15)';
          collectionRateEl.style.color = '#4ade80';
        } else if (rateVal >= 50) {
          collectionRateEl.style.background = 'rgba(234,179,8,0.15)';
          collectionRateEl.style.color = '#facc15';
        } else {
          collectionRateEl.style.background = 'rgba(239,68,68,0.15)';
          collectionRateEl.style.color = '#f87171';
        }
      }
      
      const crmCountEl = document.getElementById('crm-actions-count');
      if (crmCountEl) crmCountEl.textContent = crmCountValText;
      
      const dominantActionEl = document.getElementById('dominant-action');
      if (dominantActionEl) dominantActionEl.textContent = dominantActionText;
    }

    function updateEmployeeSelect(dataPayload) {
      const select = document.getElementById('employeeSelect');
      if (!select) return;
      
      const prevVal = select.value || selectedEmployee;
      select.innerHTML = '';
      
      const list = (dataPayload.data || []).filter(op => !op.employee_name.includes('Промежуточный'));
      list.forEach(op => {
        const opt = document.createElement('option');
        opt.value = op.employee_name;
        opt.textContent = op.employee_name;
        select.appendChild(opt);
      });
      
      if (list.length === 0) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'Нет сотрудников';
        select.appendChild(opt);
      }
      
      if (prevVal && list.some(x => x.employee_name === prevVal)) {
        select.value = prevVal;
        selectedEmployee = prevVal;
      } else if (list.length > 0) {
        select.value = list[0].employee_name;
        selectedEmployee = list[0].employee_name;
      }
      
      // КРИТИЧЕСКИ ВАЖНО: привязать onchange для обновления всех графиков
      select.onchange = function() {
        selectedEmployee = this.value;
        updateDashboard();
      };
    }

    async function updateDashboard() {
      try {
        let dataPayload = null;
        try {
          const response = await fetch(`/api/metrics?month=${encodeURIComponent(currentMonth)}&period=${encodeURIComponent(currentPeriod)}`);
          if (response.ok) {
            dataPayload = await response.json();
            console.log('[QC Dashboard] Loaded data via API');
          }
        } catch (e) {
          console.warn('[QC Dashboard] API fetch failed, falling back to local computation:', e);
        }
        
        if (!dataPayload) {
          dataPayload = getLocalMetrics(currentMonth, currentPeriod);
          console.log('[QC Dashboard] Loaded data via local fallback');
        }
        
        if (dataPayload && dataPayload.data) {
          dataPayload.data = dataPayload.data.filter(op => isValidEmployeeName(op.employee_name));
        }
        
        window.CURRENT_METRICS_DATA = dataPayload;
        
        updateEmployeeSelect(dataPayload);
        renderKPIs(dataPayload);
        
        // Обновить подзаголовок с текущим периодом
        const subtitleEl = document.getElementById('page-subtitle');
        if (subtitleEl) {
          subtitleEl.textContent = 'Динамика команды Soft Collection \u00b7 ' + currentMonth + (currentPeriod && currentPeriod !== 'Все' && currentPeriod !== 'Все периоды' ? ' \u00b7 ' + currentPeriod : '');
        }
        renderHeatmapByMode();
        buildLineChart();
        buildCharts();
        buildCorrelationCharts();
        buildGrowthTable();
        
        if (currentViewMode === 'personal' && selectedEmployee) {
          showEmployee(selectedEmployee);
        } else {
          const el = document.getElementById('drilldownContent');
          if (el) {
            el.innerHTML = `<div style="color:#64748b;text-align:center;padding:40px 0;">Выберите оператора в таблице или на тепловой карте для детализации</div>`;
          }
        }
        
        if (document.getElementById('forecast-tqs') || document.getElementById('lineChart')) {
          runForecastUpdate();
        }
      } catch (e) {
        console.error('[updateDashboard failed]', e);
      }
    }

    // ========== 2b. FORECAST MATH ORCHESTRATOR ==========

    function runForecastUpdate() {
      const timeline = [];
      const MONTH_SORT = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
      const monthSet = new Set();
      Object.values(DASHBOARD_DATA).forEach(emp => {
        if (emp.months) Object.keys(emp.months).forEach(m => monthSet.add(m));
      });
      const monthOrder = [...monthSet].sort((a, b) => {
        const ai = MONTH_SORT.findIndex(x => a.includes(x));
        const bi = MONTH_SORT.findIndex(x => b.includes(x));
        return ai - bi;
      });
      
      monthOrder.forEach(mName => {
        const pNamesSet = new Set();
        Object.values(DASHBOARD_DATA).forEach(emp => {
          if (emp.months?.[mName]?.periods) {
            emp.months[mName].periods.forEach(p => pNamesSet.add(p.period));
          }
        });
        
        const sortedPeriods = [...pNamesSet].sort();
        sortedPeriods.forEach(pName => {
          let sum = 0, count = 0;
          Object.values(DASHBOARD_DATA).forEach(emp => {
            const m = emp.months?.[mName];
            if (m?.periods) {
              const p = m.periods.find(x => x.period === pName);
              if (p && p.tqs > 0) {
                sum += p.tqs;
                count++;
              }
            }
          });
          if (count > 0) {
            timeline.push({ label: `${mName.split(' ')[0]} ${pName}`, value: sum / count });
          }
        });
      });

      if (timeline.length < 2) return;

      const dataValues = timeline.map(t => t.value);
      const forecastCount = 3;
      const forecastResult = calculateHolt(dataValues, 0.4, 0.3, forecastCount);
      
      if (document.getElementById('forecast-tqs')) {
          const nextVal = forecastResult.forecast[0];
          document.getElementById('forecast-tqs').textContent = (nextVal * 100).toFixed(1) + '%';
          
          const aiEl = document.getElementById('forecast-ai');
          const lastValid = dataValues[dataValues.length - 1];
          const diff = nextVal - lastValid;
          
          if (diff > 0.01) {
            aiEl.textContent = 'Умеренный рост (TQS ↑)'; aiEl.style.color = '#22c55e';
          } else if (diff < -0.01) {
            aiEl.textContent = 'Риск просадки (TQS ↓)'; aiEl.style.color = '#ef4444';
          } else {
            aiEl.textContent = 'Стабильный тренд'; aiEl.style.color = '#facc15';
          }
      }

      const canvas = document.getElementById('lineChart');
      if (canvas && (window.location.pathname.includes('forecast') || document.title.includes('Прогнозирование'))) {
         buildAreaForecastChart(timeline, forecastResult);
      }
    }

    function calculateHolt(data, alpha, beta, n) {
      let level = data[0];
      let trend = data[1] - data[0];
      const fits = [level];
      
      for (let i = 1; i < data.length; i++) {
        let lastLevel = level;
        level = alpha * data[i] + (1 - alpha) * (level + trend);
        trend = beta * (level - lastLevel) + (1 - beta) * trend;
        fits.push(level + trend);
      }
      
      const forecast = [];
      for (let i = 1; i <= n; i++) {
        forecast.push(level + i * trend);
      }

      let ssRes = 0, ssTot = 0;
      const mean = data.reduce((a, b) => a + b, 0) / data.length;
      for (let i = 0; i < data.length; i++) {
        ssRes += Math.pow(data[i] - fits[i], 2);
        ssTot += Math.pow(data[i] - mean, 2);
      }
      const r2 = 1 - (ssRes / (ssTot || 1));
      
      return { fits, forecast, r2: Math.max(0, r2) };
    }

    let forecastChartInstance = null;

    function buildAreaForecastChart(history, results) {
      const canvas = document.getElementById('lineChart');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (forecastChartInstance) forecastChartInstance.destroy();

      const labels = [...history.map(h => h.label)];
      for (let i = 1; i <= results.forecast.length; i++) labels.push(`Прогноз +${i}`);

      const historyData = history.map(h => h.value * 100);
      const forecastData = Array(history.length - 1).fill(null);
      forecastData.push(historyData[historyData.length - 1]);
      results.forecast.forEach(f => forecastData.push(f * 100));

      const grad = ctx.createLinearGradient(0, 0, 0, 400);
      grad.addColorStop(0, 'rgba(129, 140, 248, 0.4)');
      grad.addColorStop(1, 'rgba(129, 140, 248, 0)');

      forecastChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Исторические данные (Факт)',
              data: historyData,
              borderColor: '#818cf8',
              backgroundColor: grad,
              fill: true,
              borderWidth: 4,
              pointBackgroundColor: '#818cf8',
              pointBorderColor: '#fff',
              pointBorderWidth: 2,
              pointRadius: 6,
              pointHoverRadius: 8,
              tension: 0.4
            },
            {
              label: 'Прогноз (Double Exp Smoothing)',
              data: forecastData,
              borderColor: '#f97316',
              borderDash: [6, 4],
              borderWidth: 3,
              pointBackgroundColor: '#fff',
              pointBorderColor: '#f97316',
              pointBorderWidth: 3,
              pointRadius: 6,
              fill: false,
              tension: 0.3
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { position: 'top', labels: { color: thmC('#94a3b8', '#3f3f46'), font: { weight: '600', size: 12 }, padding: 20 } },
            tooltip: {
              backgroundColor: thmC('rgba(15, 23, 42, 0.95)', '#ffffff'),
              titleColor: thmC('#f1f5f9', '#27272a'),
              bodyColor: thmC('#cbd5e1', '#27272a'),
              padding: 12,
              cornerRadius: 8,
              callbacks: {
                label: (ctx) => {
                  const type = ctx.datasetIndex === 0 ? ' Факт: ' : ' Прогноз: ';
                  return type + ctx.parsed.y.toFixed(1) + '%';
                },
                afterFooter: () => `Accuracy (R²): ${(results.r2 * 100).toFixed(1)}%`
              }
            }
          },
          scales: {
            x: { grid: { display: false }, ticks: { color: thmC('#64748b', '#3f3f46'), font: { size: 11 } } },
            y: { min: Math.max(0, Math.min.apply(null, historyData.filter(function(v) { return v > 0; })) - 10), max: 100, grid: { color: thmC('rgba(255,255,255,0.05)', 'rgba(0,0,0,0.03)'), lineWidth: thmC(1, 0.5) }, ticks: { color: thmC('#64748b', '#3f3f46'), font: { size: 11 } } }
          }
        },
        plugins: [{
          afterDraw: chart => {
            const ctx = chart.ctx;
            ctx.save();
            ctx.fillStyle = 'rgba(148, 163, 184, 0.5)';
            ctx.font = 'bold 11px Inter';
            ctx.textAlign = 'right';
            ctx.fillText(`R² = ${results.r2.toFixed(3)}`, chart.width - 25, 45);
            ctx.restore();
          }
        }]
      });
    }

    function getSmartTooltip(periods) {
      if (!periods || !periods.length) return { text: "Нет данных", rank: -1, bg: '#64748b' };
      let worstRank = -1;
      let worstText = "В норме";
      let worstBg = '#22c55e';
      SVP_KEYS.forEach(k => {
        let diag = getDiagnosticForCriterion(periods, k);
        if (diag.rank > worstRank) {
          worstRank = diag.rank;
          worstText = diag.text;
          worstBg = diag.bg;
        }
      });
      return { text: worstText, rank: worstRank, bg: worstBg };
    }

    function renderHeatmap() {
      try {
      const el = document.getElementById('heatmapContainer');
      if (!el) return;
      el.innerHTML = '';

      let html = '<div style="display:flex;gap:2px;margin-bottom:8px;font-size:9px;color:#64748b;"><div style="width:160px">ОПЕРАТОР</div>';
      SVP_KEYS.forEach(s => html += `<div style="flex:1;text-align:center">${s.substring(0, 3)}</div>`);
      html += '</div>';
      Object.keys(DASHBOARD_DATA).sort().forEach(name => {
        if (name.includes('Промежуточный')) return;
        const m = DASHBOARD_DATA[name]?.months?.[currentMonth]; if (!m) return;
        const d = _getEffectiveData(m);
        if (!d || !d.svp) return;

        const periodsToAnalyze = currentPeriod === "Все" ? (m.periods || []) : [d];

        let border = name === selectedEmployee ? 'border:1px solid #a78bfa;background:rgba(167,139,250,0.1);' : '';
        html += `<div style="display:flex;gap:2px;margin-bottom:2px;cursor:pointer;padding:2px;border-radius:4px;${border}" onclick="selectEmployee('${name.replace(/'/g, "\\'")}')">`;
        html += `<div style="width:160px;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${name}</div>`;
        SVP_KEYS.forEach(st => {
          const v = (d.svp[st] !== undefined) ? d.svp[st] : 1;
          let bg = v >= 1 ? '#22c55e' : (v >= 0.5 ? '#eab308' : '#ef4444');
          
          const diag = getDiagnosticForCriterion(periodsToAnalyze, st);
          let textInfo = st + ':\n' + diag.text;
          
          html += `<div class="hm-tooltip" style="flex:1;"><div style="background:${bg};height:14px;opacity:0.65;border-radius:2px;"></div><div class="tt" style="white-space:pre-wrap;text-align:center;">${textInfo}</div></div>`;
        });
        html += '</div>';
      });
      el.innerHTML = html || '<div style="color:#64748b;padding:12px">Нет данных за этот период</div>';
      } catch (e) {
        console.error('[renderHeatmap failed]', e);
      }
    }

    function renderHeatmapPro() {
      try {
      const el = document.getElementById('heatmapContainer');
      if (!el) return;
      el.innerHTML = '';

      const viewport = window.innerWidth || 1280;
      const isNarrow = viewport < 1100;
      const isVeryNarrow = viewport < 900;
      const operatorWidth = isVeryNarrow ? 170 : (isNarrow ? 180 : 190);
      const scoreWidth = isVeryNarrow ? 124 : (isNarrow ? 136 : 150);
      const cellMinWidth = isVeryNarrow ? 52 : (isNarrow ? 56 : 58);
      const cellHeight = isVeryNarrow ? 24 : 28;
      const headerFont = isVeryNarrow ? 9 : 10;
      const nameFont = isVeryNarrow ? 11 : 12;
      const percentFont = isVeryNarrow ? 10 : 11;
      const scoreFont = isVeryNarrow ? 11 : 12;
      const rowPadding = isVeryNarrow ? 5 : 6;
      const colGap = isVeryNarrow ? 3 : 4;
      const minTableWidth = operatorWidth + scoreWidth + (SVP_KEYS.length * cellMinWidth) + (SVP_KEYS.length + 2) * colGap + 60;

      const legendCategories = [
        { range: '0-24%', val: 10, label: 'Несоответствие' },
        { range: '25-49%', val: 35, label: 'Критическая просадка' },
        { range: '50-64%', val: 55, label: 'Систематическая недоработка' },
        { range: '65-74%', val: 70, label: 'Недоработка' },
        { range: '75-84%', val: 80, label: 'Нестабильная отработка' },
        { range: '85-99%', val: 90, label: 'Требует внимания' },
        { range: '100%', val: 100, label: 'Полное соответствие' }
      ];

      let html = '<div class="pro-heatmap-legend">';
      html += '<div class="pro-heatmap-legend-title">Pro-диагноз по процентной шкале (7 уровней)</div>';
      html += '<div style="display:flex;flex-wrap:wrap;gap:7px;">';
      legendCategories.forEach(item => {
        const diag = getProDiagnosticByPercent(item.val);
        html += `<span style="font-size:10px;border-radius:7px;padding:5px 8px;background:${diag.bg};color:${diag.color};border:1px solid ${diag.border};">${item.range}: ${item.label}</span>`;
      });
      html += '</div></div>';

      html += `<div style="overflow-x:auto;padding-bottom:2px;"><div style="min-width:${minTableWidth}px;">`;
      html += `<div style="display:flex;gap:${colGap}px;margin-bottom:10px;font-size:${headerFont}px;font-weight:700;color:#94a3b8;letter-spacing:0.3px;"><div style="width:${operatorWidth}px">ОПЕРАТОР</div>`;
      SVP_KEYS.forEach(s => html += `<div style="flex:1;min-width:${cellMinWidth}px;text-align:center">${s.substring(0, 3)}</div>`);
      html += `<div style="width:${scoreWidth}px;text-align:center">Pro-score</div></div>`;

      const isL = isLight();

      Object.keys(DASHBOARD_DATA).sort().forEach(name => {
        if (name.includes('Промежуточный')) return;
        const m = DASHBOARD_DATA[name]?.months?.[currentMonth];
        if (!m) return;
        const d = _getEffectiveData(m);
        if (!d || !d.svp) return;

        let rankSum = 0;
        let criteriaCount = 0;
        const rowClass = 'pro-heatmap-row' + (name === selectedEmployee ? ' selected' : '');

        html += `<div class="${rowClass}" style="gap:${colGap}px;padding:${rowPadding}px;border-radius:8px;transition:all .15s ease;" onclick="selectEmployee('${name.replace(/'/g, "\\'")}')">`;
        html += `<div class="pro-heatmap-name" style="width:${operatorWidth}px;font-size:${nameFont}px;line-height:${cellHeight}px;">${name}</div>`;

        SVP_KEYS.forEach(st => {
          const v = d.svp[st] !== undefined ? d.svp[st] : 1;
          const percent = Math.round(v * 100);
          const diag = getProDiagnosticByPercent(percent);
          rankSum += diag.rank;
          criteriaCount++;
          html += `<div class="hm-tooltip" style="flex:1;min-width:${cellMinWidth}px;"><div class="pro-heatmap-cell" style="background:${diag.bg};border:1px solid ${diag.border};color:${diag.color};font-size:${percentFont}px;height:${cellHeight}px;">${percent}%</div><div class="tt" style="white-space:pre-wrap;text-align:center;">${st}: ${percent}%\n${diag.text}</div></div>`;
        });

        const proScore = criteriaCount ? ((rankSum / (criteriaCount * 6)) * 100) : 0;
        let scoreColor, scoreBg, scoreBorder;
        if (proScore >= 65) {
          scoreColor = isL ? '#dc2626' : '#f87171';
          scoreBg = isL ? 'rgba(220,38,38,0.12)' : 'rgba(239,68,68,0.20)';
          scoreBorder = isL ? 'rgba(220,38,38,0.22)' : 'rgba(239,68,68,0.35)';
        } else if (proScore >= 40) {
          scoreColor = isL ? '#c2410c' : '#fb923c';
          scoreBg = isL ? 'rgba(194,65,12,0.12)' : 'rgba(249,115,22,0.16)';
          scoreBorder = isL ? 'rgba(194,65,12,0.22)' : 'rgba(249,115,22,0.30)';
        } else if (proScore >= 20) {
          scoreColor = isL ? '#b45309' : '#facc15';
          scoreBg = isL ? 'rgba(234,179,8,0.12)' : 'rgba(234,179,8,0.16)';
          scoreBorder = isL ? 'rgba(234,179,8,0.22)' : 'rgba(234,179,8,0.30)';
        } else {
          scoreColor = isL ? '#14532d' : '#4ade80';
          scoreBg = isL ? 'rgba(34, 197, 94, 0.12)' : 'rgba(34, 197, 94, 0.20)';
          scoreBorder = isL ? 'rgba(34, 197, 94, 0.22)' : 'rgba(34, 197, 94, 0.35)';
        }
        html += `<div style="width:${scoreWidth}px;display:flex;align-items:center;justify-content:center;"><span style="font-size:${scoreFont}px;font-weight:700;color:${scoreColor};background:${scoreBg};border:1px solid ${scoreBorder};border-radius:8px;padding:${isVeryNarrow ? 5 : 6}px ${isVeryNarrow ? 8 : 10}px;min-width:${isVeryNarrow ? 74 : 82}px;text-align:center;box-sizing:border-box;">${proScore.toFixed(1)}%</span></div>`;
        html += '</div>';
      });

      html += '</div></div>';
      el.innerHTML = html || '<div style="color:#64748b;padding:12px">Нет данных за этот период</div>';
      } catch (e) {
        console.error('[renderHeatmapPro failed]', e);
      }
    }

    let drillPieChart = null;
    let drillTrendChart = null;
    let drillCRMDoughnutChart = null;

    function generateOperatorInsights(op) {
      const insights = [];
      const tqs = (op.tqs || 0) * 100;
      const plan = op.plan_fulfillment || 0;
      
      if (tqs >= 85 && plan < 60) {
        insights.push({
          type: 'warning',
          text: '<strong>Качество vs Деньги:</strong> Высокое качество разговора (TQS ' + tqs.toFixed(0) + '%) не дает сборов (план ' + plan.toFixed(0) + '%). Возможен формальный проход по скрипту. Требуется нажим на этапе Требования.'
        });
      } else if (tqs < 70 && plan >= 90) {
        insights.push({
          type: 'success',
          text: '<strong>Качество vs Деньги:</strong> Отличные сборы (' + plan.toFixed(0) + '%) при низком TQS (' + tqs.toFixed(0) + '%). Оцените риски жалоб. Подтяните речевые стандарты.'
        });
      } else if (tqs >= 85 && plan >= 90) {
        insights.push({
          type: 'success',
          text: '<strong>Идеальный баланс:</strong> Оператор отлично сочетает следование регламентам СВП и финансовую результативность.'
        });
      } else if (tqs < 70 && plan < 60) {
        insights.push({
          type: 'danger',
          text: '<strong>Критическая зона:</strong> Провал по качеству переговоров и сборам. Назначьте индивидуальное прослушивание.'
        });
      }
      
      const created = op.crm_actions?.tasks_created || 0;
      const completed = op.crm_actions?.tasks_completed || 0;
      const completionRate = created > 0 ? completed / created : 0;
      
      if (created > 0 && completionRate < 0.6) {
        insights.push({
          type: 'danger',
          text: '<strong>Дисциплина CRM:</strong> Низкая результативность контактов (' + (completionRate * 100).toFixed(0) + '%). Много тишины/сбросов.'
        });
      }
      
      if (op.crm_behavior_pattern === 'avoidant') {
        insights.push({
          type: 'info',
          text: '<strong>CRM-паттерн "Избегающий":</strong> Высокая доля сбросов или молчания. Отработайте работу со сложными отказами.'
        });
      } else if (op.crm_behavior_pattern === 'passive') {
        insights.push({
          type: 'info',
          text: '<strong>CRM-паттерн "Пассивный":</strong> Согласие с аргументами должника. Отработайте ст. 333 ГК РУз при финансовых возражениях.'
        });
      } else if (op.crm_behavior_pattern === 'negotiator') {
        insights.push({
          type: 'success',
          text: '<strong>CRM-паттерн "Переговорщик":</strong> Стабильно берет обещания (PTP). Контролируйте их фактическую оплату.'
        });
      }
      
      return insights.length ? insights : [{ type: 'info', text: 'Показатели в пределах нормы. Продолжайте мониторинг.' }];
    }

    function selectEmployee(name) {
      selectedEmployee = name;
      const select = document.getElementById('employeeSelect');
      if (select) select.value = name;
      
      if (currentViewMode !== 'personal') {
        currentViewMode = 'personal';
        localStorage.setItem('view-mode', 'personal');
        const tabTeam = document.getElementById('tab-view-team');
        const tabPersonal = document.getElementById('tab-view-personal');
        if (tabTeam && tabPersonal) {
          tabTeam.classList.remove('active');
          tabPersonal.classList.add('active');
        }
        if (select) select.style.display = 'block';
      }
      updateDashboard();
    }

    function showEmployee(name) {
      try {
        selectedEmployee = name;
        
        const select = document.getElementById('employeeSelect');
        if (select) select.value = name;

        const list = window.CURRENT_METRICS_DATA ? window.CURRENT_METRICS_DATA.data : [];
        const op = list.find(x => x.employee_name === name);
        const el = document.getElementById('drilldownContent');
        if (!el) return;
        if (!op) {
          el.innerHTML = `<h4 style="color:#a78bfa;margin-bottom:12px">${name}</h4><p style="color:#64748b">Нет данных за выбранный период</p>`;
          return;
        }

        // Зоны роста из SVP данных текущего периода
        let growthHtml = '';
        if (op.svp_scores) {
          const problems = Object.entries(op.svp_scores).filter(([k, v]) => v < 1);
          if (problems.length) {
            growthHtml = '<p style="margin-top:10px;font-size:11px;"><strong>Зоны роста:</strong><br>';
            growthHtml += problems.map(([k, v]) => {
              const cls = v <= 0.25 ? 'badge-red' : 'badge-yellow';
              return `<span class="kpi-badge ${cls}" style="margin:2px 2px 0 0">${k}: ${Math.round(v * 100)}%</span>`;
            }).join('');
            growthHtml += '</p>';
          }
        }

        const insights = generateOperatorInsights(op);
        const insightsHtml = insights.map(ins => {
          let color = '#38bdf8';
          let bg = 'rgba(56,189,248,0.08)';
          let icon = SVG_ICONS.info;
          if (ins.type === 'success') {
            color = '#4ade80';
            bg = 'rgba(34,197,94,0.08)';
            icon = SVG_ICONS.success;
          } else if (ins.type === 'warning') {
            color = '#facc15';
            bg = 'rgba(234,179,8,0.08)';
            icon = SVG_ICONS.warning;
          } else if (ins.type === 'danger') {
            color = '#f87171';
            bg = 'rgba(239,68,68,0.08)';
            icon = SVG_ICONS.danger;
          }
          return `<li style="list-style:none;padding:8px 10px;margin-bottom:6px;border-radius:6px;background:${bg};border-left:3px solid ${color};color:#cbd5e1;display:flex;gap:8px;align-items:start;"><span style="display:inline-flex;color:${color};line-height:1;margin-top:2px;">${icon}</span><span style="font-size:10.5px;">${ins.text}</span></li>`;
        }).join('');

        // Calculate behavior spikes relative to team averages
        const keysToAnalyze = ['promised_to_pay', 'refused_payment', 'thinking', 'declared_payment', 'hung_up', 'refused_conversation', 'silence'];
        const keyLabels = {
          promised_to_pay: 'Обещание платежа',
          refused_payment: 'Отказ от оплаты',
          thinking: 'Думает',
          declared_payment: 'Заявленный платеж',
          hung_up: 'Бросил трубку',
          refused_conversation: 'Отказ от разговора',
          silence: 'Тишина'
        };
        const psychologicalInterpretations = {
          promised_to_pay: 'высокая убедительность, стабильное закрытие звонков на фиксацию обещания.',
          refused_payment: 'агрессивные интонации, провоцирующие клиента на жесткий отказ, или слабая отработка возражений.',
          thinking: 'неуверенность при закрытии сделки, зависание в аргументации, нерешительность.',
          declared_payment: 'высокая результативность побуждения к действию, сильное дожимание.',
          hung_up: 'избегание конфликтов, психологическая перегрузка или преждевременный сброс звонка.',
          refused_conversation: 'неумение преодолевать первичный барьер, слабый/неубедительный вход в контакт.',
          silence: 'растерянность, отсутствие инициативы, длительные неловкие паузы в диалоге.'
        };

        const teamKeyCounts = {
          promised_to_pay: 0, refused_payment: 0, thinking: 0, declared_payment: 0, hung_up: 0, refused_conversation: 0, silence: 0
        };
        let teamTotal = 0;
        list.forEach(item => {
          if (item.crm_actions) {
            keysToAnalyze.forEach(k => {
              const v = item.crm_actions[k] || 0;
              teamKeyCounts[k] += v;
              teamTotal += v;
            });
          }
        });

        const teamShares = {};
        keysToAnalyze.forEach(k => {
          teamShares[k] = teamTotal > 0 ? (teamKeyCounts[k] / teamTotal) : 0;
        });

        const opCrm = op.crm_actions || {};
        let opTotal = 0;
        keysToAnalyze.forEach(k => {
          opTotal += opCrm[k] || 0;
        });

        const opShares = {};
        keysToAnalyze.forEach(k => {
          opShares[k] = opTotal > 0 ? ((opCrm[k] || 0) / opTotal) : 0;
        });

        const spikes = [];
        keysToAnalyze.forEach(k => {
          const opShare = opShares[k];
          const teamShare = teamShares[k];
          if (teamShare > 0 && opShare >= 0.05) {
            const ratio = opShare / teamShare;
            if (ratio >= 1.5) {
              spikes.push({
                key: k,
                label: keyLabels[k],
                ratio: ratio,
                opPct: opShare * 100,
                teamPct: teamShare * 100
              });
            }
          }
        });

        let spikesHtml = '';
        if (spikes.length > 0) {
          spikesHtml = '<div style="margin-top:12px;border-top:1px solid rgba(251,146,60,0.15);padding-top:10px;">';
          spikesHtml += '<div style="font-size:10px;color:#fb923c;font-weight:700;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;display:flex;align-items:center;gap:4px;">' + SVG_ICONS.warning + ' Выявленные всплески поведения:</div>';
          spikesHtml += '<ul style="margin:0;padding:0;list-style:none;">';
          spikes.forEach(s => {
            const interpretation = psychologicalInterpretations[s.key] || '';
            spikesHtml += `
              <li style="font-size:10.5px;color:#cbd5e1;margin-bottom:6px;background:rgba(234,179,8,0.06);border-left:2px solid #eab308;padding:4px 8px;border-radius:0 4px 4px 0;">
                <strong>${s.label}</strong> в <strong>${s.ratio.toFixed(1)}x</strong> чаще нормы по команде (${s.opPct.toFixed(0)}% vs ср. ${s.teamPct.toFixed(0)}%).<br>
                <span style="color:#94a3b8;font-style:italic;">Интерпретация: ${interpretation}</span>
              </li>`;
          });
          spikesHtml += '</ul></div>';
        } else {
          spikesHtml = '<div style="margin-top:12px;border-top:1px solid rgba(251,146,60,0.15);padding-top:10px;font-size:10.5px;color:#94a3b8;font-style:italic;text-align:center;">' +
                       'Всплески и аномалии поведения не обнаружены (в пределах нормы по команде).</div>';
        }

        const patternLabelsWithSVGs = {
          'negotiator': `<span style="display:inline-flex;align-items:center;gap:4px;color:#4ade80;">${SVG_ICONS.target} Лидер</span>`,
          'passive': `<span style="display:inline-flex;align-items:center;gap:4px;color:#cbd5e1;">${SVG_ICONS.info} Пассивный</span>`,
          'avoidant': `<span style="display:inline-flex;align-items:center;gap:4px;color:#f87171;">${SVG_ICONS.warning} Избегающий</span>`,
          'balanced': `<span style="display:inline-flex;align-items:center;gap:4px;color:#4ade80;">${SVG_ICONS.success} Норма</span>`
        };

        // Fallback tendencies и recommendations из DASHBOARD_DATA
        let tendencies = op.tendencies || op.recommendations || '';
        if (!tendencies && DASHBOARD_DATA[name]) {
          const empMonthData = DASHBOARD_DATA[name]?.months?.[currentMonth];
          if (empMonthData) {
            const pd = _getEffectiveData(empMonthData);
            if (pd) {
              tendencies = pd.tendencies || pd.rec || '';
            }
          }
        }
        
        let recommendations = op.recommendations || '';
        if (!recommendations && DASHBOARD_DATA[name]) {
          const empMonthData = DASHBOARD_DATA[name]?.months?.[currentMonth];
          if (empMonthData) {
            const pd = _getEffectiveData(empMonthData);
            if (pd) {
              recommendations = pd.recommendations || pd.rec || '';
            }
          }
        }

        el.innerHTML = `
          <h4 style="color:#f97316;margin-bottom:12px;font-weight:800;text-align:center;">${name}</h4>
          
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">
            <div class="card" style="padding:10px;text-align:center;"><small style="color:#94a3b8;">TQS</small><br><strong style="font-size:16px;color:#a78bfa;">${(op.tqs * 100).toFixed(1)}%</strong></div>
            <div class="card" style="padding:10px;text-align:center;"><small style="color:#94a3b8;">AHT</small><br><strong style="font-size:16px;color:#4ade80;">${op.aht || 'N/A'}</strong></div>
          </div>
          
          <div class="card" style="padding:12px;margin-bottom:12px;text-align:left;border:1px solid rgba(56,189,248,0.2);background:rgba(56,189,248,0.02);box-shadow:none;">
            <h5 style="color:#38bdf8;margin:0 0 8px 0;font-size:12px;font-weight:700;display:flex;align-items:center;gap:6px;">${SVG_ICONS.money} Финансовая эффективность</h5>
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;margin-bottom:6px;">
              <span style="color:#94a3b8;">Собрано:</span>
              <strong style="color:#e2e8f0;margin-left:auto;">${new Intl.NumberFormat('ru-RU', {style: 'currency', currency: 'UZS', maximumFractionDigits: 0}).format(op.collected_amount || 0)}</strong>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;margin-bottom:6px;">
              <span style="color:#94a3b8;">Выполнение плана:</span>
              <span style="color:#e2e8f0;margin-left:auto;font-weight:700;">${Math.round(op.plan_fulfillment || 0)}%</span>
            </div>
            <div style="margin-bottom:8px;background:rgba(255,255,255,0.05);height:6px;border-radius:3px;overflow:hidden;">
              <div style="background:#38bdf8;width:${Math.min(100, Math.max(0, op.plan_fulfillment || 0))}%;height:100%;border-radius:3px;transition:width 0.3s ease;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;">
              <span style="color:#94a3b8;">Средний чек:</span>
              <strong style="color:#e2e8f0;margin-left:auto;">${new Intl.NumberFormat('ru-RU', {style: 'currency', currency: 'UZS', maximumFractionDigits: 0}).format((op.collected_amount && op.collected_count) ? Math.round(op.collected_amount / op.collected_count) : 0)}</strong>
            </div>
          </div>
          
          <div class="card" style="padding:12px;margin-bottom:12px;text-align:left;border:1px solid rgba(251,146,60,0.2);background:rgba(251,146,60,0.02);box-shadow:none;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;gap:6px;">
              <h5 style="color:#fb923c;margin:0;font-size:12px;font-weight:700;display:flex;align-items:center;gap:6px;">${SVG_ICONS.activity} CRM-поведение</h5>
              <span class="kpi-badge" style="margin:0;font-size:9px;padding:2px 6px;border-radius:4px;font-weight:800;text-transform:uppercase;background:rgba(251,146,60,0.15);color:#fb923c;border:1px solid rgba(251,146,60,0.3);display:inline-flex;align-items:center;height:18px;">
                ${patternLabelsWithSVGs[op.crm_behavior_pattern] || '❓ Не определено'}
              </span>
            </div>
            <p style="font-size:11px;color:#cbd5e1;line-height:1.4;margin:0 0 10px 0;font-style:italic;">${op.crm_actions_summary || 'Нет данных'}</p>
            <div style="font-size:10px;color:#94a3b8;margin-bottom:4px;font-weight:600;">Типы CRM действий:</div>
            <div style="height:120px;position:relative;width:100%;margin-bottom:8px;"><canvas id="drillCRMDoughnut"></canvas></div>
            ${spikesHtml}
          </div>
          
          <div class="card" style="padding:12px;margin-bottom:12px;text-align:left;border:1px solid rgba(167,139,250,0.2);background:rgba(167,139,250,0.02);box-shadow:none;">
            <h5 style="color:#a78bfa;margin:0 0 8px 0;font-size:12px;font-weight:700;display:flex;align-items:center;gap:6px;">${SVG_ICONS.brain} Стратегический коучинг</h5>
            <ul style="margin:0;padding:0;" id="op-strategy-insights">
              ${insightsHtml}
            </ul>
          </div>
          
          <div class="card" style="padding:12px;text-align:left;box-shadow:none;">
            <h5 style="color:#e2e8f0;margin:0 0 8px 0;font-size:12px;font-weight:700;display:flex;align-items:center;gap:6px;">${SVG_ICONS.trend} Анализ качества переговоров</h5>
            <p style="font-size:11px;margin:0 0 6px 0;"><strong>Тенденции:</strong><br><span style="color:#cbd5e1;">${tendencies || 'Нет данных'}</span></p>
            <p style="font-size:11px;margin:0 0 10px 0;"><strong>Рекомендации QC:</strong><br><span style="color:#cbd5e1;">${recommendations || 'Нет данных'}</span></p>
            ${growthHtml}
            
            <div style="font-size:10px;color:#94a3b8;margin-top:14px;margin-bottom:4px;font-weight:600;">Просадки по критериям:</div>
            <div style="height:120px;position:relative;width:100%;margin-bottom:12px;"><canvas id="drillPie"></canvas></div>
            
            <div style="font-size:10px;color:#94a3b8;margin-bottom:4px;font-weight:600;">Динамика TQS за месяц:</div>
            <div style="height:130px;position:relative;width:100%;"><canvas id="drillTrend"></canvas></div>
          </div>
        `;
        
        // Render Charts for Drilldown
        if (drillPieChart) drillPieChart.destroy();
        if (drillTrendChart) drillTrendChart.destroy();
        if (drillCRMDoughnutChart) drillCRMDoughnutChart.destroy();

        // 1. SVP Error Chart
        if (op.svp_scores) {
          let pieLabels = [];
          let pieData = [];
          let pieColors = [];
          SVP_KEYS.forEach(k => {
            if(op.svp_scores[k] !== undefined && op.svp_scores[k] < 1) {
              pieLabels.push(k.substring(0,25));
              pieData.push(1 - op.svp_scores[k]);
              pieColors.push(op.svp_scores[k] <= 0.25 ? '#ef4444' : '#eab308');
            }
          });
          
          if(pieData.length > 0) {
            const ctxPie = document.getElementById('drillPie').getContext('2d');
            drillPieChart = new Chart(ctxPie, {
              type: 'doughnut',
              data: { labels: pieLabels, datasets: [{ data: pieData, backgroundColor: pieColors, borderWidth: 1, borderColor: '#1e2435' }] },
              options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { backgroundColor: thmC('#1e2435', '#ffffff'), titleColor: thmC('#f1f5f9', '#27272a'), bodyColor: thmC('#94a3b8', '#27272a') } }, cutout: '70%'}
            });
          } else {
            document.getElementById('drillPie').parentElement.innerHTML = `<div style="color:#22c55e;font-size:12px;padding:20px;text-align:center;display:flex;align-items:center;justify-content:center;gap:4px;">Ошибок СВП нет <span style="display:inline-flex;color:#22c55e;line-height:1;">${SVG_ICONS.success}</span></div>`;
          }
        }

        // 2. CRM Actions Chart
        const crm = op.crm_actions || {};
        const crmKeys = ['promised_to_pay', 'refused_payment', 'thinking', 'declared_payment', 'hung_up', 'refused_conversation', 'silence'];
        const crmLabels = ['Обещание платежа', 'Отказ от оплаты', 'Думает', 'Заявленный платеж', 'Бросил трубку', 'Отказ от разговора', 'Тишина'];
        const crmColors = ['#22c55e', '#ef4444', '#facc15', '#06b6d4', '#ea580c', '#ec4899', '#94a3b8'];
        const crmData = crmKeys.map(k => crm[k] || 0);
        
        const totalCRM = crmData.reduce((a, b) => a + b, 0);
        if (totalCRM > 0) {
          const ctxCRM = document.getElementById('drillCRMDoughnut').getContext('2d');
          drillCRMDoughnutChart = new Chart(ctxCRM, {
            type: 'doughnut',
            data: {
              labels: crmLabels,
              datasets: [{
                data: crmData,
                backgroundColor: crmColors,
                borderWidth: 1,
                borderColor: '#1e2435'
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: {
                  backgroundColor: thmC('#1e2435', '#ffffff'),
                  titleColor: thmC('#f1f5f9', '#27272a'),
                  bodyColor: thmC('#94a3b8', '#27272a'),
                  callbacks: {
                    label: c => c.label + ': ' + c.parsed + ' (' + ((c.parsed / totalCRM) * 100).toFixed(0) + '%)'
                  }
                }
              },
              cutout: '70%'
            }
          });
        } else {
          document.getElementById('drillCRMDoughnut').parentElement.innerHTML = '<div style="color:#64748b;font-size:12px;padding:20px;text-align:center;">Нет данных CRM за этот период</div>';
        }

        // 3. Operator TQS Monthly Dynamics Chart
        const empData = DASHBOARD_DATA[name];
        if (empData && empData.months && empData.months[currentMonth]) {
          const mAll = empData.months[currentMonth];
          if (mAll && mAll.periods) {
            const trendLabels = mAll.periods.map(p => p.period);
            const trendData = mAll.periods.map(p => p.tqs * 100);
            const ctxTrend = document.getElementById('drillTrend').getContext('2d');
            drillTrendChart = new Chart(ctxTrend, {
              type: 'line',
              data: { labels: trendLabels, datasets: [{ label: 'TQS %', data: trendData, borderColor: '#f97316', backgroundColor: '#f9731622', fill: true, tension: 0.4, pointRadius: 3 }] },
              options: { responsive: true, maintainAspectRatio: false, layout: { padding: { left: 8, right: 8, top: 8, bottom: 8 } }, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { min: 30, max: 100, ticks: { color: thmC('#64748b', '#3f3f46'), font: {size: 9} } } } }
            });
          }
        }
        
        renderHeatmapByMode();
      } catch (e) {
        console.error('[showEmployee failed]', e);
        const el = document.getElementById('drilldownContent');
        if (el) el.innerHTML = '<p style="color:#ef4444;padding:20px;">Ошибка загрузки данных сотрудника</p>';
      }
    }


    let lineChartInstance = null;
    let scatterChartInstance = null;
    let crmBarChartInstance = null;
    const LINE_COLORS = ['#a78bfa', '#4ade80', '#f87171', '#facc15', '#60a5fa', '#fb923c', '#34d399', '#e879f9', '#94a3b8', '#ffba08', '#818cf8', '#f472b6', '#2dd4bf', '#fbbf24', '#c084fc', '#22d3ee', '#fb7185', '#a3e635', '#e2e8f0', '#f97316'];

    function shortN(name) {
      const p = name.split(' ');
      return p.length > 1 ? `${p[0]} ${p[1][0]}.` : name;
    }

    function buildLineChart() {
      const canvas = document.getElementById('lineChart');
      if (!canvas) return;
      if (window.location.pathname.includes('forecast') || document.title.includes('Прогнозирование')) return;
      
      const ctx = canvas.getContext('2d');
      if (lineChartInstance) lineChartInstance.destroy();
      
      let periods = [];
      const avgTqs = [];
      const totalCollections = [];
      
      if (currentViewMode === 'team' || !selectedEmployee) {
        // TEAM MODE
        const periodsSet = new Set();
        Object.entries(DASHBOARD_DATA).forEach(([name, emp]) => {
          if (name.includes('Промежуточный')) return;
          const m = emp.months?.[currentMonth];
          if (m && m.periods) {
            m.periods.forEach(p => {
              if (p.period !== "Все" && p.period !== "Неизвестно") {
                periodsSet.add(p.period);
              }
            });
          }
        });
        
        periods = Array.from(periodsSet).sort();
        if (!periods.length) {
          // Fallback if no weekly periods exist
          Object.entries(DASHBOARD_DATA).forEach(([name, emp]) => {
            if (name.includes('Промежуточный')) return;
            const m = emp.months?.[currentMonth];
            if (m && m.periods) {
              m.periods.forEach(p => periodsSet.add(p.period));
            }
          });
          periods = Array.from(periodsSet).sort();
        }
        if (!periods.length) return;

        // Filter periods up to selected period
        if (currentPeriod !== "Все" && currentPeriod !== "Все периоды" && currentPeriod !== "Неизвестно") {
          const idx = periods.indexOf(currentPeriod);
          if (idx !== -1) {
            periods = periods.slice(0, idx + 1);
          }
        }
        
        periods.forEach(p => {
          let tqsSum = 0;
          let tqsCalls = 0;
          let tqsCount = 0;
          let collectionsSum = 0;
          
          Object.entries(DASHBOARD_DATA).forEach(([name, emp]) => {
            if (name.includes('Промежуточный')) return;
            const m = emp.months?.[currentMonth];
            if (!m || !m.periods) return;
            const entry = m.periods.find(x => x.period === p);
            if (!entry) return;
            
            if (entry.tqs > 0) {
              const calls = Number(entry.activity_count || 1);
              tqsSum += entry.tqs * calls;
              tqsCalls += calls;
              tqsCount++;
            }
            collectionsSum += entry.collected_amount || 0;
          });
          
          const avgTqsVal = tqsCalls ? tqsSum / tqsCalls : (tqsCount ? tqsSum / tqsCount : 0);
          avgTqs.push(Math.round(avgTqsVal * 100 * 10) / 10);
          totalCollections.push(collectionsSum);
        });
      } else {
        // PERSONAL MODE
        const emp = DASHBOARD_DATA[selectedEmployee];
        if (!emp || !emp.months) return;
        const m = emp.months[currentMonth];
        if (!m || !m.periods) return;
        
        let sortedPeriods = m.periods.slice()
          .filter(p => p.period !== "Все" && p.period !== "Неизвестно")
          .sort((a, b) => a.period.localeCompare(b.period));
        
        if (currentPeriod !== "Все" && currentPeriod !== "Все периоды" && currentPeriod !== "Неизвестно") {
          const idx = sortedPeriods.findIndex(p => p.period === currentPeriod);
          if (idx !== -1) {
            sortedPeriods = sortedPeriods.slice(0, idx + 1);
          }
        }
        
        periods = sortedPeriods.map(p => p.period);
        sortedPeriods.forEach(p => {
          avgTqs.push(Math.round((p.tqs || 0) * 100 * 10) / 10);
          totalCollections.push(p.collected_amount || 0);
        });
      }
      
      if (!periods.length) return;
      
      lineChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: periods,
          datasets: [
            {
              label: currentViewMode === 'team' ? 'Командный TQS (%)' : 'Личный TQS (%)',
              data: avgTqs,
              borderColor: '#a78bfa',
              backgroundColor: 'rgba(167, 139, 250, 0.15)',
              borderWidth: 3,
              pointRadius: ctx => {
                const label = ctx.chart.data.labels[ctx.dataIndex];
                return label === currentPeriod ? 9 : 5;
              },
              pointHoverRadius: ctx => {
                const label = ctx.chart.data.labels[ctx.dataIndex];
                return label === currentPeriod ? 11 : 7;
              },
              pointBackgroundColor: ctx => {
                const label = ctx.chart.data.labels[ctx.dataIndex];
                return label === currentPeriod ? '#ffffff' : '#a78bfa';
              },
              pointBorderColor: ctx => {
                const label = ctx.chart.data.labels[ctx.dataIndex];
                return label === currentPeriod ? '#a78bfa' : undefined;
              },
              pointBorderWidth: ctx => {
                const label = ctx.chart.data.labels[ctx.dataIndex];
                return label === currentPeriod ? 3 : 1;
              },
              tension: 0.4,
              yAxisID: 'y'
            },
            {
              label: currentViewMode === 'team' ? 'Сборы команды (UZS)' : 'Личные сборы (UZS)',
              data: totalCollections,
              borderColor: '#38bdf8',
              backgroundColor: 'rgba(56, 189, 248, 0.15)',
              borderWidth: 3,
              pointRadius: ctx => {
                const label = ctx.chart.data.labels[ctx.dataIndex];
                return label === currentPeriod ? 9 : 5;
              },
              pointHoverRadius: ctx => {
                const label = ctx.chart.data.labels[ctx.dataIndex];
                return label === currentPeriod ? 11 : 7;
              },
              pointBackgroundColor: ctx => {
                const label = ctx.chart.data.labels[ctx.dataIndex];
                return label === currentPeriod ? '#ffffff' : '#38bdf8';
              },
              pointBorderColor: ctx => {
                const label = ctx.chart.data.labels[ctx.dataIndex];
                return label === currentPeriod ? '#38bdf8' : undefined;
              },
              pointBorderWidth: ctx => {
                const label = ctx.chart.data.labels[ctx.dataIndex];
                return label === currentPeriod ? 3 : 1;
              },
              tension: 0.4,
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          layout: {
            padding: {
              left: 8,
              right: 8,
              top: 8,
              bottom: 8
            }
          },
          plugins: {
            legend: { labels: { color: thmC('#94a3b8', '#3f3f46'), font: { size: 11 } } },
            tooltip: {
              backgroundColor: thmC('#1e2435', '#ffffff'),
              borderColor: thmC('#2d3748', '#e4e4e7'),
              borderWidth: 1,
              titleColor: thmC('#f1f5f9', '#27272a'),
              bodyColor: thmC('#94a3b8', '#27272a'),
              callbacks: {
                label: c => {
                  if (c.datasetIndex === 0) {
                    return c.dataset.label + ': ' + c.parsed.y.toFixed(1) + '%';
                  }
                  return c.dataset.label + ': ' + new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'UZS', maximumFractionDigits: 0 }).format(c.parsed.y);
                }
              }
            }
          },
          scales: {
            x: {
              grid: { color: thmC('#1e2435', 'rgba(0,0,0,0.03)'), lineWidth: thmC(1, 0.5) },
              ticks: { color: thmC('#64748b', '#3f3f46'), font: { size: 10 } }
            },
            y: {
              type: 'linear',
              position: 'left',
              min: 30,
              max: 100,
              grid: { color: thmC('#232b3e', 'rgba(0,0,0,0.03)'), lineWidth: thmC(1, 0.5) },
              ticks: {
                color: thmC('#64748b', '#3f3f46'),
                font: { size: 10 },
                callback: v => v + '%'
              },
              title: { display: true, text: 'Качество (TQS)', color: thmC('#94a3b8', '#3f3f46') }
            },
            y1: {
              type: 'linear',
              position: 'right',
              grid: { drawOnChartArea: false },
              ticks: {
                color: thmC('#64748b', '#3f3f46'),
                font: { size: 10 },
                callback: v => new Intl.NumberFormat('ru-RU', { notation: 'compact', compactDisplay: 'short' }).format(v)
              },
              title: { display: true, text: 'Сборы (UZS)', color: thmC('#94a3b8', '#3f3f46') }
            }
          }
        }
      });
    }
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
            y: { min: 0, max: 100, grid: { color: thmC('#232b3e', 'rgba(0,0,0,0.03)'), lineWidth: thmC(1, 0.5) }, ticks: { color: thmC('#64748b', '#3f3f46'), callback: function(v) { return v + '%'; } } },
            x: { grid: { display: false }, ticks: { color: thmC('#64748b', '#3f3f46'), font: { size: 10 }, maxRotation: 45 } }
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: thmC('#1e2435', '#ffffff'),
              borderColor: thmC('#2d3748', '#e4e4e7'),
              borderWidth: 1,
              titleColor: thmC('#f1f5f9', '#27272a'),
              bodyColor: thmC('#94a3b8', '#27272a'),
              callbacks: { label: function(c) { return c.parsed.y > 0 ? 'TQS: ' + c.parsed.y + '%' : 'Нет данных TQS'; } }
            }
          }
        }
      });
    }

    function buildCorrelationCharts() {
      const scatterEl = document.getElementById('tqs-collections-scatter');
      const barEl = document.getElementById('crm-conversion-bar');
      
      const metrics = window.CURRENT_METRICS_DATA || { data: [], correlations: {} };
      const list = metrics.data || [];
      
      // 1. Scatter Chart
      if (scatterEl) {
        const ctx = scatterEl.getContext('2d');
        if (scatterChartInstance) scatterChartInstance.destroy();
        
        const patternColors = {
          'negotiator': 'rgba(34, 197, 94, 0.85)',
          'passive': 'rgba(239, 68, 68, 0.85)',
          'avoidant': 'rgba(234, 179, 8, 0.85)',
          'balanced': 'rgba(59, 130, 246, 0.85)'
        };
        const patternBorders = {
          'negotiator': '#22c55e',
          'passive': '#ef4444',
          'avoidant': '#eab308',
          'balanced': '#3b82f6'
        };
        
        const scatterData = list.map(op => ({
          x: Math.round((op.tqs || 0) * 100 * 10) / 10,
          y: op.collected_amount || 0,
          name: op.employee_name,
          pattern: op.crm_behavior_pattern || 'balanced',
          isSelected: currentViewMode === 'personal' && selectedEmployee === op.employee_name
        }));
        
        scatterChartInstance = new Chart(ctx, {
          type: 'scatter',
          data: {
            datasets: [{
              label: 'Операторы',
              data: scatterData,
              backgroundColor: ctx => {
                const item = ctx.raw;
                return item ? patternColors[item.pattern] : 'rgba(59, 130, 246, 0.85)';
              },
              borderColor: ctx => {
                const item = ctx.raw;
                return item ? patternBorders[item.pattern] : '#3b82f6';
              },
              borderWidth: ctx => {
                const item = ctx.raw;
                return item && item.isSelected ? 3 : 1.5;
              },
              pointRadius: ctx => {
                const item = ctx.raw;
                return item && item.isSelected ? 12 : 6;
              },
              pointHoverRadius: ctx => {
                const item = ctx.raw;
                return item && item.isSelected ? 14 : 8;
              }
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                backgroundColor: thmC('#1e2435', '#ffffff'),
                borderColor: thmC('#2d3748', '#e4e4e7'),
                borderWidth: 1,
                titleColor: thmC('#f1f5f9', '#27272a'),
                bodyColor: thmC('#94a3b8', '#27272a'),
                callbacks: {
                  label: c => {
                    const item = c.raw;
                    const patterns = { negotiator: 'Переговорщик', passive: 'Пассивный', avoidant: 'Избегающий', balanced: 'Сбалансированный' };
                    return [
                      `Сотрудник: ${item.name}`,
                      `TQS: ${item.x}%`,
                      `Сборы: ${new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'UZS', maximumFractionDigits: 0 }).format(item.y)}`,
                      `Паттерн: ${patterns[item.pattern]}`
                    ];
                  }
                }
              }
            },
            scales: {
              x: {
                min: 30,
                max: 100,
                grid: { color: thmC('#232b3e', 'rgba(0,0,0,0.03)'), lineWidth: thmC(1, 0.5) },
                ticks: { color: thmC('#64748b', '#3f3f46'), font: { size: 10 }, callback: v => v + '%' },
                title: { display: true, text: 'Качество разговора (TQS)', color: thmC('#94a3b8', '#3f3f46') }
              },
              y: {
                grid: { color: thmC('#232b3e', 'rgba(0,0,0,0.03)'), lineWidth: thmC(1, 0.5) },
                ticks: {
                  color: thmC('#64748b', '#3f3f46'),
                  font: { size: 10 },
                  callback: v => new Intl.NumberFormat('ru-RU', { notation: 'compact', compactDisplay: 'short' }).format(v)
                },
                title: { display: true, text: 'Сумма сбора (UZS)', color: thmC('#94a3b8', '#3f3f46') }
              }
            }
          }
        });
        
        const insightEl = document.getElementById('tqs-collections-insight');
        if (insightEl) {
          const r = metrics.correlations?.tqs_vs_collections || 0;
          let strength = 'слабая';
          let dir = 'отсутствует';
          if (Math.abs(r) > 0.6) strength = 'сильная';
          else if (Math.abs(r) > 0.3) strength = 'умеренная';
          
          if (r > 0.1) dir = 'положительная (чем выше TQS, тем выше сборы)';
          else if (r < -0.1) dir = 'отрицательная (рост TQS снижает сборы)';
          else dir = 'отсутствует (TQS не влияет на сборы)';
          
          insightEl.innerHTML = `<strong>Коэффициент корреляции Пирсона r = ${r.toFixed(2)}</strong> (${strength} ${dir})`;
        }
      }
      
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
          const legendContainer = document.getElementById('crm-legend-container');
          if (legendContainer) legendContainer.innerHTML = '';
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
              legend: { display: false },
              tooltip: {
                backgroundColor: thmC('#1e2435', '#ffffff'),
                borderColor: thmC('#2d3748', '#e4e4e7'),
                borderWidth: 1,
                titleColor: thmC('#f1f5f9', '#27272a'),
                bodyColor: thmC('#94a3b8', '#27272a'),
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

        // Отрисовка красивой кастомной легенды
        const legendContainer = document.getElementById('crm-legend-container');
        if (legendContainer) {
          legendContainer.innerHTML = filtered.map(f => {
            const pct = total > 0 ? ((f.value / total) * 100).toFixed(1) : '0.0';
            return `
              <div class="crm-legend-item" style="display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:11px;padding:6px 10px;border-radius:6px;background:${thmC('rgba(30,41,59,0.2)', 'rgba(249,115,22,0.03)')};border:1px solid ${thmC('rgba(255,255,255,0.05)', 'rgba(249,115,22,0.08)')};">
                <div style="display:flex;align-items:center;gap:8px;flex:1;min-width:0;">
                  <span style="width:8px;height:8px;border-radius:50%;background-color:${f.color};flex-shrink:0;display:inline-block;box-shadow:0 0 6px ${f.color}55;"></span>
                  <span style="font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:${thmC('#e2e8f0', '#27272a')}">${f.label}</span>
                </div>
                <span style="font-family:monospace;font-weight:700;color:${thmC('#94a3b8', '#3f3f46')}">${f.value} <span style="font-weight:500;font-size:10px;color:${thmC('#64748b', '#71717a')}">(${pct}%)</span></span>
              </div>
            `;
          }).join('');
        }
      }
    }

    function buildGrowthTable() {
      const tbody = document.getElementById('growthTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';

      const empProblems = [];
      Object.keys(DASHBOARD_DATA).forEach(name => {
        if(name.includes('Промежуточный')) return;
        const m = DASHBOARD_DATA[name]?.months?.[currentMonth]; if (!m) return;
        const d = _getEffectiveData(m);
        if (!d || !d.svp) return;

        const periodsToAnalyze = currentPeriod === "Все" ? (m.periods || []) : [d];
        const rankInfo = getSmartTooltip(periodsToAnalyze);

        let critList = [];
        SVP_KEYS.forEach(k => {
          let v = d.svp[k];
          if (v !== undefined && v < 1) {
            let diag = getDiagnosticForCriterion(periodsToAnalyze, k);
            critList.push({ name: k, val: v, diag: diag });
          }
        });

        if (critList.length > 0) {
          critList.sort((a, b) => {
            if (a.val !== b.val) return a.val - b.val;
            return b.diag.rank - a.diag.rank;
          });
          
          let critHtml = '';
          let statHtml = '';
          critList.forEach(c => {
            let cls = c.val <= 0.25 ? 'badge-red' : 'badge-yellow';
            critHtml += `<div style="height:24px;display:flex;align-items:center;margin-bottom:6px;"><span class="kpi-badge ${cls}" style="margin:0">${c.name} (${Math.round(c.val * 100)}%)</span></div>`;
            statHtml += `<div style="height:24px;display:flex;align-items:center;margin-bottom:6px;font-size:11px;font-weight:600;color:${c.diag.bg};">${c.diag.text}</div>`;
          });

          empProblems.push({
            name: name,
            tqs: d.tqs,
            rank: rankInfo.rank,
            critHtml: critHtml,
            statHtml: statHtml,
            rec: d.rec || 'Нет системных рекомендаций'
          });
        }
      });

      empProblems.sort((a, b) => b.rank - a.rank || a.tqs - b.tqs);

      let html = '';
      empProblems.forEach(ep => {
        html += `<tr style="cursor:pointer;border-bottom:1px solid rgba(255,255,255,0.05);" onclick="selectEmployee('${ep.name.replace(/'/g, "\\'")}')">
          <td style="font-weight:600;vertical-align:top;padding-top:14px;">${ep.name}</td>
          <td style="vertical-align:top;padding-top:14px;">${ep.tqs !== undefined && ep.tqs !== null ? (ep.tqs * 100).toFixed(1) + '%' : '—'}</td>
          <td style="vertical-align:top;padding-top:14px;">${ep.critHtml}</td>
          <td style="vertical-align:top;padding-top:14px;">${ep.statHtml}</td>
          <td style="font-size:11px;color:${thmC('#94a3b8', '#3f3f46')};line-height:1.5;white-space:pre-wrap;vertical-align:top;padding:14px 12px 14px 0;">${ep.rec}</td>
        </tr>`;
      });
      tbody.innerHTML = html || '<tr><td colspan="5" style="text-align:center;color:#64748b;padding:20px;">Нет зон роста (все показатели 100%)</td></tr>';
    }

    function buildLeaderboard() {
      const tbody = document.getElementById('leaderboardBody');
      if (!tbody) return;

      const empDataList = [];
      const monthKeys = Object.keys(DASHBOARD_DATA).map(name => DASHBOARD_DATA[name]?.months ? Object.keys(DASHBOARD_DATA[name].months) : []).flat();
      const uniqueMonths = [...new Set(monthKeys)].sort((a, b) => {
        const MONTH_ORDER = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
        const aMonth = a.split(' ')[0];
        const bMonth = b.split(' ')[0];
        const aIdx = MONTH_ORDER.indexOf(aMonth);
        const bIdx = MONTH_ORDER.indexOf(bMonth);
        if (aIdx !== bIdx) return aIdx - bIdx;
        const aYear = parseInt(a.split(' ')[1]) || 0;
        const bYear = parseInt(b.split(' ')[1]) || 0;
        return aYear - bYear;
      });
      
      const currentMonthIdx = uniqueMonths.indexOf(currentMonth);
      const prevMonth = currentMonthIdx > 0 ? uniqueMonths[currentMonthIdx - 1] : null;

      Object.keys(DASHBOARD_DATA).forEach(name => {
        if(name.includes('Промежуточный')) return;
        const m = DASHBOARD_DATA[name]?.months?.[currentMonth]; 
        if (!m) return;
        
        // Определяем данные для текущего периода
        let currentData = null;
        if (currentRatingPeriod === 'Все периоды') {
          currentData = _getEffectiveData(m);
        } else {
          currentData = m.periods?.find(p => p.period === currentRatingPeriod);
        }
        
        if (!currentData || currentData.tqs === undefined) return;

        // Расчет Δ TQS (динамика vs предыдущий период)
        let trend = 0;
        if (currentRatingPeriod === 'Все периоды') {
          // Сравнение с предыдущим месяцем (последний период текущего vs последний период предыдущего)
          if (prevMonth) {
            const prevM = DASHBOARD_DATA[name]?.months?.[prevMonth];
            if (prevM && prevM.periods && prevM.periods.length > 0) {
              const lastPrev = prevM.periods[prevM.periods.length - 1];
              const lastCurrent = m.periods && m.periods.length > 0 ? m.periods[m.periods.length - 1] : null;
              if (lastCurrent && lastPrev) {
                trend = lastCurrent.tqs - lastPrev.tqs;
              }
            }
          }
        } else {
          // Сравнение с предыдущим периодом внутри месяца
          if (m.periods && m.periods.length >= 2) {
            const currentIdx = m.periods.findIndex(p => p.period === currentRatingPeriod);
            if (currentIdx > 0) {
              const prev = m.periods[currentIdx - 1];
              trend = currentData.tqs - prev.tqs;
            }
          }
        }

        // Расчет TQS период (значение за текущий период)
        const periodTqs = currentData.tqs * 100;

        // Расчет Динамика периода (то же что и trend, но для отдельного столбца)
        const periodTrend = trend * 100;

        // Расчет Средний TQS за последние 3 периода
        let avgTqs3 = 0;
        if (currentRatingPeriod === 'Все периоды') {
          // Средний по месяцам (текущий + 2 предыдущих)
          const monthsToAvg = [currentMonth];
          if (currentMonthIdx > 0) monthsToAvg.push(uniqueMonths[currentMonthIdx - 1]);
          if (currentMonthIdx > 1) monthsToAvg.push(uniqueMonths[currentMonthIdx - 2]);
          
          let totalTqs = 0, count = 0;
          monthsToAvg.forEach(monthName => {
            const monthData = DASHBOARD_DATA[name]?.months?.[monthName];
            if (monthData) {
              const d = _getEffectiveData(monthData);
              if (d && d.tqs > 0) {
                totalTqs += d.tqs;
                count++;
              }
            }
          });
          avgTqs3 = count > 0 ? (totalTqs / count) * 100 : 0;
        } else {
          // Средний по периодам внутри месяца (текущий + 2 предыдущих)
          const periodsToAvg = [];
          if (m.periods) {
            const currentIdx = m.periods.findIndex(p => p.period === currentRatingPeriod);
            if (currentIdx >= 0) {
              periodsToAvg.push(m.periods[currentIdx]);
              if (currentIdx > 0) periodsToAvg.push(m.periods[currentIdx - 1]);
              if (currentIdx > 1) periodsToAvg.push(m.periods[currentIdx - 2]);
            }
          }
          let totalTqs = 0, count = 0;
          periodsToAvg.forEach(p => {
            if (p && p.tqs > 0) {
              totalTqs += p.tqs;
              count++;
            }
          });
          avgTqs3 = count > 0 ? (totalTqs / count) * 100 : 0;
        }

        empDataList.push({ 
          name, 
          tqs: currentData.tqs * 100, 
          trend: trend * 100,
          periodTqs: periodTqs,
          periodTrend: periodTrend,
          avgTqs3: avgTqs3
        });
      });

      empDataList.sort((a, b) => b.tqs - a.tqs);

      let html = '';
      empDataList.forEach((ep, idx) => {
        let trendHtml = '<span style="color:#94a3b8">▬ 0.0%</span>';
        if (ep.trend > 0.5) trendHtml = `<span style="color:#22c55e">▲ +${ep.trend.toFixed(1)}%</span>`;
        if (ep.trend < -0.5) trendHtml = `<span style="color:#ef4444">▼ ${ep.trend.toFixed(1)}%</span>`;

        let periodTrendHtml = '<span style="color:#94a3b8">▬ 0.0%</span>';
        if (ep.periodTrend > 0.5) periodTrendHtml = `<span style="color:#22c55e">▲ +${ep.periodTrend.toFixed(1)}%</span>`;
        if (ep.periodTrend < -0.5) periodTrendHtml = `<span style="color:#ef4444">▼ ${ep.periodTrend.toFixed(1)}%</span>`;

        let rankColor = idx === 0 ? '#fbbf24' : (idx === 1 ? '#94a3b8' : (idx === 2 ? '#b45309' : '#4a5568'));

        html += `<tr style="cursor:pointer;border-bottom:1px solid rgba(255,255,255,0.05);" onclick="selectEmployee('${ep.name.replace(/'/g, "\\'")}')">
          <td style="font-weight:800;color:${rankColor};font-size:14px;">${idx + 1}</td>
          <td style="font-weight:600;">${ep.name}</td>
          <td style="font-weight:800;color:${thmC('#e2e8f0','#18181b')};">${ep.tqs.toFixed(1)}%</td>
          <td style="font-size:12px;">${trendHtml}</td>
          <td style="font-weight:600;color:#93c5fd;">${ep.periodTqs.toFixed(1)}%</td>
          <td style="font-size:12px;">${periodTrendHtml}</td>
          <td style="font-weight:600;color:#fbbf24;">${ep.avgTqs3.toFixed(1)}%</td>
        </tr>`;
      });
      tbody.innerHTML = html || '<tr><td colspan="7" style="text-align:center;color:#64748b;padding:20px;">Нет данных для рейтинга</td></tr>';
    }

    // ========== 5. REGLAMENT RENDERING ==========
    function renderCriteria() {
      const g = document.getElementById('criteriaGrid');
      CRITERIA.forEach(c => {
        g.innerHTML += `<div class="crit-card" style="border-top:3px solid ${c.color}"><div class="crit-num">${c.n}</div><div class="crit-weight" style="color:${c.color}">${c.weight}%</div><div class="crit-name">${c.name}</div><div class="crit-desc">${c.desc}</div><div class="crit-bar" style="background:linear-gradient(90deg,${c.color},${c.color}44);width:${c.weight * 5}%"></div></div>`;
      });
    }

    function renderSVP() {
      const c = document.getElementById('svpContainer'); c.innerHTML = '';
      const svpData = currentObjMode === 'B2C' ? SVP_STAGES_REG : SVP_STAGES_B2B; svpData.forEach((s, i) => {
        const el = document.createElement('div'); el.className = 'svp-stage' + (i === 0 ? ' active' : '');
        el.innerHTML = `<div class="svp-num">${s.num}</div><div class="svp-title">${s.title}</div><div class="svp-desc">${s.desc}</div><div class="svp-detail">${s.detail}</div>`;
        el.onclick = () => { document.querySelectorAll('.svp-stage').forEach(x => x.classList.remove('active')); el.classList.add('active'); };
        c.appendChild(el);
      });
    }

    function renderLaws() {
      const g = document.getElementById('lawGrid'); g.innerHTML = '';
      const lawData = currentObjMode === 'B2C' ? LAWS : LAWS_B2B; lawData.forEach((l, i) => { g.innerHTML += `<div class="law-card" onclick="openLawModal(${i})"><div class="law-art">${l.art}</div><div class="law-name">${l.name}</div><div class="law-text">${l.text.substring(0, 80)}...</div></div>`; });
    }
    function openLawModal(i) {
      const l = currentObjMode === 'B2C' ? LAWS[i] : LAWS_B2B[i];
      document.getElementById('lawModalContent').innerHTML = `<div style="font-size:22px;font-weight:800;color:#a78bfa;margin-bottom:4px">${l.art}</div><div style="font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:12px">${l.name}</div><div style="font-size:12px;color:#94a3b8;line-height:1.6;margin-bottom:16px">${l.text}</div><div style="background:rgba(167,139,250,0.1);border:1px solid #4c1d95;border-radius:8px;padding:14px;"><div style="font-size:10px;font-weight:700;color:#a78bfa;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:3px;"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg> Пример цитирования</div><div style="font-size:12px;color:#c4b5fd;line-height:1.6;font-style:italic">"${l.use}"</div></div>`;
      document.getElementById('lawModal').classList.add('open');
    }
    function closeLawModal() { document.getElementById('lawModal').classList.remove('open'); }

    // ========== 6. OBJECTIONS ==========
    let currentCat = 'Все', searchTerm = '';
    function renderCatTabs() { const el = document.getElementById('catTabs'); el.innerHTML = ''; CATEGORIES.forEach(cat => { const btn = document.createElement('div'); btn.className = 'cat-tab' + (cat === currentCat ? ' active' : ''); const objData = currentObjMode === 'B2C' ? OBJECTIONS : OBJECTIONS_B2B; const cnt = cat === 'Все' ? objData.length : objData.filter(o => o.cat === cat).length; btn.textContent = cat + ' (' + cnt + ')'; btn.onclick = () => { currentCat = cat; renderCatTabs(); renderObjList(); }; el.appendChild(btn); }) }
    function filterObj() { searchTerm = document.getElementById('objSearch').value.toLowerCase().trim(); renderObjList(); }
    function renderObjList() {
      const container = document.getElementById('objList');
      const objData = currentObjMode === 'B2C' ? OBJECTIONS : OBJECTIONS_B2B; const filtered = objData.filter(o => (currentCat === 'Все' || o.cat === currentCat) && (!searchTerm || o.q.toLowerCase().includes(searchTerm) || o.script.toLowerCase().includes(searchTerm)));
      document.getElementById('objCount').textContent = 'Найдено: ' + filtered.length + ' из ' + objData.length + ' кейсов';
      if (!filtered.length) { container.innerHTML = '<div style="text-align:center;padding:40px;color:#4a5568;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> Ничего не найдено</div>'; return; }
      const groups = {}; filtered.forEach(o => { if (!groups[o.cat]) groups[o.cat] = []; groups[o.cat].push(o); });
      let html = '';
      Object.entries(groups).forEach(([cat, items]) => {
        const c = CAT_COLORS[cat] || {};
        html += `<div class="obj-group"><div class="obj-group-title">${cat} — ${items.length} кейс${items.length < 5 ? 'а' : 'ов'}</div>`;
        items.forEach(o => {
          const lawsHtml = o.laws.length ? `<div class="laws-line">${o.laws.map(l => `<span class="law-chip" onclick="openLawByName('${l}')">${l} ГК РУз ↗</span>`).join('')}</div>` : '';
          const bs = c.bg ? `background:${c.bg};color:${c.color}` : '';
          html += `<div class="acc-item" id="acc-${o.id}"><div class="acc-header" onclick="toggleAcc(${o.id})"><span class="acc-num">#${String(o.id).padStart(2, '0')}</span><span class="acc-q">${o.q}</span><div class="acc-meta"><span class="acc-cat-badge" style="${bs}">${cat}</span><span class="acc-chevron">▼</span></div></div><div class="acc-body"><div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin:14px 0 6px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:3px;"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg> Скрипт отработки</div><div class="script-box" id="script-${o.id}">${o.script}</div>${lawsHtml}<button class="copy-btn" id="copy-${o.id}" onclick="copyScript(${o.id})"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg> Скопировать скрипт</button></div></div>`;
        });
        html += '</div>';
      });
      container.innerHTML = html;
    }
    function toggleAcc(id) { document.getElementById('acc-' + id).classList.toggle('open'); }
    function copyScript(id) { const t = document.getElementById('script-' + id).textContent; navigator.clipboard.writeText(t).then(() => { const b = document.getElementById('copy-' + id); b.textContent = '✅ Скопировано!'; b.classList.add('copied'); setTimeout(() => { b.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg> Скопировать скрипт'; b.classList.remove('copied'); }, 2000); }); }
    function openLawByName(name) {
      const lawData = currentObjMode === 'B2C' ? LAWS : LAWS_B2B;
      const idx = lawData.findIndex(l => l.art.includes(name));
      if (idx !== -1) { showSection('reglament'); setTimeout(() => openLawModal(idx), 300); }
    }

    let topChartIns = null;
    let botChartIns = null;

    function buildTopBottomCharts() {
      const topCanvas = document.getElementById('topChart');
      const botCanvas = document.getElementById('bottomChart');
      if (!topCanvas || !botCanvas) return;

      const empDataList = [];
      Object.entries(DASHBOARD_DATA).forEach(([name, emp]) => {
        if(name.includes('Промежуточный')) return;
        const m = emp.months?.[currentMonth]; if (!m) return;
        
        // Используем выбранный период для рейтинга
        let d;
        if (currentRatingPeriod === 'Все периоды') {
          d = _getEffectiveData(m);
        } else {
          d = m.periods?.find(p => p.period === currentRatingPeriod);
        }
        
        if (!d || d.tqs === undefined || isNaN(d.tqs)) return;
        empDataList.push({ name: name.split(' ')[0], tqs: parseFloat((d.tqs * 100).toFixed(1)) });
      });

      empDataList.sort((a, b) => b.tqs - a.tqs);

      const top5 = empDataList.slice(0, 5);
      const bot3 = empDataList.slice(-3).reverse();

      if(topChartIns) topChartIns.destroy();
      if(botChartIns) botChartIns.destroy();

      topChartIns = new Chart(topCanvas.getContext('2d'), {
          type: 'bar',
          data: { labels: top5.map(e => e.name), datasets: [{ label: 'TQS %', data: top5.map(e=>e.tqs), backgroundColor: '#22c55e', borderRadius: 4 }] },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
                     scales: { y: { min: 50, max: 100, ticks: {color:'#94a3b8'} }, x:{ ticks: {color:'#94a3b8'} } }
          }
      });

      botChartIns = new Chart(botCanvas.getContext('2d'), {
          type: 'bar',
          data: { labels: bot3.map(e => e.name), datasets: [{ label: 'TQS %', data: bot3.map(e=>e.tqs), backgroundColor: '#ef4444', borderRadius: 4 }] },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
                     scales: { y: { min: 20, max: 100, ticks: {color:'#94a3b8'} }, x:{ ticks: {color:'#94a3b8'} } }
          }
      });
    }

    // ========== 7. INIT ==========
    async function pageInit() {
      showLoading(true);
      const ok = await loadDashboardDataFromAPI();
      if (ok) {
        initFilters();
        initHeatmapModeTabs();
        
        // Инициализация для страницы Rating
        if (document.getElementById('leaderboardBody')) {
          buildLeaderboard();
          buildTopBottomCharts();
        } else {
          setViewMode(currentViewMode);
          if (window.FileUploader) {
            window.FileUploader.init();
          }
        }
      }
      showLoading(false);
    }
    window.pageInit = pageInit;

    document.addEventListener('DOMContentLoaded', () => {
      pageInit();
    });
    window.showSection = showSection; window.toggleTheme = toggleTheme; window.showEmployee = showEmployee; window.selectEmployee = selectEmployee;
    window.openLawModal = openLawModal; window.closeLawModal = closeLawModal; window.copyScript = copyScript;
    window.filterObj = filterObj; window.toggleAcc = toggleAcc; window.openLawByName = openLawByName;
    window.toggleSidebar = toggleSidebar;

    // ========== FILE UPLOAD MODULE ==========
    window.FileUploader = {
        init() {
            const dropZone = document.getElementById('drop-zone');
            const fileInput = document.getElementById('file-input');
            if (!dropZone || !fileInput) return;

            // Click to select
            dropZone.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));

            // Drag & drop
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('dragover');
            });
            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('dragover');
            });
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
                this.handleFiles(e.dataTransfer.files);
            });

            // Загрузить статус данных
            this.refreshChecklist();
        },

        async handleFiles(fileList) {
            if (!fileList || fileList.length === 0) return;

            const logCard = document.getElementById('upload-log-card');
            const logEl = document.getElementById('upload-log');
            if (logCard) logCard.style.display = 'block';
            if (logEl) logEl.innerHTML = '';

            this.log('📤 Начинаю загрузку ' + fileList.length + ' файлов...', 'info');

            const formData = new FormData();
            for (const file of fileList) {
                formData.append('files', file);
                this.log('📎 ' + file.name + ' (' + (file.size / 1024).toFixed(0) + ' KB)', 'info');
            }

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    this.log('❌ Ошибка сервера: ' + response.status, 'error');
                    return;
                }

                const data = await response.json();

                let uploadedMonth = null;
                for (const result of data.results) {
                    if (result.status === 'ok') {
                        uploadedMonth = result.month;
                        const typeNames = {
                            quality: '📊 Quality (оценки)',
                            collections: '💰 Сборы',
                            crm: '📋 CRM-действия',
                            report: '📄 Промежуточный отчёт'
                        };
                        this.log(
                            '✅ ' + result.filename + ' → ' +
                            (typeNames[result.type] || result.type) +
                            ' | ' + result.month + ' ' + result.period +
                            ' | ' + result.employees_count + ' сотрудников',
                            'success'
                        );
                    } else {
                        this.log('❌ ' + result.filename + ': ' + result.message, 'error');
                    }
                }

                if (uploadedMonth) {
                    if (typeof currentMonth !== 'undefined') {
                        currentMonth = uploadedMonth;
                        localStorage.setItem('current-month', uploadedMonth);
                        localStorage.setItem('view-mode', 'team');

                        const mSelect = document.getElementById('monthSelect');
                        if (mSelect) {
                            let optionExists = false;
                            for (let i = 0; i < mSelect.options.length; i++) {
                                if (mSelect.options[i].value === uploadedMonth) {
                                    optionExists = true;
                                    break;
                                }
                            }
                            if (!optionExists) {
                                const o = document.createElement('option');
                                o.value = uploadedMonth;
                                o.textContent = uploadedMonth;
                                mSelect.appendChild(o);
                            }
                            mSelect.value = uploadedMonth;
                        }
                        
                        if (typeof updatePeriodTabs === 'function') {
                            updatePeriodTabs();
                        }
                    }
                }

                this.log('🔄 Обновляю дашборд...', 'info');
                await this.refreshChecklist();

                // Перезагрузить данные дашборда
                if (typeof updateDashboard === 'function') {
                    await updateDashboard();
                }
                
                // Показать кнопку Обновить
                const refreshBtn = document.getElementById('upload-refresh-btn');
                if (refreshBtn) {
                    refreshBtn.style.display = 'inline-flex';
                }

                this.log('✅ Дашборд обновлён!', 'success');
                this.log('ℹ️ Нажмите кнопку "Обновить данные" ниже или "Обновить данные аналитики" выше, чтобы применить изменения.', 'info');
                
                // Автоматический переход в оперативное пространство через 2 секунды
                this.log('🔄 Переключение в аналитику через 2 секунды...', 'info');
                setTimeout(function() {
                  setViewMode('team');
                }, 2000);

            } catch (err) {
                this.log('❌ Ошибка: ' + err.message, 'error');
            }
        },

        async refreshChecklist() {
            try {
                const response = await fetch('/api/upload/status');
                const data = await response.json();
                this.renderChecklist(data);
            } catch (e) {
                console.error('Failed to load upload status:', e);
            }
        },

        renderChecklist(data) {
            const container = document.getElementById('upload-checklist');
            const progressFill = document.getElementById('upload-progress-fill');
            const progressText = document.getElementById('upload-progress-text');
            if (!container) return;

            const periods = data.periods || [];
            const months = data.months || [];

            // Ищем статус для выбранного месяца
            let activeMonthStatus = null;
            if (typeof currentMonth !== 'undefined' && currentMonth) {
                activeMonthStatus = months.find(m => m.month === currentMonth);
            }

            // Если не нашли статус месяца в months, собираем из periods
            if (!activeMonthStatus && typeof currentMonth !== 'undefined' && currentMonth) {
                const monthPeriods = periods.filter(p => p.month === currentMonth);
                activeMonthStatus = {
                    month: currentMonth,
                    has_quality: monthPeriods.some(p => p.has_quality),
                    has_collections: monthPeriods.some(p => p.has_collections),
                    has_crm: monthPeriods.some(p => p.has_crm),
                    has_report: monthPeriods.some(p => p.has_report),
                    employees_count: monthPeriods.length > 0 ? monthPeriods[0].employees_count : 0
                };
            }

            const latest = activeMonthStatus;

            const items = [
                { key: 'has_quality', label: 'Quality (оценки звонков)', icon: '📊' },
                { key: 'has_collections', label: 'Сборы (финансы)', icon: '💰' },
                { key: 'has_crm', label: 'CRM-действия', icon: '📋' },
                { key: 'has_report', label: 'Промежуточный отчёт (PDF)', icon: '📄' },
            ];

            let loaded = 0;
            container.innerHTML = items.map(item => {
                const done = latest && latest[item.key];
                if (done) loaded++;
                
                const iconHtml = done 
                    ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><polyline points="20 6 9 17 4 12"></polyline></svg>`
                    : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><rect x="3" y="3" width="18" height="18" rx="4"></rect></svg>`;

                return `
                    <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;
                        background:${done ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.1)'};
                        border:1px solid ${done ? 'rgba(16,185,129,0.35)' : 'rgba(239,68,68,0.25)'};
                        border-radius:8px;
                        transition: all 0.2s ease;">
                        <span style="display:flex;align-items:center;">${iconHtml}</span>
                        <div>
                            <div style="font-size:12px;font-weight:700;color:${done ? '#10b981' : '#ef4444'};">
                                ${item.icon} ${item.label}
                            </div>
                            <div style="font-size:10px;color:#94a3b8;margin-top:2px;">
                                ${done ? 'Загружен' : 'Не загружен'}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            const percent = (loaded / items.length) * 100;
            if (progressFill) progressFill.style.width = percent + '%';
            if (progressText) {
                progressText.textContent = latest
                    ? `${latest.month} · ${loaded}/4 файла загружено · ${latest.employees_count} сотрудников`
                    : 'Нет загруженных данных';
            }
        },

        log(message, type) {
            const logEl = document.getElementById('upload-log');
            if (!logEl) return;
            const colors = { info: '#94a3b8', success: '#4ade80', error: '#f87171' };
            const div = document.createElement('div');
            div.style.color = colors[type] || '#94a3b8';
            div.textContent = message;
            logEl.appendChild(div);
            logEl.scrollTop = logEl.scrollHeight;
        }
    };

function escapeHtml(value) {
  return String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function cleanupDisplayText(value) {
  return String(value || '')
    .replace(/\uFFFD/g, '')
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '')
    .replace(/\(\s*\d{2}(?:\s+\d{2}){2,}[^)]*\)/g, '')
    .replace(/!B@0=8F0|1I89|@0745;|B5<0|:>=B5=B/gi, '')
    .replace(/\r/g, '')
    .replace(/[ \t]+$/gm, '');
}

function normalizeSearchText(value) {
  return cleanupDisplayText(value).toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-я0-9\s]+/gi, ' ').replace(/\s+/g, ' ').trim();
}

function matchesSearch(indexText, query) {
  const q = normalizeSearchText(query);
  if (!q) return true;
  const haystack = normalizeSearchText(indexText);
  const parts = q.split(' ').filter((x) => x.length >= 2);
  return parts.every((p) => haystack.includes(p));
}

function formatInline(text) {
  return escapeHtml(cleanupDisplayText(text))
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="tactical-code">$1</code>')
    .replace(/&lt;br\s*\/?&gt;/gi, '<br/>');
}

function markdownToSimpleHtml(mdText) {
  const lines = cleanupDisplayText(mdText).split(/\r?\n/);
  let html = '';
  let inList = false;
  let inTable = false;

  const close = () => {
    if (inList) {
      html += '</ul>';
      inList = false;
    }
    if (inTable) {
      html += '</tbody></table></div>';
      inTable = false;
    }
  };

  const isSep = (line) => /^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line.trim());
  const cells = (line) => line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((c) => formatInline(c.trim()));

  lines.forEach((line, idx) => {
    const l = line.trim();
    if (!l) {
      close();
      return;
    }
    if (l.startsWith('# ')) {
      close();
      html += `<h3 class="tactical-text-title" style="font-size:18px;margin:16px 0 10px;">${formatInline(l.slice(2))}</h3>`;
      return;
    }
    if (l.startsWith('## ')) {
      close();
      html += `<h4 class="tactical-text-accent" style="font-size:15px;margin:14px 0 8px;">${formatInline(l.slice(3))}</h4>`;
      return;
    }
    if (l.startsWith('### ')) {
      close();
      html += `<h5 class="tactical-text-accent" style="font-size:14px;margin:12px 0 6px;">${formatInline(l.slice(4))}</h5>`;
      return;
    }
    if (l.startsWith('- ')) {
      if (inTable) {
        html += '</tbody></table></div>';
        inTable = false;
      }
      if (!inList) {
        html += `<ul class="tactical-text-body" style="margin:6px 0 12px 18px;line-height:1.6;font-size:13px;">`;
        inList = true;
      }
      html += `<li style="margin:4px 0;">${formatInline(l.slice(2))}</li>`;
      return;
    }
    if (l.startsWith('|')) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      const next = lines[idx + 1] ? lines[idx + 1].trim() : '';
      if (!inTable && next && isSep(next)) {
        html += `<div style="overflow-x:auto;margin:8px 0 14px;"><table class="tactical-text-body" style="width:100%;border-collapse:collapse;font-size:12px;"><thead><tr>`;
        cells(l).forEach((c) => { html += `<th class="tactical-th" style="text-align:left;padding:8px;">${c}</th>`; });
        html += '</tr></thead><tbody>';
        inTable = true;
        return;
      }
      if (isSep(l)) return;
      if (inTable) {
        html += '<tr>';
        cells(l).forEach((c) => { html += `<td class="tactical-td" style="vertical-align:top;padding:8px;">${c}</td>`; });
        html += '</tr>';
        return;
      }
    }
    close();
    html += `<p class="tactical-text-body" style="font-size:13px;line-height:1.7;margin:8px 0;">${formatInline(l)}</p>`;
  });

  close();
  return html;
}

function splitByHeading(mdText, level) {
  const rx = new RegExp(`^#{${level}}\\s+(.+)$`);
  const lines = cleanupDisplayText(mdText).split(/\r?\n/);
  const out = [];
  let cur = null;
  lines.forEach((line) => {
    const m = line.match(rx);
    if (m) {
      if (cur) out.push(cur);
      cur = { title: cleanupDisplayText(m[1].trim()), lines: [] };
      return;
    }
    if (!cur) cur = { title: 'Общий раздел', lines: [] };
    cur.lines.push(line);
  });
  if (cur) out.push(cur);
  return out.map((x) => ({ title: x.title, content: cleanupDisplayText(x.lines.join('\n').trim()) })).filter((x) => x.content);
}

function buildManualTopics(mdText) {
  const clean = cleanupDisplayText(mdText);
  const candidates = [6, 5, 4, 3, 2].map((lvl) => splitByHeading(clean, lvl).filter((x) => x.title !== 'Общий раздел'));
  const best = candidates.reduce((a, b) => (b.length > a.length ? b : a), []);
  return best.length ? best : splitByHeading(clean, 2);
}

function splitLong(content, title, maxLines) {
  const lines = cleanupDisplayText(content).split(/\r?\n/);
  const pages = [];
  let curTitle = title || 'Тема';
  let cur = [];
  let count = 0;
  const push = () => {
    const t = cur.join('\n').trim();
    if (t) pages.push({ title: curTitle, content: t });
  };
  lines.forEach((line) => {
    const tr = line.trim();
    if (/^#{1,6}\s+/.test(tr)) {
      push();
      curTitle = tr.replace(/^#{1,6}\s+/, '').trim() || curTitle;
      cur = [line];
      count = tr ? 1 : 0;
      return;
    }
    cur.push(line);
    if (tr) count += 1;
    if (count >= maxLines) {
      push();
      cur = [];
      count = 0;
    }
  });
  push();
  return pages.length ? pages : [{ title: title || 'Тема', content }];
}

function renderEmptyTemplate(targetEl, title, path, helper) {
  targetEl.innerHTML = `<div class="card"><div class="card-title">Шаблон контента</div><p>Для раздела <strong>${escapeHtml(title)}</strong> файл пуст: <code>${escapeHtml(path)}</code></p><p style="color:#94a3b8">${escapeHtml(helper)}</p></div>`;
}

async function loadMarkdown(path) {
  try {
    const res = await fetch(path, { cache: 'no-store' });
    return res.ok ? res.text() : '';
  } catch {
    return '';
  }
}

function mountPager(container, pages) {
  const stage = container.querySelector('.js-stage');
  const pills = container.querySelector('.js-pills');
  const prev = container.querySelector('.js-prev');
  const next = container.querySelector('.js-next');
  let idx = 0;
  const render = () => {
    idx = Math.max(0, Math.min(idx, pages.length - 1));
    const p = pages[idx];
    stage.innerHTML = `<div style="display:flex;justify-content:space-between;margin-bottom:8px;"><div class="tactical-text-accent" style="font-weight:700;">${escapeHtml(p.title)}</div><div class="tactical-text-muted" style="font-size:11px;">Страница ${idx + 1} из ${pages.length}</div></div>${markdownToSimpleHtml(p.content)}`;
    pills.innerHTML = pages.map((_, i) => `<button type="button" data-i="${i}" class="tactical-pill ${i === idx ? 'active' : ''}" style="cursor:pointer;border-radius:999px;padding:3px 8px;font-size:11px;">${i + 1}</button>`).join('');
    pills.querySelectorAll('[data-i]').forEach((b) => b.addEventListener('click', () => { idx = Number(b.getAttribute('data-i')); render(); }));
    prev.disabled = idx === 0;
    next.disabled = idx === pages.length - 1;
    prev.style.opacity = idx === 0 ? '0.45' : '1';
    next.style.opacity = idx === pages.length - 1 ? '0.45' : '1';
  };
  prev.addEventListener('click', () => { idx -= 1; render(); });
  next.addEventListener('click', () => { idx += 1; render(); });
  render();
  return { set: (n) => { idx = n; render(); }, get: () => idx, pages };
}

async function initLawPage() {
  const root = document.getElementById('law-content');
  if (!root) return;
  const path = 'content/law/law-offer.md';
  const md = await loadMarkdown(path);
  if (!String(md).trim()) return renderEmptyTemplate(root, 'Нормативная аргументация', path, 'Добавьте пункты оферты, кейсы и примеры реплик.');
  const sections = splitByHeading(md, 2);
  root.innerHTML = `<div class="card"><div class="card-title">База нормативной аргументации</div>${sections.map((s, i) => `<details ${i === 0 ? 'open' : ''} class="law-details" style="margin:8px 0;border-radius:8px;overflow:hidden;"><summary class="law-summary" style="cursor:pointer;padding:9px 10px;font-size:13px;font-weight:600;">${escapeHtml(s.title)}</summary><div style="padding:10px 12px;">${markdownToSimpleHtml(s.content)}</div></details>`).join('')}</div>`;
}

async function initInstrumentsPage() {
  const root = document.getElementById('instruments-content');
  if (!root) return;
  const files = [
    { title: 'Манипуляция', path: 'content/tactical/instruments/manipulation.md' },
    { title: 'Легендирование', path: 'content/tactical/instruments/legending.md' },
    { title: 'Аргументация', path: 'content/tactical/instruments/argumentation.md' },
    { title: 'Выставление требования', path: 'content/tactical/instruments/demand-setting.md' },
    { title: 'Подведение итогов', path: 'content/tactical/instruments/closing-summary.md' }
  ];
  root.innerHTML = `<div class="card" style="margin-bottom:12px;"><div class="card-title">Быстрый поиск по инструментам</div><input id="instruments-search" type="text" placeholder="Введите ключевое слово..." class="tactical-input" style="width:100%;border-radius:8px;padding:8px 10px;font-size:13px;" /></div><div id="instruments-cards"></div>`;
  const host = document.getElementById('instruments-cards');
  const search = document.getElementById('instruments-search');
  const cards = [];
  const pagers = [];

  for (const file of files) {
    const md = cleanupDisplayText((await loadMarkdown(file.path)).trim());
    const block = document.createElement('div');
    block.className = 'card';
    block.style.marginBottom = '12px';
    if (!md) {
      block.innerHTML = `<div class="card-title">${escapeHtml(file.title)}</div><p class="tactical-text-muted">Контент не заполнен: <code>${escapeHtml(file.path)}</code></p>`;
      host.appendChild(block);
      cards.push(block);
      continue;
    }
    const sections = splitByHeading(md, 2).filter((x) => x.title !== 'Общий раздел');
    const source = sections.length ? sections : splitByHeading(md, 3);
    const pages = source.flatMap((s) => splitLong(s.content, s.title, 38));
    block.dataset.search = `${file.title}\n${md}\n${pages.map((p) => p.title).join('\n')}`;
    block.innerHTML = `<div class="card-title">${escapeHtml(file.title)}</div><div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:8px;"><div class="tactical-text-muted" style="font-size:12px;">Тем: ${pages.length}</div><div style="display:flex;gap:8px;"><button class="cat-tab js-prev" type="button">Назад</button><button class="cat-tab js-next" type="button">Вперед</button></div></div><div class="js-pills" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;"></div><div class="js-stage" class="tactical-stage" style="border-radius:10px;padding:10px 12px;"></div>`;
    host.appendChild(block);
    cards.push(block);
    pagers.push({ card: block, pager: mountPager(block, pages) });
  }

  const applyFilter = () => {
    const q = search.value || '';
    cards.forEach((c) => { c.style.display = matchesSearch(c.dataset.search || c.textContent || '', q) ? '' : 'none'; });
    if (!normalizeSearchText(q)) return;
    pagers.forEach(({ card, pager }) => {
      if (card.style.display === 'none') return;
      const i = pager.pages.findIndex((p) => matchesSearch(`${p.title}\n${p.content}`, q));
      if (i >= 0) pager.set(i);
    });
  };
  search.addEventListener('input', applyFilter);
}

async function initManualPage() {
  const graph = document.getElementById('manual-graph');
  const detail = document.getElementById('manual-step-detail');
  const prev = document.getElementById('manual-prev');
  const next = document.getElementById('manual-next');
  if (!graph || !detail || !prev || !next) return;

  const md = await loadMarkdown('content/tactical/manual/manual-flow.md');
  const topics = buildManualTopics(md);
  const steps = topics.length ? topics.map((t, i) => ({ id: `topic-${i + 1}`, label: t.title || `Тема ${i + 1}` })) : [{ id: 'step-1', label: 'Тема 1' }];
  const pagesByStep = steps.map((s, i) => splitLong(topics[i] ? topics[i].content : `## ${s.label}\nМатериал не загружен`, s.label, 30));

  let stepIdx = 0;
  let stepPage = 0;

  const renderTiles = () => {
    graph.innerHTML = `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;">${steps.map((s, i) => `<button type="button" data-step="${i}" class="tactical-graph-btn ${i === stepIdx ? 'active' : ''}" style="text-align:left;cursor:pointer;border-radius:12px;padding:10px 12px;"><div class="tactical-topic-label ${i === stepIdx ? 'active' : ''}" style="font-size:12px;">Тема ${i + 1}</div><div style="font-size:13px;font-weight:700;line-height:1.35;">${escapeHtml(s.label)}</div></button>`).join('')}</div>`;
    graph.querySelectorAll('[data-step]').forEach((b) => b.addEventListener('click', () => { stepIdx = Number(b.getAttribute('data-step')); stepPage = 0; renderTiles(); renderDetail(); }));
  };

  const renderDetail = () => {
    const pages = pagesByStep[stepIdx] || [{ title: steps[stepIdx].label, content: '' }];
    if (stepPage >= pages.length) stepPage = pages.length - 1;
    const p = pages[stepPage];
    detail.innerHTML = `<div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-bottom:8px;"><h4 class="tactical-text-title" style="margin:0;font-size:16px;">${escapeHtml(steps[stepIdx].label)}</h4><div class="tactical-text-muted" style="font-size:11px;">Шаг ${stepIdx + 1} из ${steps.length}</div></div><label class="tactical-text-muted" style="display:block;font-size:11px;margin-bottom:4px;">Быстрый переход к теме</label><select id="manual-step-select" class="tactical-input" style="width:100%;border-radius:8px;padding:8px 10px;font-size:13px;margin-bottom:8px;">${steps.map((s, i) => `<option value="${i}" ${i === stepIdx ? 'selected' : ''}>${escapeHtml(s.label)}</option>`).join('')}</select><div style="display:flex;justify-content:space-between;margin-bottom:8px;"><div class="tactical-text-accent" style="font-size:12px;font-weight:600;">${escapeHtml(p.title)}</div><div class="tactical-text-muted" style="font-size:11px;">Страница ${stepPage + 1} из ${pages.length}</div></div><div class="tactical-stage-alt" style="border-radius:10px;padding:10px 12px;">${markdownToSimpleHtml(p.content)}</div><div id="manual-step-pills" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;"></div><div style="display:flex;gap:8px;margin-top:8px;"><button type="button" id="manual-step-page-prev" class="cat-tab">Стр. назад</button><button type="button" id="manual-step-page-next" class="cat-tab">Стр. вперед</button></div>`;
    const pills = detail.querySelector('#manual-step-pills');
    pills.innerHTML = pages.map((_, i) => `<button type="button" data-i="${i}" class="tactical-pill ${i === stepPage ? 'active' : ''}" style="cursor:pointer;border-radius:999px;padding:3px 8px;font-size:11px;">${i + 1}</button>`).join('');
    pills.querySelectorAll('[data-i]').forEach((b) => b.addEventListener('click', () => { stepPage = Number(b.getAttribute('data-i')); renderDetail(); }));
    detail.querySelector('#manual-step-page-prev').addEventListener('click', () => { if (stepPage > 0) { stepPage -= 1; renderDetail(); } });
    detail.querySelector('#manual-step-page-next').addEventListener('click', () => { if (stepPage < pages.length - 1) { stepPage += 1; renderDetail(); } });
    detail.querySelector('#manual-step-select').addEventListener('change', (e) => { stepIdx = Number(e.target.value); stepPage = 0; renderTiles(); renderDetail(); });
    prev.disabled = stepIdx === 0;
    next.disabled = stepIdx === steps.length - 1;
    prev.style.opacity = stepIdx === 0 ? '0.45' : '1';
    next.style.opacity = stepIdx === steps.length - 1 ? '0.45' : '1';
  };

  const renderTopics = () => {
    if (!topics.length) return;
    const wrap = document.createElement('div');
    wrap.id = 'manual-sections';
    wrap.className = 'card';
    wrap.style.marginTop = '14px';
    wrap.innerHTML = `<div class="card-title">Полный мануал по темам</div><label class="tactical-text-muted" style="display:block;font-size:11px;margin-bottom:4px;">Быстрый переход к теме</label><select id="manual-topic-select" class="tactical-input" style="width:100%;border-radius:8px;padding:8px 10px;font-size:13px;margin-bottom:8px;">${topics.map((t, i) => `<option value="${i}">${escapeHtml(t.title || `Тема ${i + 1}`)}</option>`).join('')}</select><div style="display:flex;justify-content:space-between;margin-bottom:8px;"><div id="manual-topic-title" class="tactical-text-accent" style="font-size:13px;font-weight:700;"></div><div id="manual-topic-meta" class="tactical-text-muted" style="font-size:11px;"></div></div><div id="manual-topic-stage" class="tactical-stage-alt" style="border-radius:10px;padding:10px 12px;"></div><div id="manual-topic-pills" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;"></div><div style="display:flex;gap:8px;margin-top:8px;"><button type="button" id="manual-topic-prev" class="cat-tab">Тема назад</button><button type="button" id="manual-topic-next" class="cat-tab">Тема вперед</button></div>`;
    const card = detail.closest('.card');
    if (card) card.insertAdjacentElement('afterend', wrap);
    const titleEl = wrap.querySelector('#manual-topic-title');
    const metaEl = wrap.querySelector('#manual-topic-meta');
    const stageEl = wrap.querySelector('#manual-topic-stage');
    const pillsEl = wrap.querySelector('#manual-topic-pills');
    const selectEl = wrap.querySelector('#manual-topic-select');
    const prevEl = wrap.querySelector('#manual-topic-prev');
    const nextEl = wrap.querySelector('#manual-topic-next');
    let i = 0;
    const render = () => {
      const t = topics[i];
      titleEl.textContent = t.title || `Тема ${i + 1}`;
      metaEl.textContent = `Тема ${i + 1} из ${topics.length}`;
      stageEl.innerHTML = markdownToSimpleHtml(t.content || '');
      selectEl.value = String(i);
      prevEl.disabled = i === 0;
      nextEl.disabled = i === topics.length - 1;
      pillsEl.innerHTML = topics.map((_, n) => `<button type="button" data-i="${n}" class="tactical-pill ${n === i ? 'active' : ''}" style="cursor:pointer;border-radius:999px;padding:3px 8px;font-size:11px;">${n + 1}</button>`).join('');
      pillsEl.querySelectorAll('[data-i]').forEach((b) => b.addEventListener('click', () => { i = Number(b.getAttribute('data-i')); render(); }));
    };
    prevEl.addEventListener('click', () => { if (i > 0) { i -= 1; render(); } });
    nextEl.addEventListener('click', () => { if (i < topics.length - 1) { i += 1; render(); } });
    selectEl.addEventListener('change', () => { i = Number(selectEl.value); render(); });
    render();
  };

  prev.onclick = () => { if (stepIdx > 0) { stepIdx -= 1; stepPage = 0; renderTiles(); renderDetail(); } };
  next.onclick = () => { if (stepIdx < steps.length - 1) { stepIdx += 1; stepPage = 0; renderTiles(); renderDetail(); } };
  renderTiles();
  renderDetail();
  renderTopics();
}

window.initLawPage = initLawPage;
window.initInstrumentsPage = initInstrumentsPage;
window.initManualPage = initManualPage;

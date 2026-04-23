function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function markdownToSimpleHtml(mdText) {
  const lines = mdText.split(/\r?\n/);
  let html = '';
  let inList = false;

  lines.forEach((line) => {
    const l = line.trim();
    if (!l) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      return;
    }

    if (l.startsWith('# ')) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      html += `<h3 style="font-size:18px;color:#f1f5f9;margin:16px 0 10px;">${escapeHtml(l.slice(2))}</h3>`;
      return;
    }

    if (l.startsWith('## ')) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      html += `<h4 style="font-size:15px;color:#fb923c;margin:14px 0 8px;">${escapeHtml(l.slice(3))}</h4>`;
      return;
    }

    if (l.startsWith('- ')) {
      if (!inList) {
        html += '<ul style="margin:6px 0 12px 18px;color:#cbd5e1;line-height:1.6;font-size:13px;">';
        inList = true;
      }
      html += `<li style="margin:4px 0;">${escapeHtml(l.slice(2))}</li>`;
      return;
    }

    if (inList) {
      html += '</ul>';
      inList = false;
    }
    html += `<p style="font-size:13px;color:#cbd5e1;line-height:1.7;margin:8px 0;">${escapeHtml(l)}</p>`;
  });

  if (inList) html += '</ul>';
  return html;
}

async function loadMarkdown(path) {
  try {
    const response = await fetch(path, { cache: 'no-store' });
    if (!response.ok) return '';
    return await response.text();
  } catch (_err) {
    return '';
  }
}

function renderEmptyTemplate(targetEl, title, filePath, helper) {
  targetEl.innerHTML = `
    <div class="card" style="margin-bottom:16px;">
      <div class="card-title">Шаблон контента</div>
      <div style="font-size:13px;color:#cbd5e1;line-height:1.7;">
        <p style="margin:0 0 8px;">Для раздела <strong>${escapeHtml(title)}</strong> файл пока пуст:</p>
        <p style="margin:0 0 12px;color:#94a3b8;"><code>${escapeHtml(filePath)}</code></p>
        <p style="margin:0;color:#94a3b8;">${escapeHtml(helper)}</p>
      </div>
    </div>
  `;
}

async function initLawPage() {
  const root = document.getElementById('law-content');
  if (!root) return;
  const filePath = 'content/law/law-offer.md';
  const md = await loadMarkdown(filePath);

  if (!md.trim()) {
    renderEmptyTemplate(
      root,
      'Нормативная аргументация',
      filePath,
      'Добавьте пункты оферты, кейсы применения и примеры реплик оператора.'
    );
    return;
  }

  root.innerHTML = `<div class="card">${markdownToSimpleHtml(md)}</div>`;
}

async function initInstrumentsPage() {
  const root = document.getElementById('instruments-content');
  if (!root) return;

  const toolFiles = [
    { title: 'Манипуляция', path: 'content/tactical/instruments/manipulation.md' },
    { title: 'Легендирование', path: 'content/tactical/instruments/legending.md' },
    { title: 'Аргументация', path: 'content/tactical/instruments/argumentation.md' },
    { title: 'Выставление требования', path: 'content/tactical/instruments/demand-setting.md' },
    { title: 'Подведение итогов', path: 'content/tactical/instruments/closing-summary.md' }
  ];

  let html = '';
  for (const tool of toolFiles) {
    const md = await loadMarkdown(tool.path);
    if (!md.trim()) {
      html += `
        <div class="card" style="margin-bottom:12px;">
          <div class="card-title">${escapeHtml(tool.title)}</div>
          <p style="margin:0;color:#94a3b8;font-size:13px;">
            Контент не заполнен. Файл: <code>${escapeHtml(tool.path)}</code>
          </p>
        </div>
      `;
    } else {
      html += `
        <div class="card" style="margin-bottom:12px;">
          <div class="card-title">${escapeHtml(tool.title)}</div>
          ${markdownToSimpleHtml(md)}
        </div>
      `;
    }
  }

  root.innerHTML = html;
}

async function initManualPage() {
  const graphEl = document.getElementById('manual-graph');
  const detailEl = document.getElementById('manual-step-detail');
  const prevBtn = document.getElementById('manual-prev');
  const nextBtn = document.getElementById('manual-next');
  if (!graphEl || !detailEl || !prevBtn || !nextBtn) return;

  const filePath = 'content/tactical/manual/manual-flow.md';
  const md = await loadMarkdown(filePath);
  const fallbackSteps = [
    { id: 'step-1', label: 'Вход в контакт', description: 'Старт контакта и фокус на управлении диалогом.' },
    { id: 'step-2', label: 'Диагностика причины', description: 'Уточняем реальную причину просрочки и мотивацию.' },
    { id: 'step-3', label: 'Выбор инструмента', description: 'Подбираем аргументацию/легендирование/манипуляцию.' },
    { id: 'step-4', label: 'Требование и фиксация', description: 'Фиксируем обязательство и финализируем условия.' }
  ];

  let steps = fallbackSteps;
  if (md.trim()) {
    const stepMatches = [...md.matchAll(/- ID:\s*([^\n]+)\n[\s\S]*?- Название:\s*([^\n]+)\n[\s\S]*?- Описание:\s*([^\n]+)\n[\s\S]*?- Почему это важно:\s*([^\n]+)/g)];
    if (stepMatches.length) {
      steps = stepMatches.map((m) => ({
        id: m[1].trim(),
        label: m[2].trim(),
        description: `${m[3].trim()} Почему: ${m[4].trim()}`
      }));
    }
  }

  let currentIdx = 0;

  function renderStep() {
    const step = steps[currentIdx];
    detailEl.innerHTML = `
      <h4 style="margin:0 0 8px;color:#f1f5f9;font-size:16px;">${escapeHtml(step.label)}</h4>
      <p style="margin:0;color:#cbd5e1;font-size:13px;line-height:1.7;">${escapeHtml(step.description)}</p>
      <div style="margin-top:10px;font-size:11px;color:#94a3b8;">Шаг ${currentIdx + 1} из ${steps.length}</div>
    `;

    prevBtn.disabled = currentIdx === 0;
    nextBtn.disabled = currentIdx === steps.length - 1;
    prevBtn.style.opacity = currentIdx === 0 ? '0.45' : '1';
    nextBtn.style.opacity = currentIdx === steps.length - 1 ? '0.45' : '1';
  }

  function renderGraph() {
    const width = 860;
    const height = 200;
    const padX = 65;
    const y = 100;
    const gap = steps.length > 1 ? (width - padX * 2) / (steps.length - 1) : 0;

    let svg = `<svg viewBox="0 0 ${width} ${height}" style="width:100%;max-width:100%;height:auto;">`;
    for (let i = 0; i < steps.length - 1; i++) {
      const x1 = padX + i * gap + 45;
      const x2 = padX + (i + 1) * gap - 45;
      svg += `<line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="#334155" stroke-width="2" />`;
      svg += `<polygon points="${x2 - 6},${y - 4} ${x2},${y} ${x2 - 6},${y + 4}" fill="#334155" />`;
    }

    steps.forEach((step, idx) => {
      const x = padX + idx * gap;
      const active = idx === currentIdx;
      const fill = active ? 'rgba(249,115,22,0.22)' : 'rgba(30,41,59,0.8)';
      const stroke = active ? '#f97316' : '#334155';
      const text = active ? '#f97316' : '#cbd5e1';
      svg += `<g data-step="${idx}" style="cursor:pointer;">
        <rect x="${x - 45}" y="${y - 22}" rx="10" ry="10" width="90" height="44" fill="${fill}" stroke="${stroke}" />
        <text x="${x}" y="${y + 4}" text-anchor="middle" fill="${text}" font-size="11" font-weight="600">${escapeHtml(step.label).slice(0, 16)}</text>
      </g>`;
    });

    svg += '</svg>';
    graphEl.innerHTML = svg;

    graphEl.querySelectorAll('[data-step]').forEach((el) => {
      el.addEventListener('click', () => {
        currentIdx = Number(el.getAttribute('data-step'));
        renderGraph();
        renderStep();
      });
    });
  }

  prevBtn.onclick = () => {
    if (currentIdx > 0) {
      currentIdx -= 1;
      renderGraph();
      renderStep();
    }
  };
  nextBtn.onclick = () => {
    if (currentIdx < steps.length - 1) {
      currentIdx += 1;
      renderGraph();
      renderStep();
    }
  };

  renderGraph();
  renderStep();
}

window.initLawPage = initLawPage;
window.initInstrumentsPage = initInstrumentsPage;
window.initManualPage = initManualPage;

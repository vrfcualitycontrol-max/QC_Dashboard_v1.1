function initSidebar(activeId) {
  const sidebarHtml = `
    <div class="logo" style="display: flex; justify-content: space-between; align-items: center;">
      <div class="logo-text">
        <h1>QC Dashboard</h1>
        <p>Variant Retail Finance · SC Unit</p>
      </div>
      <div class="hamburger" onclick="toggleSidebar()" style="cursor: pointer; font-size: 20px; color: #f97316;">☰</div>
    </div>
    
    <div style="padding:10px 0; overflow-y: auto; height:calc(100vh - 140px); overflow-x:hidden;">
      <div class="nav-section-title">ОПЕРАЦИОННЫЕ ПОКАЗАТЕЛИ</div>
      <a href="analytics.html" class="nav-item ${activeId === 'analytics' ? 'active' : ''}">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg></span>
        Аналитика
      </a>
      <a href="rating.html" class="nav-item ${activeId === 'rating' ? 'active' : ''}">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg></span>
        Рейтинг
      </a>
      <a href="forecast.html" class="nav-item ${activeId === 'forecast' ? 'active' : ''}">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg></span>
        Прогнозирование
      </a>

      <div class="nav-section-title" style="margin-top:15px;">ОПЕРАЦИОННЫЕ ИНСТРУМЕНТЫ</div>
      
      <!-- РсВ Dropdown Placeholder for future CSS/JS toggle -->
      <div style="padding: 10px 16px; color: #a0aec0; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;">БАЗА ВОЗРАЖЕНИЙ</div>
      <a href="objections_b2c.html" class="nav-item ${activeId === 'obj_b2c' ? 'active' : ''}" title="Физ. лица">
        <span class="nav-icon">👤</span> B2C
      </a>
      <a href="objections_b2b.html" class="nav-item ${activeId === 'obj_b2b' ? 'active' : ''}" title="Юр. лица">
        <span class="nav-icon">🏢</span> B2B
      </a>

      <div style="padding: 10px 16px; color: #a0aec0; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;">ТАКТИЧЕСКИЕ ИНСТРУМЕНТЫ</div>
      <a href="law.html" class="nav-item ${activeId === 'law' ? 'active' : ''}">
        <span class="nav-icon">⚖️</span> Нормат. аргументация <span class="nav-badge">В разраб.</span>
      </a>
      <a href="instruments.html" class="nav-item ${activeId === 'instruments' ? 'active' : ''}">
        <span class="nav-icon">🔧</span> Инструментарий <span class="nav-badge">В разраб.</span>
      </a>

      <a href="manual.html" class="nav-item ${activeId === 'manual' ? 'active' : ''}" style="margin-top:10px;">
        <span class="nav-icon">📖</span> Мануал <span class="nav-badge">В разраб.</span>
      </a>

      <div class="nav-section-title" style="margin-top:15px;">РЕГЛАМЕНТ</div>
      <a href="reg_mechanics.html" class="nav-item ${activeId === 'reg_mechanics' ? 'active' : ''}">Механика оценки</a>
      <a href="reg_methodology.html" class="nav-item ${activeId === 'reg_methodology' ? 'active' : ''}">Методология (9 крит.)</a>

      <div class="nav-section-title" style="margin-top:15px; font-size:9px;">АРХИТЕКТУРА СВП</div>
      <a href="svp_mechanism.html" class="nav-item ${activeId === 'svp_mechanism' ? 'active' : ''}">Порядок механизма</a>
      <a href="svp_crm.html" class="nav-item ${activeId === 'svp_crm' ? 'active' : ''}">CRM Soft Collection</a>

      <div class="nav-section-title" style="margin-top:15px;">РЕГЛАМЕНТ РАБОТЫ QC</div>
      <a href="qc_regulations.html" class="nav-item ${activeId === 'qc_regulations' ? 'active' : ''}">Документ</a>

    </div>

    <div style="margin-top:auto;padding:12px 16px;border-top:1px solid #2d3748;" class="bottom-info">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:52px;height:36px;background:#f97316;border-radius:6px;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:14px;">VRF</div>
        <div class="bottom-text">
          <div style="font-size:10px;color:#94a3b8;font-weight:600;">Февраль–Апрель 2026</div>
          <div style="font-size:9px;color:#4a5568;margin-top:1px;">Soft Collection Unit</div>
        </div>
      </div>
    </div>
  `;
  document.getElementById('sidebar').innerHTML = sidebarHtml;
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('collapsed');
  document.getElementById('main').classList.toggle('expanded');
}

// Support Theme toggle universally
function toggleTheme() {
  document.body.classList.toggle('light-theme');
  localStorage.setItem('sc-theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
  if(typeof lineChartInstance !== 'undefined' && lineChartInstance) lineChartInstance.update();
  if(typeof trendChart !== 'undefined' && trendChart) trendChart.update();
}

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
      <div class="nav-subsection-title" style="padding: 10px 16px; color: #a0aec0; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;">БАЗА ВОЗРАЖЕНИЙ</div>
      <a href="objections_b2c.html" class="nav-item ${activeId === 'obj_b2c' ? 'active' : ''}" title="Физ. лица">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M20 21a8 8 0 0 0-16 0"></path><circle cx="12" cy="7" r="4"></circle></svg></span> B2C
      </a>
      <a href="objections_b2b.html" class="nav-item ${activeId === 'obj_b2b' ? 'active' : ''}" title="Юр. лица">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M3 21h18"></path><path d="M5 21V7l7-4 7 4v14"></path><path d="M9 10h.01"></path><path d="M12 10h.01"></path><path d="M15 10h.01"></path><path d="M9 14h.01"></path><path d="M12 14h.01"></path><path d="M15 14h.01"></path></svg></span> B2B
      </a>

      <div class="nav-subsection-title" style="padding: 10px 16px; color: #a0aec0; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;">ТАКТИЧЕСКИЕ ИНСТРУМЕНТЫ</div>
      <a href="law.html" class="nav-item ${activeId === 'law' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M12 3v18"></path><path d="M5 7h14"></path><path d="M6 7l-3 5h6z"></path><path d="M18 7l-3 5h6z"></path><path d="M8 21h8"></path></svg></span> Нормат. аргументация <span class="nav-badge">Новый</span>
      </a>
      <a href="instruments.html" class="nav-item ${activeId === 'instruments' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M14.7 6.3a3 3 0 0 0-4.2 4.2L3 18l3 3 7.5-7.5a3 3 0 0 0 4.2-4.2l-2.2 2.2-2-2z"></path></svg></span> Инструментарий <span class="nav-badge">Новый</span>
      </a>

      <a href="manual.html" class="nav-item ${activeId === 'manual' ? 'active' : ''}" style="margin-top:10px;">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M4 5a2 2 0 0 1 2-2h13v18H6a2 2 0 0 1-2-2z"></path><path d="M8 7h7"></path><path d="M8 11h7"></path><path d="M8 15h5"></path></svg></span> Мануал <span class="nav-badge">Новый</span>
      </a>

      <div class="nav-section-title" style="margin-top:15px;">РЕГЛАМЕНТ</div>
      <a href="reg_mechanics.html" class="nav-item ${activeId === 'reg_mechanics' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M12 3l9 5-9 5-9-5 9-5z"></path><path d="M3 13l9 5 9-5"></path></svg></span>
        Механика оценки
      </a>
      <a href="reg_methodology.html" class="nav-item ${activeId === 'reg_methodology' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M4 19h16"></path><path d="M7 16V8"></path><path d="M12 16V5"></path><path d="M17 16v-6"></path></svg></span>
        Методология (9 крит.)
      </a>

      <div class="nav-section-title" style="margin-top:15px; font-size:9px;">АРХИТЕКТУРА СВП</div>
      <a href="svp_mechanism.html" class="nav-item ${activeId === 'svp_mechanism' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="2"></circle><circle cx="18" cy="6" r="2"></circle><circle cx="12" cy="18" r="2"></circle><path d="M8 6h8"></path><path d="M7.5 7.5l3.5 8"></path><path d="M16.5 7.5l-3.5 8"></path></svg></span>
        Порядок механизма
      </a>
      <a href="svp_crm.html" class="nav-item ${activeId === 'svp_crm' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="14" rx="2"></rect><path d="M7 8h10"></path><path d="M7 12h6"></path><path d="M9 21h6"></path></svg></span>
        CRM Soft Collection
      </a>

      <div class="nav-section-title" style="margin-top:15px;">РЕГЛАМЕНТ РАБОТЫ QC</div>
      <a href="qc_regulations.html" class="nav-item ${activeId === 'qc_regulations' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M7 3h7l5 5v13H7z"></path><path d="M14 3v5h5"></path><path d="M10 13h8"></path><path d="M10 17h8"></path></svg></span>
        Документ
      </a>

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

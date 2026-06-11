function initSidebar(activeId) {
  const sidebarHtml = `
    <div class="logo" style="display: flex; justify-content: space-between; align-items: center;">
      <div class="logo-text">
        <div class="sidebar-slogan-text">Leaderboard for Soft Collection unit</div>
      </div>
      <div class="hamburger" onclick="toggleSidebar()" style="cursor: pointer; font-size: 20px; color: #f97316;">\u2630</div>
    </div>

    <div style="padding:10px 0; overflow-y: auto; flex: 1; overflow-x:hidden;">
      <div class="nav-section-title">\u041e\u041f\u0415\u0420\u0410\u0426\u0418\u041e\u041d\u041d\u042b\u0415 \u041f\u041e\u041a\u0410\u0417\u0410\u0422\u0415\u041b\u0418</div>
      <a href="analytics.html" class="nav-item ${activeId === 'analytics' ? 'active' : ''}">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg></span>
        \u0410\u043d\u0430\u043b\u0438\u0442\u0438\u043a\u0430
      </a>
      <a href="rating.html" class="nav-item ${activeId === 'rating' ? 'active' : ''}">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg></span>
        \u0420\u0435\u0439\u0442\u0438\u043d\u0433
      </a>
      <a href="forecast.html" class="nav-item ${activeId === 'forecast' ? 'active' : ''}">
        <span class="nav-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg></span>
        \u041f\u0440\u043e\u0433\u043d\u043e\u0437\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435
      </a>

      <div class="nav-section-title" style="margin-top:15px;">\u041e\u041f\u0415\u0420\u0410\u0426\u0418\u041e\u041d\u041d\u042b\u0415 \u0418\u041d\u0421\u0422\u0420\u0423\u041c\u0415\u041d\u0422\u042b</div>

      <div class="nav-subsection-title" style="padding: 10px 16px; color: #a0aec0; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;">\u0411\u0410\u0417\u0410 \u0412\u041e\u0417\u0420\u0410\u0416\u0415\u041d\u0418\u0419</div>
      <a href="objections_b2c.html" class="nav-item ${activeId === 'obj_b2c' ? 'active' : ''}" title="\u0424\u0438\u0437. \u043b\u0438\u0446\u0430">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M20 21a8 8 0 0 0-16 0"></path><circle cx="12" cy="7" r="4"></circle></svg></span> B2C
      </a>
      <a href="objections_b2b.html" class="nav-item ${activeId === 'obj_b2b' ? 'active' : ''}" title="\u042e\u0440. \u043b\u0438\u0446\u0430">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M3 21h18"></path><path d="M5 21V7l7-4 7 4v14"></path><path d="M9 10h.01"></path><path d="M12 10h.01"></path><path d="M15 10h.01"></path><path d="M9 14h.01"></path><path d="M12 14h.01"></path><path d="M15 14h.01"></path></svg></span> B2B
      </a>

      <div class="nav-section-title" style="margin-top:15px;">\u0422\u0410\u041a\u0422\u0418\u0427\u0415\u0421\u041a\u0418\u0415 \u0418\u041d\u0421\u0422\u0420\u0423\u041c\u0415\u041d\u0422\u042b</div>
      <a href="law.html" class="nav-item ${activeId === 'law' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M12 3v18"></path><path d="M5 7h14"></path><path d="M6 7l-3 5h6z"></path><path d="M18 7l-3 5h6z"></path><path d="M8 21h8"></path></svg></span> \u041d\u043e\u0440\u043c\u0430\u0442. \u0430\u0440\u0433\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u044f
      </a>
      <a href="instruments.html" class="nav-item ${activeId === 'instruments' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M14.7 6.3a3 3 0 0 0-4.2 4.2L3 18l3 3 7.5-7.5a3 3 0 0 0 4.2-4.2l-2.2 2.2-2-2z"></path></svg></span> \u0418\u043d\u0441\u0442\u0440\u0443\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439
      </a>
      <a href="manual.html" class="nav-item ${activeId === 'manual' ? 'active' : ''}" style="margin-top:10px;">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M4 5a2 2 0 0 1 2-2h13v18H6a2 2 0 0 1-2-2z"></path><path d="M8 7h7"></path><path d="M8 11h7"></path><path d="M8 15h5"></path></svg></span> \u041c\u0430\u043d\u0443\u0430\u043b
      </a>

      <div class="nav-section-title" style="margin-top:15px;">\u0420\u0415\u0413\u041b\u0410\u041c\u0415\u041d\u0422</div>
      <a href="reg_mechanics.html" class="nav-item ${activeId === 'reg_mechanics' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M12 3l9 5-9 5-9-5 9-5z"></path><path d="M3 13l9 5 9-5"></path></svg></span>
        \u041c\u0435\u0445\u0430\u043d\u0438\u043a\u0430 \u043e\u0446\u0435\u043d\u043a\u0438
      </a>
      <a href="reg_methodology.html" class="nav-item ${activeId === 'reg_methodology' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M4 19h16"></path><path d="M7 16V8"></path><path d="M12 16V5"></path><path d="M17 16v-6"></path></svg></span>
        \u041c\u0435\u0442\u043e\u0434\u043e\u043b\u043e\u0433\u0438\u044f (9 \u043a\u0440\u0438\u0442.)
      </a>

      <div class="nav-section-title" style="margin-top:15px; font-size:9px;">\u0410\u0420\u0425\u0418\u0422\u0415\u041a\u0422\u0423\u0420\u0410 \u0421\u0412\u041f</div>
      <a href="svp_mechanism.html" class="nav-item ${activeId === 'svp_mechanism' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="2"></circle><circle cx="18" cy="6" r="2"></circle><circle cx="12" cy="18" r="2"></circle><path d="M8 6h8"></path><path d="M7.5 7.5l3.5 8"></path><path d="M16.5 7.5l-3.5 8"></path></svg></span>
        \u041f\u043e\u0440\u044f\u0434\u043e\u043a \u043c\u0435\u0445\u0430\u043d\u0438\u0437\u043c\u0430
      </a>
      <a href="svp_crm.html" class="nav-item ${activeId === 'svp_crm' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="14" rx="2"></rect><path d="M7 8h10"></path><path d="M7 12h6"></path><path d="M9 21h6"></path></svg></span>
        CRM Soft Collection
      </a>

      <div class="nav-section-title" style="margin-top:15px;">\u0420\u0415\u0413\u041b\u0410\u041c\u0415\u041d\u0422 \u0420\u0410\u0411\u041e\u0422\u042b QC</div>
      <a href="qc_regulations.html" class="nav-item ${activeId === 'qc_regulations' ? 'active' : ''}">
        <span class="nav-icon"><svg viewBox="0 0 24 24"><path d="M7 3h7l5 5v13H7z"></path><path d="M14 3v5h5"></path><path d="M10 13h8"></path><path d="M10 17h8"></path></svg></span>
        \u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442
      </a>
    </div>

    <div style="margin-top:auto;padding:12px 16px;border-top:1px solid #2d3748;" class="bottom-info">
      <div style="display:flex;align-items:center;gap:10px;">
        <img src="logo/New_logo1.1.jpg" alt="Логотип организации" class="sidebar-org-logo">
        <div class="bottom-text">
          <div style="font-size:10px;color:#94a3b8;font-weight:600;">\u0424\u0435\u0432\u0440\u0430\u043b\u044c\u2013\u0410\u043f\u0440\u0435\u043b\u044c 2026</div>
          <div style="font-size:9px;color:#4a5568;margin-top:1px;">Soft Collection Unit</div>
        </div>
      </div>
    </div>
  `;
  document.getElementById('sidebar').innerHTML = sidebarHtml;

  // Intercept nav-item clicks: stamp current theme + sidebar state onto the URL
  // so the next page loads in exactly the right visual state from first paint.
  document.getElementById('sidebar').addEventListener('click', function(e) {
    const a = e.target.closest('a.nav-item');
    if (!a || !a.href) return;
    const theme = document.body.classList.contains('light-mode') ? 'light' : 'dark';
    const isCollapsed = document.getElementById('sidebar').classList.contains('collapsed');
    try {
      const url = new URL(a.href, window.location.href);
      url.searchParams.set('theme', theme);
      url.searchParams.set('sidebar', isCollapsed ? 'collapsed' : 'expanded');
      a.href = url.toString();
    } catch (err) { /* skip if URL is invalid */ }
    // Normal navigation proceeds — no preventDefault
  });
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const main = document.getElementById('main');

  // Kill transitions momentarily to prevent flicker on toggle
  sidebar.style.transition = 'none';
  main.style.transition = 'none';

  const isCollapsed = sidebar.classList.toggle('collapsed');
  main.classList.toggle('collapsed');

  // Re-enable transitions on the next paint cycle
  requestAnimationFrame(function() {
    requestAnimationFrame(function() {
      sidebar.style.transition = '';
      main.style.transition = '';
    });
  });

  const state = isCollapsed ? 'collapsed' : 'expanded';
  localStorage.setItem('sc-sidebar', state);
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('sidebar', state);
    window.history.replaceState({}, '', url);
  } catch (err) {}
}

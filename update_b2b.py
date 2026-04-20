import json
import re

with open('b2b_data.json', 'r', encoding='utf-8') as f:
    b2b = json.load(f)

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update HTML Search bar
old_search = """<div class="page-sub">20 кейсов · Интерактивный поиск · Скриптовая база · СВП · Правовая база</div>
      <input class="search-box" id="objSearch" placeholder="<svg width=" 18" height="18" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
        style="vertical-align:middle;margin-right:4px;">
      <circle cx="11" cy="11" r="8"></circle>
      <line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> Введите ключевое слово..." oninput="filterObj()">"""

new_search = """<div class="page-sub">Интерактивный поиск · Скриптовая база · СВП · Правовая база</div>
      <div style="display:flex; gap: 10px; margin-bottom: 20px;">
        <button id="btn-b2c" class="cat-tab active" onclick="setObjMode('B2C')">Физ. лица (B2C)</button>
        <button id="btn-b2b" class="cat-tab" style="background:rgba(234,179,8,0.1); border-color:#eab308; color:#facc15;" onclick="setObjMode('B2B')">Юр. лица (B2B)</button>
      </div>
      <div style="position:relative; margin-bottom: 20px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="position:absolute; top:12px; left:14px; color:#94a3b8;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input class="search-box" id="objSearch" placeholder="Введите ключевое слово..." style="padding-left: 40px; margin-bottom: 0;" oninput="filterObj()">
      </div>"""

html = html.replace(old_search, new_search)

# 2. Add B2B arrays
b2b_svp_str = json.dumps(b2b['svp'], ensure_ascii=False)
b2b_laws_str = json.dumps(b2b['laws'], ensure_ascii=False)
b2b_obj_str = json.dumps(b2b['obj'], ensure_ascii=False, indent=2)

arrays_injection = f"""
    const SVP_STAGES_B2B = {b2b_svp_str};
    const LAWS_B2B = {b2b_laws_str};
    const OBJECTIONS_B2B = {b2b_obj_str};
    let currentObjMode = 'B2C';

    function setObjMode(mode) {{
      currentObjMode = mode;
      document.getElementById('btn-b2c').className = 'cat-tab' + (mode === 'B2C' ? ' active' : '');
      document.getElementById('btn-b2b').className = 'cat-tab' + (mode === 'B2B' ? ' active' : '');
      document.getElementById('btn-b2b').style.background = mode === 'B2B' ? '#eab308' : 'rgba(234,179,8,0.1)';
      document.getElementById('btn-b2b').style.color = mode === 'B2B' ? '#0f1117' : '#facc15';
      
      currentCat = 'Все';
      renderSVP();
      renderLaws();
      renderCatTabs();
      renderObjList();
    }}
"""

html = re.sub(r'(const OBJECTIONS = \[.*?\];)', r'\1\n' + arrays_injection, html, flags=re.DOTALL)

# 3. Update get/render functions
html = re.sub(
    r'SVP_STAGES_REG\.forEach\(\(s,\s*i\)\s*=>\s*\{',
    r'const svpData = currentObjMode === \'B2C\' ? SVP_STAGES_REG : SVP_STAGES_B2B; svpData.forEach((s, i) => {',
    html
)
html = html.replace("const c = document.getElementById('svpContainer');", "const c = document.getElementById('svpContainer'); c.innerHTML = '';")

html = re.sub(
    r'LAWS\.forEach\(\(l,\s*i\)\s*=>\s*\{(?!=)',
    r'const lawData = currentObjMode === \'B2C\' ? LAWS : LAWS_B2B; lawData.forEach((l, i) => {',
    html
)
html = html.replace("const g = document.getElementById('lawGrid');", "const g = document.getElementById('lawGrid'); g.innerHTML = '';")

# Replace openLawModal to dynamically use current array instead of LAWS
html = re.sub(
    r'const l = LAWS\[i\];',
    r'const l = currentObjMode === \'B2C\' ? LAWS[i] : LAWS_B2B[i];',
    html
)

# Cat Tabs counting
html = re.sub(
    r'const cnt = cat === \'Все\' \? OBJECTIONS\.length : OBJECTIONS\.filter\(o => o\.cat === cat\)\.length;',
    r'const objData = currentObjMode === \'B2C\' ? OBJECTIONS : OBJECTIONS_B2B; const cnt = cat === \'Все\' ? objData.length : objData.filter(o => o.cat === cat).length;',
    html
)

# Filtering logic
html = re.sub(
    r'const filtered = OBJECTIONS\.filter\(o =>',
    r'const objData = currentObjMode === \'B2C\' ? OBJECTIONS : OBJECTIONS_B2B; const filtered = objData.filter(o =>',
    html
)

html = html.replace("из ' + OBJECTIONS.length + ' кейсов", "из ' + objData.length + ' кейсов")

# Fix openLawByName
new_openlaw = """function openLawByName(name) {
      const idx = (currentObjMode === 'B2C' ? LAWS : LAWS_B2B).findIndex(l => l.art.includes(name));
      if (idx !== -1) { showSection('reglament'); setTimeout(() => openLawModal(idx), 300); }
    }"""
html = re.sub(r'function openLawByName\(name\).*?\} \} \}', new_openlaw + ' }', html, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Injection Complete!')

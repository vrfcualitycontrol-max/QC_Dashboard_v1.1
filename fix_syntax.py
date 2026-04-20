with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Fix the escaped quotes that break Javascript syntax
# currentObjMode === \'B2C\' -> currentObjMode === 'B2C'
html = html.replace(r"\'B2C\'", "'B2C'")

# 2. Fully replace openLawByName manually
old_func = "function openLawByName(name) { const map = { 'Ст. 236': 0, 'Ст. 237': 1, 'Ст. 333': 2, 'Ст. 421': 3 }; const idx = map[name]; if (idx !== undefined) { showSection('reglament'); setTimeout(() => openLawModal(idx), 300); } }"

new_func = """function openLawByName(name) {
      const lawData = currentObjMode === 'B2C' ? LAWS : LAWS_B2B;
      const idx = lawData.findIndex(l => l.art.includes(name));
      if (idx !== -1) { showSection('reglament'); setTimeout(() => openLawModal(idx), 300); }
    }"""

if old_func in html:
    html = html.replace(old_func, new_func)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Fixed syntax errors in index.html!')

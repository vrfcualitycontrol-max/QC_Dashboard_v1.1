import re

# Clean up app.js by removing DATA START/END
with open("assets/js/app.js", "r", encoding="utf-8") as f:
    app_content = f.read()

app_content = re.sub(r'// --- DATA START ---.*?// --- DATA END ---', '', app_content, flags=re.DOTALL)

with open("assets/js/app.js", "w", encoding="utf-8") as f:
    f.write(app_content)

# Update auto_updater.py
with open("auto_updater.py", "r", encoding="utf-8") as f:
    updater = f.read()

updater = updater.replace('INDEX_HTML_PATH = SCRIPT_DIR / "index.html"', 'INDEX_HTML_PATH = SCRIPT_DIR / "assets" / "js" / "data.js"')

with open("auto_updater.py", "w", encoding="utf-8") as f:
    f.write(updater)

print("Cleanup complete.")

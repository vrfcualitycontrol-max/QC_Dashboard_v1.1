import re

content = open("index.html", "r", encoding="utf-8").read()

# Extract styles
style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
if style_match:
    with open("assets/css/style.css", "w", encoding="utf-8") as f:
        f.write(style_match.group(1))

# Extract DATA START/END
data_match = re.search(r'(// --- DATA START ---.*?// --- DATA END ---)', content, re.DOTALL)
if data_match:
    with open("assets/js/data.js", "w", encoding="utf-8") as f:
        f.write(data_match.group(1))

# Extract logic scripts
script_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
if script_match:
    with open("assets/js/app.js", "w", encoding="utf-8") as f:
        f.write(script_match.group(1))

print("Extraction complete.")

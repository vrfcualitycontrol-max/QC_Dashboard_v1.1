import re

js_path = 'assets/js/tactical-pages.js'
with open(js_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken string literals
content = content.replace(
    "html += '<ul style=\"margin:6px 0 12px 18px;color:${thmC('#cbd5e1', '#3f3f46')};line-height:1.6;font-size:13px;\">';",
    "html += `<ul style=\"margin:6px 0 12px 18px;color:${thmC('#cbd5e1', '#3f3f46')};line-height:1.6;font-size:13px;\">`;"
)

content = content.replace(
    "html += '<div style=\"overflow-x:auto;margin:8px 0 14px;\"><table style=\"width:100%;border-collapse:collapse;font-size:12px;color:${thmC('#cbd5e1', '#3f3f46')};\"><thead><tr>';",
    "html += `<div style=\"overflow-x:auto;margin:8px 0 14px;\"><table style=\"width:100%;border-collapse:collapse;font-size:12px;color:${thmC('#cbd5e1', '#3f3f46')};\"><thead><tr>`;"
)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed syntax errors!")

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix the escaped quotes that break Javascript syntax
html = html.replace(r"\'Все\'", "'Все'")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Fixed Все quotes!')

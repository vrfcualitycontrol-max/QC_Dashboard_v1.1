with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

if 'id="btn-b2b"' in text:
    print('Buttons injected!')
else:
    print('Buttons MISSING!')

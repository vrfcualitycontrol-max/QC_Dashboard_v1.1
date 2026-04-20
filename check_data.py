import re
import json

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'const DASHBOARD_DATA = (\{.*?\});\n// --- DATA END ---', html, re.DOTALL)
if m:
    data_str = m.group(1)
    print("Length of DASHBOARD_DATA string:", len(data_str))
    try:
        data = json.loads(data_str)
        print("Successfully parsed as JSON. Number of employees:", len(data.keys()))
        first_emp = list(data.keys())[0]
        print("First employee name:", repr(first_emp))
        print("Months for first employee:", list(data[first_emp]['months'].keys()))
    except Exception as e:
        print("Failed to parse JSON!")
        print(e)
else:
    print('const DASHBOARD_DATA not found.')

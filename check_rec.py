import json
import re

content = open('index.html', encoding='utf-8').read()
match = re.search(r'const DASHBOARD_DATA = ({.*?});', content, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    print("Checking for recommendations in 13-19.04 period:\n")
    # Проверить, есть ли рекомендации для периода 13-19
    found_period = False
    for emp_name, emp_data in list(data.items()):
        for month, month_data in emp_data.get('months', {}).items():
            for period in month_data.get('periods', []):
                if '13-19' in str(period.get('period', '')):
                    found_period = True
                    rec = period.get('rec', '')
                    print(f"Employee: {emp_name}")
                    print(f"  Period: {period['period']}")
                    print(f"  Recommendations length: {len(rec)}")
                    if rec:
                        print(f"  Sample: {rec[:150]}...")
                    else:
                        print(f"  ⚠️ NO RECOMMENDATIONS FOUND")
                    print()
    
    if not found_period:
        print("❌ Period 13-19.04 not found in data at all!")
else:
    print("❌ Could not find DASHBOARD_DATA in index.html")

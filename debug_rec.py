#!/usr/bin/env python3
import re
import pdfplumber
from pathlib import Path

pdf_file = list(Path('reports').glob('*13-19*.pdf'))[0]
with pdfplumber.open(pdf_file) as pdf:
    text = '\n'.join(page.extract_text() or '' for page in pdf.pages)

# Find first employee's recommendations section
parts = re.split(r'Отчет\s+по\s+сотруднику\s*[:：]', text, flags=re.IGNORECASE)
section = parts[2]  # First employee after title

# Extract from 'Рекомендации'
pattern = re.search(r'Рекомендации[^:]*:', section, flags=re.IGNORECASE)
if pattern:
    start = pattern.end()
    remaining = section[start:]
    # Show next 800 chars
    print('Raw text after "Рекомендации:"')
    print(remaining[:800])
    print('\n--- NEXT SECTION MARKERS ---')
    
    # Look for next section markers
    markers = re.finditer(r'\n\d+\.', remaining)
    for i, marker in enumerate(markers):
        if i < 3:
            print(f"Marker {i+1} at position {marker.start()}: {repr(remaining[marker.start():marker.start()+10])}")

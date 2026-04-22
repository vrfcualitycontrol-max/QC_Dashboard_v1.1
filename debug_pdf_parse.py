#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from pathlib import Path
import pdfplumber

REPORTS_DIR = Path(__file__).parent / "reports"

def extract_pdf_sections(text: str):
    parts = re.split(r"Отчет\s+по\s+сотруднику\s*[:：]", text, flags=re.IGNORECASE)
    return [part.strip() for part in parts if part.strip()]

def extract_section_text(block: str, key: str) -> str:
    pattern = re.search(fr"{re.escape(key)}\s*[:：]?\s*(.*)", block, flags=re.IGNORECASE)
    if pattern:
        return pattern.group(1).strip().replace("\n", " ")
    return ""

def extract_month_and_period(filename: str):
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})", filename)
    if match:
        period = f"{match.group(1)}-{match.group(4)}"
        return period
    return "Неизвестно"

# Test PDF parsing
pdf_file = list(REPORTS_DIR.glob("*13-19*.pdf"))[0]
print(f"Testing PDF: {pdf_file.name}\n")

period = extract_month_and_period(pdf_file.name)
print(f"Period extracted: {period}\n")

with pdfplumber.open(pdf_file) as pdf:
    text = "\n".join(page.extract_text() or "" for page in pdf.pages)

print(f"Total text length: {len(text)} chars\n")

sections = extract_pdf_sections(text)
print(f"Found {len(sections)} sections\n")

# Test first 2 sections
for i, section in enumerate(sections[:2]):
    print(f"=== SECTION {i+1} ===")
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    
    if lines:
        employee = lines[0]
        print(f"Employee: {employee}")
        print(f"Section length: {len(section)} chars")
        
        # Extract different patterns
        tendencies = extract_section_text(section, "Тенденции")
        rec1 = extract_section_text(section, "Рекомендации")
        rec2 = extract_section_text(section, "Рекомендации для Лида")
        
        print(f"\nExtract 'Тенденции': {len(tendencies)} chars")
        if tendencies:
            print(f"  Sample: {tendencies[:100]}...")
        
        print(f"Extract 'Рекомендации': {len(rec1)} chars")
        if rec1:
            print(f"  Sample: {rec1[:100]}...")
        else:
            print("  NOT FOUND")
        
        print(f"Extract 'Рекомендации для Лида': {len(rec2)} chars")
        if rec2:
            print(f"  Sample: {rec2[:100]}...")
        else:
            print("  NOT FOUND")
        
        # Show actual lines containing "рекомендац"
        print("\nLines containing 'рекомендац':")
        for line in lines:
            if 'рекомендац' in line.lower():
                print(f"  → {line[:100]}")
    
    print()

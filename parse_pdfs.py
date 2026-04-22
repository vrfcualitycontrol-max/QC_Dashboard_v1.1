import pdfplumber
import os

pdfs = [
    "Архитектура структуры ведения переговоров (СВП).pdf",
    "МЕХАНИКА ОЦЕНКИ КАЧЕСТВА ПЕРЕГОВОРОВ 2026.pdf",
    "Правила работы с системой CRM при взыскании задолженности на ранней стадии Soft Collection 1.1.pdf",
    "РЕГЛАМЕНТ РАБОТЫ ОТДЕЛА QUALITY CONTROL v2.0..pdf"
]

for pdf_path in pdfs:
    print(f"--- {pdf_path} ---")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            print(f"Length: {len(text)} chars")
            print(text[:1000])
            print("...[truncated]...\n")
    except Exception as e:
        import traceback
        traceback.print_exc()

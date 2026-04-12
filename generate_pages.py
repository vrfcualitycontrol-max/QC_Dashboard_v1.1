#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор HTML-страниц для QC Dashboard v1.2.2
Создает страницы из шаблона includes/template.html
"""

from pathlib import Path

BASE = Path(__file__).parent
TEMPLATE = BASE / "includes" / "template.html"
SIDEBAR = BASE / "includes" / "sidebar.html"

# Определение всех страниц
PAGES = [
    # Главная — приветственный лендинг (создаётся отдельно)
    
    # Аналитика
    ("summary.html", "Сводка", "Обзорные метрики команды, лидерборд и ключевые показатели качества."),
    ("heatmap.html", "SVP Heatmap Pro", "Тепловая карта выработки по 9 критериям СВП с алгоритмом диагнозов."),
    ("analytics.html", "Аналитика", "История, сравнение периодов, тренды и прогнозирование качества."),
    ("employees.html", "Сотрудники", "Персональные профили, рекомендации и корреляция TQS/AHT."),
    
    # Инструменты — B2C
    ("tools/b2c/objections.html", "B2C · Отработка возражений", "Справочник техник отработки возражений для B2C сегмента."),
    ("tools/b2c/regulations.html", "B2C · Нормативная аргументация", "Договор, оферта и нормативно-правовые акты для B2C."),
    
    # Инструменты — B2B
    ("tools/b2b/objections.html", "B2B · Отработка возражений", "Справочник техник отработки возражений для B2B сегмента."),
    ("tools/b2b/regulations.html", "B2B · Нормативная аргументация", "Договор, оферта и нормативно-правовые акты для B2B."),
    
    # Инструменты — Тактика
    ("tools/tactics/overview.html", "Тактические инструменты", "Обзор тактических инструментов ведения переговоров."),
    ("tools/tactics/argumentation.html", "Аргументация", "Методы и техники аргументации в диалоге."),
    ("tools/tactics/manipulation.html", "Манипуляция", "Техники манипуляции в переговорах."),
    ("tools/tactics/legending.html", "Легендирование", "Методы легендирования при работе с должниками."),
    ("tools/tactics/requirements.html", "Выставление требований", "Правила и техники выставления требований."),
    ("tools/tactics/summary.html", "Подведение итогов", "Техники подведения итогов диалога."),
    
    # Регламент
    ("regulations/qc-rules.html", "Правила оценивания QC", "Нормативная база и правила оценивания качества."),
    ("regulations/evaluation.html", "Механика оценки качества", "Методология оценивания по 9 критериям СВП."),
    ("regulations/svp.html", "Архитектура СВП", "Порядок механизма ведения переговоров."),
    ("regulations/crm.html", "CRM Soft Collection", "Правила работы с системой CRM."),
    ("regulations/qc-charter.html", "Устав QC отдела", "Регламент работы отдела Quality Control."),
    
    # Настройки
    ("settings.html", "Настройки", "Загрузка файлов, логи парсинга, статус системы."),
]


def generate_page(filename: str, title: str, description: str):
    """Генерирует HTML-файл страницы из шаблона"""
    template = TEMPLATE.read_text(encoding="utf-8")
    sidebar = SIDEBAR.read_text(encoding="utf-8")
    
    content = template.replace("{{TITLE}}", title)
    content = content.replace("{{DESCRIPTION}}", description)
    content = content.replace("{{SIDEBAR}}", sidebar)
    
    # Корректировка пути к логотипу для вложенных страниц
    depth = filename.count("/")
    if depth > 0:
        prefix = "../" * depth
        content = content.replace('src="../New logo1.1.png"', f'src="{prefix}New logo1.1.png"')
        content = content.replace('href="../', f'href="{prefix}')
        content = content.replace("href='../", f"href='{prefix}")
    
    filepath = BASE / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    print(f"✅ {filename} — {title}")


def main():
    print("=" * 60)
    print("QC Dashboard v1.2.2 — Генератор страниц")
    print("=" * 60)
    
    for filename, title, description in PAGES:
        generate_page(filename, title, description)
    
    print(f"\n✅ Сгенерировано {len(PAGES)} страниц")


if __name__ == "__main__":
    main()

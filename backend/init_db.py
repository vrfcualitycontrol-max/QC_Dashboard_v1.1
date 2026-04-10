#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт инициализации БД - создание индексов и представлений
Запускается автоматически при старте контейнера
"""

import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://qc_user:qc_password@postgres:5432/qc_dashboard"
)

def init_database():
    """Создание индексов и представлений"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("✅ Создание индексов...")
        
        # Индексы
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_employee_scores_name ON employee_scores(employee_name)",
            "CREATE INDEX IF NOT EXISTS idx_employee_scores_period ON employee_scores(period)",
            "CREATE INDEX IF NOT EXISTS idx_employee_scores_created ON employee_scores(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_pdf_recommendations_name ON pdf_recommendations(employee_name)",
            "CREATE INDEX IF NOT EXISTS idx_parsing_logs_status ON parsing_logs(status)",
            "CREATE INDEX IF NOT EXISTS idx_parsing_logs_parsed_at ON parsing_logs(parsed_at)"
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                conn.commit()
                print(f"  ✅ {index_sql.split(' ON ')[1].split('(')[0] if ' ON ' in index_sql else 'index'}")
            except Exception as e:
                print(f"  ⚠️  Пропущено: {e}")
        
        print("\n✅ Создание представлений...")
        
        # Представление для leaderboard
        leaderboard_view = """
        CREATE OR REPLACE VIEW leaderboard_view AS
        SELECT 
            employee_name,
            ROUND(AVG(tqs), 4) as avg_tqs,
            ROUND(AVG(CASE WHEN aht > 0 THEN aht END), 2) as avg_aht,
            SUM(activity_count) as total_activity,
            COUNT(DISTINCT period) as periods_count
        FROM employee_scores
        GROUP BY employee_name
        ORDER BY avg_tqs DESC
        """
        
        try:
            conn.execute(text(leaderboard_view))
            conn.commit()
            print("  ✅ leaderboard_view")
        except Exception as e:
            print(f"  ⚠️  leaderboard_view: {e}")
        
        # Представление для трендов по периодам
        period_trends = """
        CREATE OR REPLACE VIEW period_trends AS
        SELECT 
            period,
            ROUND(AVG(tqs), 4) as avg_tqs,
            ROUND(AVG(CASE WHEN aht > 0 THEN aht END), 2) as avg_aht,
            SUM(activity_count) as total_activity,
            COUNT(DISTINCT employee_name) as employees_count
        FROM employee_scores
        GROUP BY period
        ORDER BY period
        """
        
        try:
            conn.execute(text(period_trends))
            conn.commit()
            print("  ✅ period_trends")
        except Exception as e:
            print(f"  ⚠️  period_trends: {e}")
        
        print("\n✅ Инициализация БД завершена!")

if __name__ == "__main__":
    init_database()

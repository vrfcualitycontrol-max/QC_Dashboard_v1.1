-- Инициализация БД QC Dashboard
-- Создание дополнительных индексов для оптимизации

CREATE INDEX IF NOT EXISTS idx_employee_scores_name ON employee_scores(employee_name);
CREATE INDEX IF NOT EXISTS idx_employee_scores_period ON employee_scores(period);
CREATE INDEX IF NOT EXISTS idx_employee_scores_created ON employee_scores(created_at);

CREATE INDEX IF NOT EXISTS idx_pdf_recommendations_name ON pdf_recommendations(employee_name);

CREATE INDEX IF NOT EXISTS idx_parsing_logs_status ON parsing_logs(status);
CREATE INDEX IF NOT EXISTS idx_parsing_logs_parsed_at ON parsing_logs(parsed_at);

-- Представление для leaderboard
CREATE OR REPLACE VIEW leaderboard_view AS
SELECT 
    employee_name,
    ROUND(AVG(tqs), 4) as avg_tqs,
    ROUND(AVG(aht), 2) as avg_aht,
    SUM(activity_count) as total_activity,
    COUNT(DISTINCT period) as periods_count
FROM employee_scores
GROUP BY employee_name
ORDER BY avg_tqs DESC;

-- Представление для трендов по периодам
CREATE OR REPLACE VIEW period_trends AS
SELECT 
    period,
    ROUND(AVG(tqs), 4) as avg_tqs,
    ROUND(AVG(CASE WHEN aht > 0 THEN aht END), 2) as avg_aht,
    SUM(activity_count) as total_activity,
    COUNT(DISTINCT employee_name) as employees_count
FROM employee_scores
GROUP BY period
ORDER BY period;

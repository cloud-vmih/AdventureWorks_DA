-- Views for Chapter 1: Business Health
CREATE OR REPLACE VIEW mart.vw_ch1_quota_quarterly AS
SELECT 
    calendar_year, 
    calendar_quarter, 
    CAST(calendar_year AS VARCHAR) || 'Q' || CAST(calendar_quarter AS VARCHAR) AS quarter_key,
    SUM(sales_amount_quota) AS total_quota,
    AVG(sales_amount_quota) AS avg_quota
FROM dwh.fact_sales_quota
GROUP BY calendar_year, calendar_quarter
ORDER BY calendar_year, calendar_quarter;

CREATE OR REPLACE VIEW mart.vw_ch1_employee_quota AS
SELECT
    q.employee_key,
    e.first_name || ' ' || e.last_name AS employee_name,
    e.job_title,
    SUM(q.sales_amount_quota) AS quota
FROM dwh.fact_sales_quota q
LEFT JOIN dwh.dim_employee e ON q.employee_key = e.employee_key
GROUP BY q.employee_key, e.first_name, e.last_name, e.job_title
ORDER BY quota DESC;

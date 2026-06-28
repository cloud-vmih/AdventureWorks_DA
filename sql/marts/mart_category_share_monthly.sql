-- Data Mart: Category Share Monthly
CREATE TABLE IF NOT EXISTS mart.mart_category_share_monthly (
    month_key VARCHAR(8),
    territory_id INT,
    category_name VARCHAR(100),
    revenue NUMERIC,
    total_revenue NUMERIC,
    category_share NUMERIC
);

TRUNCATE TABLE mart.mart_category_share_monthly;

INSERT INTO mart.mart_category_share_monthly (
    month_key, territory_id, category_name,
    revenue, total_revenue, category_share
)
SELECT
    month_key,
    territory_id,
    category_name,
    SUM(revenue) as revenue,
    SUM(SUM(revenue)) OVER (PARTITION BY month_key, territory_id) as total_revenue,
    CASE
        WHEN SUM(SUM(revenue)) OVER (PARTITION BY month_key, territory_id) > 0
        THEN SUM(revenue) / SUM(SUM(revenue)) OVER (PARTITION BY month_key, territory_id)
        ELSE 0
    END as category_share
FROM mart.mart_sales_kpi_monthly
GROUP BY month_key, territory_id, category_name
ORDER BY month_key, territory_id, category_name;

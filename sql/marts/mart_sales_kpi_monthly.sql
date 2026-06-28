-- Data Mart Sales Monthly script
CREATE TABLE IF NOT EXISTS mart.mart_sales_kpi_monthly (
    month_key VARCHAR(8),
    territory_id INT,
    territory_group VARCHAR(50),
    country_code VARCHAR(3),
    channel VARCHAR(10),
    category_name VARCHAR(100),
    revenue NUMERIC,
    cogs NUMERIC,
    gross_profit NUMERIC,
    gross_margin NUMERIC,
    orders INT,
    quantity INT
);

TRUNCATE TABLE mart.mart_sales_kpi_monthly;

INSERT INTO mart.mart_sales_kpi_monthly (
    month_key, territory_id, territory_group, country_code, channel,
    category_name, revenue, cogs, gross_profit, gross_margin, orders, quantity
)
SELECT
    TO_CHAR(f.order_date, 'YYYYMM') as month_key,
    f.territory_id,
    COALESCE(t.territory_group, 'Unknown') as territory_group,
    COALESCE(t.country_code, 'Unknown') as country_code,
    CASE WHEN f.online_order_flag = true THEN 'B2C' ELSE 'B2B' END as channel,
    COALESCE(p.category_name, 'Unknown') as category_name,
    SUM(f.line_total) as revenue,
    SUM(f.total_product_cost) as cogs,
    SUM(f.gross_profit) as gross_profit,
    CASE
        WHEN SUM(f.line_total) > 0 THEN SUM(f.gross_profit) / SUM(f.line_total)
        ELSE 0
    END as gross_margin,
    COUNT(DISTINCT f.sales_order_number) as orders,
    SUM(f.order_qty) as quantity
FROM dwh.fact_internet_sales f
LEFT JOIN dwh.dim_product p ON f.product_key = p.product_key
LEFT JOIN dwh.dim_sales_territory t ON f.territory_id = t.territory_id
GROUP BY
    TO_CHAR(f.order_date, 'YYYYMM'),
    f.territory_id,
    t.territory_group,
    t.country_code,
    f.online_order_flag,
    p.category_name;

-- Data Mart Sales Monthly script
CREATE TABLE IF NOT EXISTS mart.mart_sales_kpi_monthly (
    month_key VARCHAR(6),
    territory_id INT,
    channel VARCHAR(10), -- 'B2C' (Online) or 'B2B' (Reseller)
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
    month_key, territory_id, channel, category_name, revenue, cogs, gross_profit, gross_margin, orders, quantity
)
SELECT 
    TO_CHAR(f.order_date, 'YYYYMM') as month_key,
    f.territory_id,
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
GROUP BY 
    TO_CHAR(f.order_date, 'YYYYMM'),
    f.territory_id,
    f.online_order_flag,
    p.category_name;

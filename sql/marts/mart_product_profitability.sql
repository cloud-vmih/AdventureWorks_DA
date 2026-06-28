-- Data Mart Product Profitability script
CREATE TABLE IF NOT EXISTS mart.mart_product_profitability (
    month_key VARCHAR(6),
    product_key INT,
    product_name VARCHAR(100),
    category_name VARCHAR(100),
    subcategory_name VARCHAR(100),
    units_sold INT,
    revenue NUMERIC,
    total_standard_cost NUMERIC,
    gross_profit NUMERIC,
    gross_margin NUMERIC,
    avg_unit_price NUMERIC,
    avg_discount_rate NUMERIC
);

TRUNCATE TABLE mart.mart_product_profitability;

INSERT INTO mart.mart_product_profitability (
    month_key, product_key, product_name, category_name, subcategory_name,
    units_sold, revenue, total_standard_cost, gross_profit, gross_margin,
    avg_unit_price, avg_discount_rate
)
SELECT
    TO_CHAR(f.order_date, 'YYYYMM') as month_key,
    p.product_key,
    p.product_name,
    p.category_name,
    p.subcategory_name,
    SUM(f.order_qty) as units_sold,
    SUM(f.line_total) as revenue,
    SUM(f.total_product_cost) as total_standard_cost,
    SUM(f.gross_profit) as gross_profit,
    CASE
        WHEN SUM(f.line_total) > 0 THEN SUM(f.gross_profit) / SUM(f.line_total)
        ELSE 0
    END as gross_margin,
    AVG(f.unit_price) as avg_unit_price,
    AVG(f.unit_price_discount) as avg_discount_rate
FROM dwh.fact_internet_sales f
LEFT JOIN dwh.dim_product p ON f.product_key = p.product_key
GROUP BY
    TO_CHAR(f.order_date, 'YYYYMM'),
    p.product_key,
    p.product_name,
    p.category_name,
    p.subcategory_name;

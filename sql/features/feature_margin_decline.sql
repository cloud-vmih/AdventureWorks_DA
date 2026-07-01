CREATE SCHEMA IF NOT EXISTS feature;

CREATE TABLE IF NOT EXISTS feature.margin_decline_features (
    month_key VARCHAR(6),
    territory_id INT,
    product_key INT,
    category_name VARCHAR(100),
    subcategory_name VARCHAR(100),
    gross_margin NUMERIC,
    gross_margin_lag_1 NUMERIC,
    gross_margin_lag_2 NUMERIC,
    revenue NUMERIC,
    total_standard_cost NUMERIC,
    avg_unit_price NUMERIC,
    avg_discount_rate NUMERIC,
    cpi NUMERIC,
    interest_rate NUMERIC
);

TRUNCATE TABLE feature.margin_decline_features;

WITH margin_monthly AS (
    SELECT
        TO_CHAR(f.order_date, 'YYYYMM') AS month_key,
        f.territory_id AS territory_id,
        p.product_key,
        p.category_name,
        p.subcategory_name,
        SUM(f.line_total) AS revenue,
        SUM(f.total_product_cost) AS total_standard_cost,
        CASE
            WHEN SUM(f.line_total) > 0 THEN SUM(f.gross_profit) / SUM(f.line_total)
            ELSE 0
        END AS gross_margin,
        AVG(f.unit_price) AS avg_unit_price,
        AVG(f.unit_price_discount) AS avg_discount_rate
    FROM dwh.fact_internet_sales f
    JOIN dwh.dim_product p ON f.product_key = p.product_key
    GROUP BY
        TO_CHAR(f.order_date, 'YYYYMM'),
        f.territory_id,
        p.product_key,
        p.category_name,
        p.subcategory_name
),
macro_monthly AS (
    SELECT
        LEFT(m.month_key, 6) AS month_key,
        t.territory_id,
        m.cpi,
        m.interest_rate
    FROM dwh.fact_macro_economic_monthly m
    JOIN dwh.dim_sales_territory t ON m.territory_key = t.territory_key
),
base AS (
    SELECT
        mm.month_key,
        mm.territory_id,
        mm.product_key,
        mm.category_name,
        mm.subcategory_name,
        mm.gross_margin,
        mm.revenue,
        mm.total_standard_cost,
        mm.avg_unit_price,
        mm.avg_discount_rate,
        COALESCE(m.cpi, 0) AS cpi,
        COALESCE(m.interest_rate, 0) AS interest_rate
    FROM margin_monthly mm
    LEFT JOIN macro_monthly m ON mm.month_key = m.month_key AND mm.territory_id = m.territory_id
)
INSERT INTO feature.margin_decline_features
SELECT
    month_key,
    territory_id,
    product_key,
    category_name,
    subcategory_name,
    gross_margin,
    LAG(gross_margin, 1) OVER(PARTITION BY product_key, territory_id ORDER BY month_key) AS gross_margin_lag_1,
    LAG(gross_margin, 2) OVER(PARTITION BY product_key, territory_id ORDER BY month_key) AS gross_margin_lag_2,
    revenue,
    total_standard_cost,
    avg_unit_price,
    avg_discount_rate,
    cpi,
    interest_rate
FROM base;

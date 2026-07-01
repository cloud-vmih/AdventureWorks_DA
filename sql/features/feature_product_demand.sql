CREATE SCHEMA IF NOT EXISTS feature;

CREATE TABLE IF NOT EXISTS feature.product_demand_features (
    month_key VARCHAR(6),
    territory_id INT,
    product_key INT,
    category_name VARCHAR(100),
    subcategory_name VARCHAR(100),
    current_inventory INT,
    units_sold INT,
    units_sold_lag_1 INT,
    units_sold_lag_2 INT,
    units_sold_lag_3 INT,
    units_sold_lag_12 INT,
    revenue NUMERIC,
    cpi NUMERIC,
    interest_rate NUMERIC
);

TRUNCATE TABLE feature.product_demand_features;

WITH sales_monthly AS (
    SELECT
        TO_CHAR(f.order_date, 'YYYYMM') AS month_key,
        f.territory_id AS territory_id,
        p.product_key,
        p.category_name,
        p.subcategory_name,
        SUM(f.order_qty) AS units_sold,
        SUM(f.line_total) AS revenue
    FROM dwh.fact_internet_sales f
    JOIN dwh.dim_product p ON f.product_key = p.product_key
    GROUP BY
        TO_CHAR(f.order_date, 'YYYYMM'),
        f.territory_id,
        p.product_key,
        p.category_name,
        p.subcategory_name
),
inventory_latest AS (
    -- Get the latest snapshot of inventory per product (global across DWH)
    SELECT
        product_key,
        SUM(quantity) AS current_inventory
    FROM dwh.fact_inventory
    GROUP BY product_key
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
        s.month_key,
        s.territory_id,
        s.product_key,
        s.category_name,
        s.subcategory_name,
        COALESCE(i.current_inventory, 0) AS current_inventory,
        s.units_sold,
        s.revenue,
        COALESCE(m.cpi, 0) AS cpi,
        COALESCE(m.interest_rate, 0) AS interest_rate
    FROM sales_monthly s
    LEFT JOIN inventory_latest i ON s.product_key = i.product_key
    LEFT JOIN macro_monthly m ON s.month_key = m.month_key AND s.territory_id = m.territory_id
)
INSERT INTO feature.product_demand_features
SELECT
    month_key,
    territory_id,
    product_key,
    category_name,
    subcategory_name,
    current_inventory,
    units_sold,
    LAG(units_sold, 1) OVER(PARTITION BY product_key, territory_id ORDER BY month_key) AS units_sold_lag_1,
    LAG(units_sold, 2) OVER(PARTITION BY product_key, territory_id ORDER BY month_key) AS units_sold_lag_2,
    LAG(units_sold, 3) OVER(PARTITION BY product_key, territory_id ORDER BY month_key) AS units_sold_lag_3,
    LAG(units_sold, 12) OVER(PARTITION BY product_key, territory_id ORDER BY month_key) AS units_sold_lag_12,
    revenue,
    cpi,
    interest_rate
FROM base;

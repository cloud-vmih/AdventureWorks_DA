DROP TABLE IF EXISTS mart.mart_inventory_risk;

CREATE TABLE mart.mart_inventory_risk AS

WITH sales AS (
    SELECT
        p.product_key,
        p.product_name,
        p.category_name,
        p.subcategory_name,

        SUM(f.order_qty) AS units_sold,
        SUM(f.line_total) AS revenue,
        SUM(f.total_product_cost) AS cogs,
        SUM(f.gross_profit) AS gross_profit,

        CASE
            WHEN SUM(f.line_total) = 0 THEN NULL
            ELSE SUM(f.gross_profit) / SUM(f.line_total)
        END AS gross_margin

    FROM dwh.fact_internet_sales f
    LEFT JOIN dwh.dim_product p
        ON f.product_key = p.product_key

    GROUP BY
        p.product_key,
        p.product_name,
        p.category_name,
        p.subcategory_name
),

inventory AS (
    SELECT
        product_key,
        SUM(quantity) AS current_inventory_qty,
        AVG(quantity) AS avg_inventory_qty,
        MAX(quantity) AS max_inventory_qty,
        MIN(quantity) AS min_inventory_qty,
        COUNT(*) AS inventory_records
    FROM dwh.fact_inventory
    GROUP BY product_key
),

base AS (
    SELECT
        COALESCE(s.product_key, i.product_key) AS product_key,

        COALESCE(s.product_name, p.product_name) AS product_name,
        COALESCE(s.category_name, p.category_name) AS category_name,
        COALESCE(s.subcategory_name, p.subcategory_name) AS subcategory_name,

        COALESCE(s.units_sold, 0) AS units_sold,
        COALESCE(s.revenue, 0) AS revenue,
        COALESCE(s.cogs, 0) AS cogs,
        COALESCE(s.gross_profit, 0) AS gross_profit,
        s.gross_margin,

        COALESCE(i.current_inventory_qty, 0) AS current_inventory_qty,
        COALESCE(i.avg_inventory_qty, 0) AS avg_inventory_qty,
        COALESCE(i.max_inventory_qty, 0) AS max_inventory_qty,
        COALESCE(i.min_inventory_qty, 0) AS min_inventory_qty,
        COALESCE(i.inventory_records, 0) AS inventory_records

    FROM sales s
    FULL OUTER JOIN inventory i
        ON s.product_key = i.product_key
    LEFT JOIN dwh.dim_product p
        ON COALESCE(s.product_key, i.product_key) = p.product_key
)

SELECT
    product_key,
    product_name,
    category_name,
    subcategory_name,

    units_sold,
    revenue,
    cogs,
    gross_profit,
    gross_margin,

    current_inventory_qty,
    avg_inventory_qty,
    max_inventory_qty,
    min_inventory_qty,
    inventory_records,

    CASE
        WHEN current_inventory_qty = 0 THEN NULL
        ELSE units_sold / current_inventory_qty
    END AS inventory_turnover_qty,

    CASE
        WHEN units_sold = 0 AND current_inventory_qty > 0 THEN NULL
        ELSE current_inventory_qty / NULLIF(units_sold, 0) * 30
    END AS days_inventory_proxy,

    CASE
        WHEN units_sold = 0 AND current_inventory_qty > 0 THEN 'No Demand - Overstock Risk'
        WHEN units_sold > 0 AND current_inventory_qty = 0 THEN 'Demand - Low Inventory'
        WHEN current_inventory_qty > 0 AND units_sold / NULLIF(current_inventory_qty, 0) < 0.5 THEN 'Slow Moving'
        WHEN current_inventory_qty > 0 AND units_sold / NULLIF(current_inventory_qty, 0) >= 0.5 THEN 'Healthy'
        ELSE 'Unknown'
    END AS inventory_risk_status

FROM base;
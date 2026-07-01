DROP TABLE IF EXISTS mart.mart_product_profitability_monthly;

CREATE TABLE mart.mart_product_profitability_monthly AS

SELECT

    TO_CHAR(f.order_date,'YYYYMM') AS month_key,

    t.territory_id,
    t.territory_group,
    t.country_code,

    CASE
        WHEN f.online_order_flag = TRUE THEN 'B2C'
        ELSE 'B2B'
    END AS channel,

    p.product_key,
    p.product_name,
    p.category_name,
    p.subcategory_name,

    COUNT(DISTINCT f.sales_order_number) AS orders,

    SUM(f.order_qty) AS quantity,

    SUM(f.line_total) AS revenue,

    SUM(f.total_product_cost) AS cogs,

    SUM(f.gross_profit) AS gross_profit,

    CASE
        WHEN SUM(f.line_total)=0 THEN NULL
        ELSE SUM(f.gross_profit)/SUM(f.line_total)
    END AS gross_margin,

    AVG(f.unit_price) AS avg_unit_price,

    AVG(f.unit_price_discount) AS avg_discount_rate,

    AVG(f.standard_cost) AS avg_standard_cost

FROM dwh.fact_internet_sales f

LEFT JOIN dwh.dim_product p
ON f.product_key=p.product_key

LEFT JOIN dwh.dim_sales_territory t
ON f.territory_id=t.territory_id

GROUP BY

    TO_CHAR(f.order_date,'YYYYMM'),

    t.territory_id,
    t.territory_group,
    t.country_code,

    CASE
        WHEN f.online_order_flag=TRUE THEN 'B2C'
        ELSE 'B2B'
    END,

    p.product_key,
    p.product_name,
    p.category_name,
    p.subcategory_name;
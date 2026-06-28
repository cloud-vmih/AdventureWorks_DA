-- Customer Churn Feature Engineering SQL
CREATE TABLE IF NOT EXISTS feature.customer_churn_features (
    customer_key INT PRIMARY KEY,
    recency INT,
    frequency INT,
    monetary NUMERIC,
    tenure INT,
    avg_discount_rate NUMERIC,
    preferred_territory_id INT,
    preferred_category VARCHAR(100),
    avg_cpi NUMERIC,
    avg_inflation NUMERIC,
    churn_label INT
);

TRUNCATE TABLE feature.customer_churn_features;

-- Sliding window split relative to the maximum date in DWH
-- Behavior window: up to (MaxDate - 6 months)
-- Label window: from (MaxDate - 6 months) to MaxDate
WITH max_date_cte AS (
    SELECT COALESCE(MAX(order_date), CURRENT_TIMESTAMP) as max_date FROM dwh.fact_internet_sales
),
snapshot_cte AS (
    SELECT (max_date - INTERVAL '6 months') as snapshot_date FROM max_date_cte
),
behavior_cte AS (
    SELECT
        f.customer_key,
        EXTRACT(DAY FROM (s.snapshot_date - MAX(f.order_date))) as recency,
        COUNT(DISTINCT f.sales_order_number) as frequency,
        SUM(f.line_total) as monetary,
        EXTRACT(DAY FROM (s.snapshot_date - MIN(f.order_date))) as tenure,
        AVG(f.unit_price_discount) as avg_discount_rate,
        -- Most common territory
        MODE() WITHIN GROUP (ORDER BY f.territory_id) as preferred_territory_id
    FROM dwh.fact_internet_sales f
    CROSS JOIN snapshot_cte s
    WHERE f.order_date <= s.snapshot_date
    GROUP BY f.customer_key, s.snapshot_date
),
label_cte AS (
    SELECT DISTINCT customer_key
    FROM dwh.fact_internet_sales f
    CROSS JOIN snapshot_cte s
    WHERE f.order_date > s.snapshot_date
),
customer_category AS (
    SELECT
        f.customer_key,
        MODE() WITHIN GROUP (ORDER BY p.category_name) as preferred_category
    FROM dwh.fact_internet_sales f
    LEFT JOIN dwh.dim_product p ON f.product_key = p.product_key
    GROUP BY f.customer_key
),
customer_macro AS (
    SELECT
        f.customer_key,
        AVG(m.cpi) as avg_cpi,
        AVG(m.inflation) as avg_inflation
    FROM dwh.fact_internet_sales f
    LEFT JOIN dwh.dim_sales_territory t ON f.territory_id = t.territory_id
    LEFT JOIN dwh.fact_macro_economic_monthly m
        ON t.territory_key = m.territory_key
        AND TO_CHAR(f.order_date, 'YYYYMM') = m.month_key
    GROUP BY f.customer_key
)
INSERT INTO feature.customer_churn_features (
    customer_key, recency, frequency, monetary, tenure, avg_discount_rate,
    preferred_territory_id, preferred_category, avg_cpi, avg_inflation, churn_label
)
SELECT
    b.customer_key,
    COALESCE(b.recency, 9999)::INT as recency,
    b.frequency::INT,
    b.monetary,
    b.tenure::INT,
    b.avg_discount_rate,
    b.preferred_territory_id,
    cc.preferred_category,
    cm.avg_cpi,
    cm.avg_inflation,
    CASE WHEN l.customer_key IS NOT NULL THEN 0 ELSE 1 END as churn_label
FROM behavior_cte b
LEFT JOIN label_cte l ON b.customer_key = l.customer_key
LEFT JOIN customer_category cc ON b.customer_key = cc.customer_key
LEFT JOIN customer_macro cm ON b.customer_key = cm.customer_key;

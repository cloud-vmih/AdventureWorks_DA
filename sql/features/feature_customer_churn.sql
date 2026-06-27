-- Customer Churn Feature Engineering SQL
CREATE TABLE IF NOT EXISTS feature.customer_churn_features (
    customer_key INT PRIMARY KEY,
    recency INT,
    frequency INT,
    monetary NUMERIC,
    tenure INT,
    avg_discount_rate NUMERIC,
    churn_label INT
);

TRUNCATE TABLE feature.customer_churn_features;

-- Use a sliding window split relative to the maximum date in DWH to label churn cleanly without leakage.
-- Behavior window: up to (MaxDate - 6 months)
-- Label window: from (MaxDate - 6 months) to MaxDate (6-month churn horizon)
WITH max_date_cte AS (
    SELECT COALESCE(MAX(order_date), CURRENT_TIMESTAMP) as max_date FROM dwh.fact_internet_sales
),
snapshot_cte AS (
    SELECT (max_date - INTERVAL '6 months') as snapshot_date FROM max_date_cte
),
behavior_cte AS (
    SELECT 
        f.customer_key,
        -- Recency: Days from last purchase to snapshot_date
        EXTRACT(DAY FROM (s.snapshot_date - MAX(f.order_date))) as recency,
        -- Frequency: count of distinct orders
        COUNT(DISTINCT f.sales_order_number) as frequency,
        -- Monetary: sum line_total
        SUM(f.line_total) as monetary,
        -- Tenure: Days from first purchase to snapshot_date
        EXTRACT(DAY FROM (s.snapshot_date - MIN(f.order_date))) as tenure,
        -- Average discount rate
        AVG(f.unit_price_discount) as avg_discount_rate
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
)
INSERT INTO feature.customer_churn_features (customer_key, recency, frequency, monetary, tenure, avg_discount_rate, churn_label)
SELECT 
    b.customer_key,
    COALESCE(b.recency, 9999)::INT as recency,
    b.frequency::INT,
    b.monetary,
    b.tenure::INT,
    b.avg_discount_rate,
    -- If they have purchases in the label window, churn_label = 0 (loyal), otherwise 1 (churned)
    CASE WHEN l.customer_key IS NOT NULL THEN 0 ELSE 1 END as churn_label
FROM behavior_cte b
LEFT JOIN label_cte l ON b.customer_key = l.customer_key;

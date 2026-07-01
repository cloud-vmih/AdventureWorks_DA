CREATE TABLE IF NOT EXISTS dwh.fact_customer_rfm_snapshot (
    rfm_key SERIAL PRIMARY KEY,
    customer_key INT REFERENCES dwh.dim_customer(customer_key),
    snapshot_date_key INT REFERENCES dwh.dim_date(date_key),
    recency_days INT,
    frequency_count INT,
    monetary_amount NUMERIC
);

TRUNCATE TABLE dwh.fact_customer_rfm_snapshot;

WITH monthly_snapshots AS (
    SELECT GENERATE_SERIES(
        DATE_TRUNC('month', MIN(order_date))::DATE,
        DATE_TRUNC('month', MAX(order_date))::DATE,
        '1 month'::INTERVAL
    )::DATE as snapshot_date
    FROM dwh.fact_internet_sales
),
customer_first AS (
    SELECT customer_key, MIN(order_date::DATE) as first_order_date
    FROM dwh.fact_internet_sales
    GROUP BY customer_key
),
customer_months AS (
    SELECT
        cf.customer_key,
        m.snapshot_date
    FROM monthly_snapshots m
    JOIN customer_first cf ON m.snapshot_date >= cf.first_order_date
)
INSERT INTO dwh.fact_customer_rfm_snapshot (
    customer_key, snapshot_date_key, recency_days, frequency_count, monetary_amount
)
SELECT
    cm.customer_key,
    (EXTRACT(YEAR FROM cm.snapshot_date) * 10000 + EXTRACT(MONTH FROM cm.snapshot_date) * 100 + 1)::INT as snapshot_date_key,
    COALESCE((cm.snapshot_date - MAX(f.order_date::DATE)), 999) as recency_days,
    COUNT(DISTINCT f.sales_order_number)::INT as frequency_count,
    COALESCE(SUM(f.line_total), 0) as monetary_amount
FROM customer_months cm
LEFT JOIN dwh.fact_internet_sales f
    ON cm.customer_key = f.customer_key
    AND f.order_date::DATE <= cm.snapshot_date
GROUP BY cm.customer_key, cm.snapshot_date
ORDER BY cm.customer_key, cm.snapshot_date;

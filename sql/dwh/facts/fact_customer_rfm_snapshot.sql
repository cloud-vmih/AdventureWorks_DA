CREATE TABLE IF NOT EXISTS dwh.fact_customer_rfm_snapshot (
    rfm_key SERIAL PRIMARY KEY,
    customer_key INT REFERENCES dwh.dim_customer(customer_key),
    snapshot_date_key INT REFERENCES dwh.dim_date(date_key),
    recency_days INT,
    frequency_count INT,
    monetary_amount NUMERIC
);

TRUNCATE TABLE dwh.fact_customer_rfm_snapshot;

WITH max_date AS (
    SELECT MAX(order_date)::DATE as last_date FROM dwh.fact_internet_sales
)
INSERT INTO dwh.fact_customer_rfm_snapshot (customer_key, snapshot_date_key, recency_days, frequency_count, monetary_amount)
SELECT
    f.customer_key,
    (EXTRACT(YEAR FROM md.last_date) * 10000 + EXTRACT(MONTH FROM md.last_date) * 100 + EXTRACT(DAY FROM md.last_date))::INT as snapshot_date_key,
    (md.last_date - MAX(f.order_date::DATE))::INT as recency_days,
    COUNT(DISTINCT f.sales_order_number)::INT as frequency_count,
    SUM(f.line_total) as monetary_amount
FROM dwh.fact_internet_sales f
CROSS JOIN max_date md
GROUP BY f.customer_key, md.last_date;

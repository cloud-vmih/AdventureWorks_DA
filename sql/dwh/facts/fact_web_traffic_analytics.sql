CREATE TABLE IF NOT EXISTS dwh.fact_web_traffic_analytics (
    traffic_key SERIAL PRIMARY KEY,
    customer_key INT REFERENCES dwh.dim_customer(customer_key),
    date_key INT REFERENCES dwh.dim_date(date_key),
    session_duration INT,
    pages_visited INT,
    device_type VARCHAR(20),
    bounce_rate NUMERIC
);

TRUNCATE TABLE dwh.fact_web_traffic_analytics;

WITH customer_dates AS (
    SELECT DISTINCT f.customer_key, d.date_key, d.full_date
    FROM dwh.fact_internet_sales f
    LEFT JOIN dwh.dim_date d ON f.order_date::DATE = d.full_date
)
INSERT INTO dwh.fact_web_traffic_analytics (customer_key, date_key, session_duration, pages_visited, device_type, bounce_rate)
SELECT
    cd.customer_key,
    cd.date_key,
    (30 + (random() * 570)::INT) as session_duration,
    (2 + (random() * 18)::INT) as pages_visited,
    CASE (random() * 2)::INT
        WHEN 0 THEN 'Desktop'
        WHEN 1 THEN 'Mobile'
        ELSE 'Tablet'
    END as device_type,
    (random() * 0.7)::NUMERIC(3,2) as bounce_rate
FROM customer_dates cd
WHERE random() < 0.3;

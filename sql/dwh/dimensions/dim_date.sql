CREATE TABLE IF NOT EXISTS dwh.dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    week_of_year INT NOT NULL
);

TRUNCATE TABLE dwh.dim_date CASCADE;

INSERT INTO dwh.dim_date (date_key, full_date, year, quarter, month, month_name, day_of_month, day_of_week, day_name, week_of_year)
SELECT
    EXTRACT(YEAR FROM d.d) * 10000 + EXTRACT(MONTH FROM d.d) * 100 + EXTRACT(DAY FROM d.d) as date_key,
    d.d::DATE as full_date,
    EXTRACT(YEAR FROM d.d)::INT as year,
    EXTRACT(QUARTER FROM d.d)::INT as quarter,
    EXTRACT(MONTH FROM d.d)::INT as month,
    TO_CHAR(d.d, 'Month') as month_name,
    EXTRACT(DAY FROM d.d)::INT as day_of_month,
    EXTRACT(DOW FROM d.d)::INT as day_of_week,
    TO_CHAR(d.d, 'Day') as day_name,
    EXTRACT(WEEK FROM d.d)::INT as week_of_year
FROM generate_series('2021-01-01'::DATE, '2025-12-31'::DATE, '1 day') d(d);

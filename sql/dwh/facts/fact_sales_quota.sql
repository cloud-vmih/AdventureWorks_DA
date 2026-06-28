CREATE TABLE IF NOT EXISTS dwh.fact_sales_quota (
    quota_key SERIAL PRIMARY KEY,
    employee_key INT REFERENCES dwh.dim_employee(employee_key),
    date_key INT REFERENCES dwh.dim_date(date_key),
    calendar_year INT,
    calendar_quarter INT,
    sales_amount_quota NUMERIC
);

TRUNCATE TABLE dwh.fact_sales_quota;

INSERT INTO dwh.fact_sales_quota (employee_key, date_key, calendar_year, calendar_quarter, sales_amount_quota)
SELECT
    e.employee_key,
    d.date_key,
    EXTRACT(YEAR FROM sqh.quotadate)::INT as calendar_year,
    EXTRACT(QUARTER FROM sqh.quotadate)::INT as calendar_quarter,
    sqh.salesquota as sales_amount_quota
FROM staging.salespersonquotahistory sqh
LEFT JOIN dwh.dim_employee e ON sqh.businessentityid = e.employee_id
LEFT JOIN dwh.dim_date d ON sqh.quotadate::DATE = d.full_date;

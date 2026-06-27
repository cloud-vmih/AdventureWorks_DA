-- Revenue Forecast Feature Engineering SQL
CREATE TABLE IF NOT EXISTS feature.revenue_forecast_features (
    month_key VARCHAR(6),
    territory_id INT,
    country_code VARCHAR(3),
    revenue NUMERIC,
    revenue_lag_1 NUMERIC,
    revenue_lag_2 NUMERIC,
    cpi NUMERIC,
    interest_rate NUMERIC,
    oil_price NUMERIC,
    exchange_rate NUMERIC
);

TRUNCATE TABLE feature.revenue_forecast_features;

-- Aggregate sales to monthly territory levels, generate revenue lags, and join with macroeconomic factors.
WITH monthly_sales AS (
    SELECT 
        month_key,
        territory_id,
        SUM(revenue) as revenue
    FROM mart.mart_sales_kpi_monthly
    GROUP BY month_key, territory_id
),
lags AS (
    SELECT 
        month_key,
        territory_id,
        revenue,
        LAG(revenue, 1) OVER (PARTITION BY territory_id ORDER BY month_key) as revenue_lag_1,
        LAG(revenue, 2) OVER (PARTITION BY territory_id ORDER BY month_key) as revenue_lag_2
    FROM monthly_sales
),
territory_map AS (
    SELECT 
        territoryid as territory_id,
        countryregioncode as country_code
    FROM staging.salesterritory
)
INSERT INTO feature.revenue_forecast_features (
    month_key, territory_id, country_code, revenue, revenue_lag_1, revenue_lag_2, cpi, interest_rate, oil_price, exchange_rate
)
SELECT 
    l.month_key,
    l.territory_id,
    tm.country_code,
    l.revenue,
    COALESCE(l.revenue_lag_1, 0) as revenue_lag_1,
    COALESCE(l.revenue_lag_2, 0) as revenue_lag_2,
    COALESCE(c.cpi, 100.0) as cpi,
    COALESCE(i.interest_rate, 2.0) as interest_rate,
    COALESCE(o.oil_price, 60.0) as oil_price,
    COALESCE(e.exchange_rate, 1.0) as exchange_rate
FROM lags l
JOIN territory_map tm ON l.territory_id = tm.territory_id
LEFT JOIN staging.macro_cpi c ON l.month_key = c.month_key AND tm.country_code = c.country_code
LEFT JOIN staging.macro_interest_rate i ON l.month_key = i.month_key AND tm.country_code = i.country_code
LEFT JOIN staging.macro_oil_price o ON l.month_key = o.month_key
LEFT JOIN staging.macro_exchange_rate e ON l.month_key = e.month_key AND tm.country_code = e.country_code
WHERE l.revenue_lag_1 IS NOT NULL AND l.revenue_lag_2 IS NOT NULL; -- Exclude first 2 months where lags are missing

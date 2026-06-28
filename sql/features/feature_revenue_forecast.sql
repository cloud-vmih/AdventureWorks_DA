-- Revenue Forecast Feature Engineering SQL
CREATE TABLE IF NOT EXISTS feature.revenue_forecast_features (
    month_key VARCHAR(6),
    territory_id INT,
    country_code VARCHAR(3),
    revenue NUMERIC,
    revenue_lag_1 NUMERIC,
    revenue_lag_2 NUMERIC,
    gdp NUMERIC,
    cpi NUMERIC,
    inflation NUMERIC,
    interest_rate NUMERIC,
    oil_price NUMERIC,
    exchange_rate NUMERIC,
    population NUMERIC,
    income NUMERIC
);

TRUNCATE TABLE feature.revenue_forecast_features;

-- Aggregate sales to monthly territory levels, generate revenue lags, join with macro economic factors.
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
)
INSERT INTO feature.revenue_forecast_features (
    month_key, territory_id, country_code,
    revenue, revenue_lag_1, revenue_lag_2,
    gdp, cpi, inflation, interest_rate, oil_price, exchange_rate,
    population, income
)
SELECT
    l.month_key,
    l.territory_id,
    COALESCE(t.country_code, 'Unknown') as country_code,
    l.revenue,
    COALESCE(l.revenue_lag_1, 0) as revenue_lag_1,
    COALESCE(l.revenue_lag_2, 0) as revenue_lag_2,
    COALESCE(m.gdp, 0) as gdp,
    COALESCE(m.cpi, 100.0) as cpi,
    COALESCE(m.inflation, 0) as inflation,
    COALESCE(m.interest_rate, 2.0) as interest_rate,
    COALESCE(m.oil_price, 60.0) as oil_price,
    COALESCE(m.exchange_rate, 1.0) as exchange_rate,
    COALESCE(m.population, 0) as population,
    COALESCE(m.income, 0) as income
FROM lags l
LEFT JOIN dwh.dim_sales_territory t ON l.territory_id = t.territory_id
LEFT JOIN dwh.fact_macro_economic_monthly m
    ON t.territory_key = m.territory_key
    AND l.month_key = m.month_key
WHERE l.revenue_lag_1 IS NOT NULL AND l.revenue_lag_2 IS NOT NULL;

-- Data Mart Macro Monthly script
CREATE TABLE IF NOT EXISTS mart.mart_macro_monthly (
    month_key VARCHAR(6),
    territory_id INT,
    country_code VARCHAR(3),
    gdp NUMERIC,
    income NUMERIC,
    population NUMERIC,
    cpi NUMERIC,
    inflation NUMERIC,
    interest_rate NUMERIC,
    oil_price NUMERIC,
    exchange_rate NUMERIC
);

TRUNCATE TABLE mart.mart_macro_monthly;

INSERT INTO mart.mart_macro_monthly (
    month_key, territory_id, country_code,
    gdp, income, population, cpi, inflation,
    interest_rate, oil_price, exchange_rate
)
SELECT
    m.month_key,
    t.territory_id,
    m.country_code,
    m.gdp,
    m.income,
    m.population,
    m.cpi,
    m.inflation,
    m.interest_rate,
    m.oil_price,
    m.exchange_rate
FROM dwh.fact_macro_economic_monthly m
LEFT JOIN dwh.dim_sales_territory t ON m.territory_key = t.territory_key
ORDER BY m.month_key, t.territory_id;

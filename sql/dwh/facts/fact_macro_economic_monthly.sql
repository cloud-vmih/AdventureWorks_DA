CREATE TABLE IF NOT EXISTS dwh.fact_macro_economic_monthly (
    month_key VARCHAR(6),
    territory_key INT REFERENCES dwh.dim_sales_territory(territory_key),
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

TRUNCATE TABLE dwh.fact_macro_economic_monthly;

INSERT INTO dwh.fact_macro_economic_monthly (
    month_key, territory_key, country_code,
    gdp, income, population, cpi, inflation,
    interest_rate, oil_price, exchange_rate
)
SELECT
    TO_CHAR(m.date::date, 'YYYYMM') as month_key,
    t.territory_key,
    m.country_code,
    m.gdp,
    m.income,
    m.population,
    m.cpi,
    m.inflation,
    m.interest_rate,
    m.oil_price,
    m.exchange_rate
FROM staging.macro_territory_monthly m
LEFT JOIN dwh.dim_sales_territory t ON m.territoryid = t.territory_id;

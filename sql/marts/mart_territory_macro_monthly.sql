-- Data Mart: Territory × Month — Sales + Macro combined
CREATE TABLE IF NOT EXISTS mart.mart_territory_macro_monthly (
    month_key VARCHAR(8),
    territory_id INT,
    territory_group VARCHAR(50),
    country_code VARCHAR(3),
    revenue NUMERIC,
    cogs NUMERIC,
    gross_profit NUMERIC,
    orders INT,
    quantity INT,
    gdp NUMERIC,
    income NUMERIC,
    population NUMERIC,
    cpi NUMERIC,
    inflation NUMERIC,
    interest_rate NUMERIC,
    oil_price NUMERIC,
    exchange_rate NUMERIC
);

TRUNCATE TABLE mart.mart_territory_macro_monthly;

INSERT INTO mart.mart_territory_macro_monthly (
    month_key, territory_id, territory_group, country_code,
    revenue, cogs, gross_profit, orders, quantity,
    gdp, income, population, cpi, inflation,
    interest_rate, oil_price, exchange_rate
)
SELECT
    s.month_key,
    s.territory_id,
    MAX(s.territory_group) as territory_group,
    MAX(s.country_code) as country_code,
    SUM(s.revenue) as revenue,
    SUM(s.cogs) as cogs,
    SUM(s.gross_profit) as gross_profit,
    SUM(s.orders) as orders,
    SUM(s.quantity) as quantity,
    MAX(m.gdp) as gdp,
    MAX(m.income) as income,
    MAX(m.population) as population,
    MAX(m.cpi) as cpi,
    MAX(m.inflation) as inflation,
    MAX(m.interest_rate) as interest_rate,
    MAX(m.oil_price) as oil_price,
    MAX(m.exchange_rate) as exchange_rate
FROM mart.mart_sales_kpi_monthly s
LEFT JOIN mart.mart_macro_monthly m ON s.month_key = m.month_key AND s.territory_id = m.territory_id
GROUP BY s.month_key, s.territory_id
ORDER BY s.month_key, s.territory_id;

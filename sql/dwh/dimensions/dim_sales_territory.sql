CREATE TABLE IF NOT EXISTS dwh.dim_sales_territory (
    territory_key SERIAL PRIMARY KEY,
    territory_id INT UNIQUE,
    territory_name VARCHAR(50),
    country_code VARCHAR(3),
    territory_group VARCHAR(50)
);

TRUNCATE TABLE dwh.dim_sales_territory CASCADE;

INSERT INTO dwh.dim_sales_territory (territory_id, territory_name, country_code, territory_group)
SELECT
    territoryid as territory_id,
    name as territory_name,
    countryregioncode as country_code,
    "group" as territory_group
FROM staging.salesterritory;

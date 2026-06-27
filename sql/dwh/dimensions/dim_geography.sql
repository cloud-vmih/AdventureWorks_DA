CREATE TABLE IF NOT EXISTS dwh.dim_geography (
    geography_key SERIAL PRIMARY KEY,
    city VARCHAR(30),
    state_province VARCHAR(50),
    state_province_code CHAR(3),
    country_region VARCHAR(50),
    country_region_code VARCHAR(3),
    postal_code VARCHAR(15)
);

TRUNCATE TABLE dwh.dim_geography CASCADE;

INSERT INTO dwh.dim_geography (city, state_province, state_province_code, country_region, country_region_code, postal_code)
SELECT DISTINCT
    a.city,
    sp.name as state_province,
    sp.stateprovincecode as state_province_code,
    cr.name as country_region,
    cr.countryregioncode as country_region_code,
    a.postalcode as postal_code
FROM staging.address a
JOIN staging.stateprovince sp ON a.stateprovinceid = sp.stateprovinceid
JOIN staging.countryregion cr ON sp.countryregioncode = cr.countryregioncode;

CREATE TABLE IF NOT EXISTS dwh.dim_reseller (
    reseller_key SERIAL PRIMARY KEY,
    reseller_id INT UNIQUE,
    reseller_name VARCHAR(100),
    geography_key INT REFERENCES dwh.dim_geography(geography_key),
    sales_person_id INT,
    modified_date TIMESTAMP
);

TRUNCATE TABLE dwh.dim_reseller CASCADE;

WITH store_address AS (
    SELECT DISTINCT ON (s.businessentityid)
        s.businessentityid,
        s.name,
        s.salespersonid,
        s.modifieddate,
        a.city,
        a.postalcode
    FROM staging.store s
    LEFT JOIN staging.businessentityaddress bea ON s.businessentityid = bea.businessentityid
    LEFT JOIN staging.address a ON bea.addressid = a.addressid
    ORDER BY s.businessentityid, bea.addresstypeid
)
INSERT INTO dwh.dim_reseller (reseller_id, reseller_name, geography_key, sales_person_id, modified_date)
SELECT DISTINCT ON (sa.businessentityid)
    sa.businessentityid as reseller_id,
    sa.name as reseller_name,
    g.geography_key,
    sa.salespersonid as sales_person_id,
    sa.modifieddate as modified_date
FROM store_address sa
LEFT JOIN dwh.dim_geography g ON sa.city = g.city AND sa.postalcode = g.postal_code
ORDER BY sa.businessentityid, g.geography_key;

-- Dimension Customer script
CREATE TABLE IF NOT EXISTS dwh.dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id INT UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(200),
    person_type VARCHAR(10),
    email_promotion INT,
    territory_id INT,
    modified_date TIMESTAMP
);

TRUNCATE TABLE dwh.dim_customer RESTART IDENTITY CASCADE;

INSERT INTO dwh.dim_customer (customer_id, first_name, last_name, full_name, person_type, email_promotion, territory_id, modified_date)
SELECT 
    c.customerid as customer_id,
    COALESCE(p.firstname, 'Store') as first_name,
    COALESCE(p.lastname, CAST(c.storeid AS VARCHAR)) as last_name,
    CASE 
        WHEN p.firstname IS NOT NULL THEN p.firstname || ' ' || p.lastname 
        ELSE 'Store Customer #' || c.customerid 
    END as full_name,
    p.persontype as person_type,
    p.emailpromotion as email_promotion,
    c.territoryid as territory_id,
    c.modifieddate as modified_date
FROM staging.customer c
LEFT JOIN staging.person p ON c.personid = p.businessentityid;

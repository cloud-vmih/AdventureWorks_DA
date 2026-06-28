CREATE TABLE IF NOT EXISTS dwh.fact_inventory (
    inventory_key SERIAL PRIMARY KEY,
    product_key INT REFERENCES dwh.dim_product(product_key),
    date_key INT REFERENCES dwh.dim_date(date_key),
    quantity INT,
    shelf VARCHAR(10),
    bin INT
);

TRUNCATE TABLE dwh.fact_inventory;

INSERT INTO dwh.fact_inventory (product_key, date_key, quantity, shelf, bin)
SELECT
    p.product_key,
    d.date_key,
    pi.quantity,
    pi.shelf,
    pi.bin
FROM staging.productinventory pi
LEFT JOIN dwh.dim_product p ON pi.productid = p.product_id
LEFT JOIN dwh.dim_date d ON pi.modifieddate::DATE = d.full_date;

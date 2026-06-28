-- Dimension Product script
CREATE TABLE IF NOT EXISTS dwh.dim_product (
    product_key SERIAL PRIMARY KEY,
    product_id INT UNIQUE,
    product_name VARCHAR(100),
    product_number VARCHAR(50),
    color VARCHAR(50),
    standard_cost NUMERIC,
    list_price NUMERIC,
    size VARCHAR(50),
    weight NUMERIC,
    subcategory_name VARCHAR(100),
    category_name VARCHAR(100),
    modified_date TIMESTAMP
);

TRUNCATE TABLE dwh.dim_product RESTART IDENTITY CASCADE;

INSERT INTO dwh.dim_product (product_id, product_name, product_number, color, standard_cost, list_price, size, weight, subcategory_name, category_name, modified_date)
SELECT 
    p.productid as product_id,
    p.name as product_name,
    p.productnumber as product_number,
    p.color,
    p.standardcost as standard_cost,
    p.listprice as list_price,
    p.size,
    p.weight,
    ps.name as subcategory_name,
    pc.name as category_name,
    p.modifieddate as modified_date
FROM staging.product p
LEFT JOIN staging.productsubcategory ps ON p.productsubcategoryid = ps.productsubcategoryid
LEFT JOIN staging.productcategory pc ON ps.productcategoryid = pc.productcategoryid;

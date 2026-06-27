CREATE TABLE IF NOT EXISTS dwh.dim_product_subcategory (
    subcategory_key SERIAL PRIMARY KEY,
    subcategory_id INT UNIQUE,
    category_key INT REFERENCES dwh.dim_product_category(category_key),
    subcategory_name VARCHAR(100)
);

TRUNCATE TABLE dwh.dim_product_subcategory CASCADE;

INSERT INTO dwh.dim_product_subcategory (subcategory_id, category_key, subcategory_name)
SELECT
    ps.productsubcategoryid as subcategory_id,
    pc.category_key,
    ps.name as subcategory_name
FROM staging.productsubcategory ps
LEFT JOIN dwh.dim_product_category pc ON ps.productcategoryid = pc.category_id;

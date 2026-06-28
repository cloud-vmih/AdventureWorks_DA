CREATE TABLE IF NOT EXISTS dwh.dim_product_category (
    category_key SERIAL PRIMARY KEY,
    category_id INT UNIQUE,
    category_name VARCHAR(100)
);

TRUNCATE TABLE dwh.dim_product_category CASCADE;

INSERT INTO dwh.dim_product_category (category_id, category_name)
SELECT productcategoryid, name FROM staging.productcategory;

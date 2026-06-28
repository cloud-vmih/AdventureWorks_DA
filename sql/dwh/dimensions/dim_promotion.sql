CREATE TABLE IF NOT EXISTS dwh.dim_promotion (
    promotion_key SERIAL PRIMARY KEY,
    promotion_id INT UNIQUE,
    description VARCHAR(255),
    discount_pct NUMERIC,
    type VARCHAR(50),
    category VARCHAR(50),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    min_qty INT,
    max_qty INT
);

TRUNCATE TABLE dwh.dim_promotion CASCADE;

INSERT INTO dwh.dim_promotion (promotion_id, description, discount_pct, type, category, start_date, end_date, min_qty, max_qty)
SELECT
    specialofferid as promotion_id,
    description,
    discountpct as discount_pct,
    type,
    category,
    startdate as start_date,
    enddate as end_date,
    minqty as min_qty,
    maxqty as max_qty
FROM staging.specialoffer;

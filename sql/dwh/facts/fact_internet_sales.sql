-- Fact Internet Sales script
CREATE TABLE IF NOT EXISTS dwh.fact_internet_sales (
    sales_key SERIAL PRIMARY KEY,
    sales_order_number VARCHAR(50),
    sales_order_id INT,
    sales_order_detail_id INT,
    customer_key INT,
    product_key INT,
    order_date TIMESTAMP,
    due_date TIMESTAMP,
    ship_date TIMESTAMP,
    order_qty INT,
    unit_price NUMERIC,
    unit_price_discount NUMERIC,
    line_total NUMERIC,
    standard_cost NUMERIC,
    total_product_cost NUMERIC,
    gross_profit NUMERIC,
    territory_id INT,
    online_order_flag BOOLEAN
);

TRUNCATE TABLE dwh.fact_internet_sales RESTART IDENTITY;

INSERT INTO dwh.fact_internet_sales (
    sales_order_number, sales_order_id, sales_order_detail_id, customer_key, product_key,
    order_date, due_date, ship_date, order_qty, unit_price, unit_price_discount, line_total,
    standard_cost, total_product_cost, gross_profit, territory_id, online_order_flag
)
SELECT 
    'SO' || h.salesorderid as sales_order_number,
    h.salesorderid as sales_order_id,
    d.salesorderdetailid as sales_order_detail_id,
    c.customer_key,
    p.product_key,
    h.orderdate as order_date,
    h.duedate as due_date,
    h.shipdate as ship_date,
    d.orderqty as order_qty,
    d.unitprice as unit_price,
    d.unitpricediscount as unit_price_discount,
    (d.unitprice * (1.0 - d.unitpricediscount) * d.orderqty) as line_total,
    p.standard_cost,
    (p.standard_cost * d.orderqty) as total_product_cost,
    ((d.unitprice * (1.0 - d.unitpricediscount) * d.orderqty) - (p.standard_cost * d.orderqty)) as gross_profit,
    h.territoryid as territory_id,
    h.onlineorderflag as online_order_flag
FROM staging.salesorderheader h
JOIN staging.salesorderdetail d ON h.salesorderid = d.salesorderid
LEFT JOIN dwh.dim_customer c ON h.customerid = c.customer_id
LEFT JOIN dwh.dim_product p ON d.productid = p.product_id;

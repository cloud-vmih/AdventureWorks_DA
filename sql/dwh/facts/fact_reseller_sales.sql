CREATE TABLE IF NOT EXISTS dwh.fact_reseller_sales (
    sales_key SERIAL PRIMARY KEY,
    sales_order_number VARCHAR(50),
    reseller_key INT REFERENCES dwh.dim_reseller(reseller_key),
    product_key INT REFERENCES dwh.dim_product(product_key),
    employee_key INT REFERENCES dwh.dim_employee(employee_key),
    date_key INT REFERENCES dwh.dim_date(date_key),
    order_qty INT,
    unit_price NUMERIC,
    unit_price_discount NUMERIC,
    line_total NUMERIC,
    territory_key INT REFERENCES dwh.dim_sales_territory(territory_key)
);

TRUNCATE TABLE dwh.fact_reseller_sales;

INSERT INTO dwh.fact_reseller_sales (
    sales_order_number, reseller_key, product_key, employee_key, date_key,
    order_qty, unit_price, unit_price_discount, line_total, territory_key
)
SELECT
    'SO' || h.salesorderid as sales_order_number,
    r.reseller_key,
    p.product_key,
    e.employee_key,
    d.date_key,
    det.orderqty as order_qty,
    det.unitprice as unit_price,
    det.unitpricediscount as unit_price_discount,
    (det.unitprice * (1.0 - det.unitpricediscount) * det.orderqty) as line_total,
    t.territory_key
FROM staging.salesorderheader h
JOIN staging.salesorderdetail det ON h.salesorderid = det.salesorderid
JOIN staging.customer c ON h.customerid = c.customerid
JOIN dwh.dim_reseller r ON c.storeid = r.reseller_id
LEFT JOIN dwh.dim_product p ON det.productid = p.product_id
LEFT JOIN dwh.dim_employee e ON h.salespersonid = e.employee_id
LEFT JOIN dwh.dim_date d ON h.orderdate::DATE = d.full_date
LEFT JOIN dwh.dim_sales_territory t ON h.territoryid = t.territory_id
WHERE c.storeid IS NOT NULL;

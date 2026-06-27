-- Clean staging data before moving to DWH schema
-- Delete records with invalid quantities or prices
DELETE FROM staging.salesorderdetail
WHERE orderqty <= 0 OR unitprice < 0;

-- Delete records with missing dates in sales header
DELETE FROM staging.salesorderheader
WHERE orderdate IS NULL;

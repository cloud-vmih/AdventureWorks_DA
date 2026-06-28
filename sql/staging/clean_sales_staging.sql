-- Clean staging data before moving to DWH schema

-- Sales Order: remove invalid quantities or prices
DELETE FROM staging.salesorderdetail
WHERE orderqty <= 0 OR unitprice < 0;

-- Sales Header: remove records with missing dates
DELETE FROM staging.salesorderheader
WHERE orderdate IS NULL;

-- Product: remove invalid prices
DELETE FROM staging.product
WHERE listprice < 0 OR standardcost < 0;

-- Employee: remove records without hire date
DELETE FROM staging.employee
WHERE hiredate IS NULL;

-- SpecialOffer: remove invalid date ranges
DELETE FROM staging.specialoffer
WHERE enddate < startdate;

-- CurrencyRate: remove invalid rates
DELETE FROM staging.currencyrate
WHERE averagerate <= 0;

-- ProductInventory: remove invalid quantities
DELETE FROM staging.productinventory
WHERE quantity < 0;

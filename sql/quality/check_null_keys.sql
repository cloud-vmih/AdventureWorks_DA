-- Data Quality Check SQL Script
-- Run checks to detect null keys, unmatched dimensions, negative values, and duplicates

-- Check 1: Null customer keys in fact_internet_sales
SELECT
    'fact_internet_sales' as table_name,
    'customer_key IS NULL' as check_name,
    COUNT(*) as violation_count
FROM dwh.fact_internet_sales
WHERE customer_key IS NULL

UNION ALL

-- Check 2: Null product keys in fact_internet_sales
SELECT
    'fact_internet_sales' as table_name,
    'product_key IS NULL' as check_name,
    COUNT(*) as violation_count
FROM dwh.fact_internet_sales
WHERE product_key IS NULL

UNION ALL

-- Check 3: Negative line_total in fact_internet_sales
SELECT
    'fact_internet_sales' as table_name,
    'negative line_total' as check_name,
    COUNT(*) as violation_count
FROM dwh.fact_internet_sales
WHERE line_total < 0

UNION ALL

-- Check 4: Unmatched customer_key in fact_internet_sales
SELECT
    'fact_internet_sales' as table_name,
    'unmatched customer_key' as check_name,
    COUNT(f.*) as violation_count
FROM dwh.fact_internet_sales f
LEFT JOIN dwh.dim_customer c ON f.customer_key = c.customer_key
WHERE c.customer_key IS NULL AND f.customer_key IS NOT NULL

UNION ALL

-- Check 5: Null product_key in fact_reseller_sales
SELECT
    'fact_reseller_sales' as table_name,
    'product_key IS NULL' as check_name,
    COUNT(*) as violation_count
FROM dwh.fact_reseller_sales
WHERE product_key IS NULL

UNION ALL

-- Check 6: Unmatched territory_key in fact_macro_economic_monthly
SELECT
    'fact_macro_economic_monthly' as table_name,
    'unmatched territory_key' as check_name,
    COUNT(f.*) as violation_count
FROM dwh.fact_macro_economic_monthly f
LEFT JOIN dwh.dim_sales_territory t ON f.territory_key = t.territory_key
WHERE t.territory_key IS NULL AND f.territory_key IS NOT NULL

UNION ALL

-- Check 7: Null date_key in fact_currency_rate
SELECT
    'fact_currency_rate' as table_name,
    'date_key IS NULL' as check_name,
    COUNT(*) as violation_count
FROM dwh.fact_currency_rate
WHERE date_key IS NULL

UNION ALL

-- Check 8: Duplicate customer_key in dim_customer
SELECT
    'dim_customer' as table_name,
    'duplicate customer_id' as check_name,
    COUNT(*) as violation_count
FROM (
    SELECT customer_id
    FROM dwh.dim_customer
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) dup

UNION ALL

-- Check 9: Duplicate product_id in dim_product
SELECT
    'dim_product' as table_name,
    'duplicate product_id' as check_name,
    COUNT(*) as violation_count
FROM (
    SELECT product_id
    FROM dwh.dim_product
    WHERE product_id IS NOT NULL
    GROUP BY product_id
    HAVING COUNT(*) > 1
) dup

UNION ALL

-- Check 10: Negative order_qty in fact_internet_sales (should be caught by clean but just in case)
SELECT
    'fact_internet_sales' as table_name,
    'negative order_qty' as check_name,
    COUNT(*) as violation_count
FROM dwh.fact_internet_sales
WHERE order_qty < 0;

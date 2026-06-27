-- Data Quality Check SQL Script
-- Run checks to detect null keys, unmatched dimensions, and negative values

-- Check 1: Null customer keys in fact table
SELECT 
    'fact_internet_sales' as table_name,
    'customer_key IS NULL' as check_name,
    COUNT(*) as violation_count
FROM dwh.fact_internet_sales
WHERE customer_key IS NULL

UNION ALL

-- Check 2: Null product keys in fact table
SELECT 
    'fact_internet_sales' as table_name,
    'product_key IS NULL' as check_name,
    COUNT(*) as violation_count
FROM dwh.fact_internet_sales
WHERE product_key IS NULL

UNION ALL

-- Check 3: Negative line totals (revenue)
SELECT 
    'fact_internet_sales' as table_name,
    'negative line_total' as check_name,
    COUNT(*) as violation_count
FROM dwh.fact_internet_sales
WHERE line_total < 0

UNION ALL

-- Check 4: Unmatched customer keys (referential integrity)
SELECT 
    'fact_internet_sales' as table_name,
    'unmatched customer_key' as check_name,
    COUNT(f.*) as violation_count
FROM dwh.fact_internet_sales f
LEFT JOIN dwh.dim_customer c ON f.customer_key = c.customer_key
WHERE c.customer_key IS NULL AND f.customer_key IS NOT NULL;

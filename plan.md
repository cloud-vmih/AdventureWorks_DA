# Plan: Rewrite ETL Core + Phase 4 theo DWHstruct.pdf

## 1. Phân tích Gap

### Hiện tại → Mục tiêu (DWHstruct.pdf)

| Thành phần | Hiện có | Cần đạt |
|-----------|---------|---------|
| Staging tables | 8 OLTP tables | ~29 OLTP tables + 1 macro |
| Dim tables | 2 (customer, product) | 11 (thêm: date, geo, territory, reseller, employee, promotion, currency, subcat, cat) |
| Fact tables | 1 (internet_sales) | 7 (thêm: reseller, currency_rate, quota, inventory, macro_economic, rfm) |

## 2. File 1: `src/etl/extract_to_staging.py` — Rewrite

Mở rộng từ 8 queries lên ~29 queries, mapping trực tiếp từ OLTP schemas:

```
OLTP Schema.Table              → staging.table
──────────────────────────────────────────────────
person.businessentity          → staging.businessentity
person.person                  → staging.person
person.address                 → staging.address
person.stateprovince           → staging.stateprovince
person.countryregion           → staging.countryregion
person.businessentityaddress   → staging.businessentityaddress
person.emailaddress            → staging.emailaddress
humanresources.employee        → staging.employee
humanresources.employeepayhistory → staging.employeepayhistory
humanresources.department      → staging.department
production.product             → staging.product
production.productcategory     → staging.productcategory
production.productsubcategory  → staging.productsubcategory
production.productinventory    → staging.productinventory
production.billofmaterials     → staging.billofmaterials
production.location            → staging.location
purchasing.vendor              → staging.vendor
purchasing.shipmethod          → staging.shipmethod
sales.salesorderheader         → staging.salesorderheader
sales.salesorderdetail         → staging.salesorderdetail
sales.customer                 → staging.customer
sales.store                    → staging.store
sales.specialoffer             → staging.specialoffer
sales.specialofferproduct      → staging.specialofferproduct
sales.currency                 → staging.currency
sales.currencyrate             → staging.currencyrate
sales.salesperson              → staging.salesperson
sales.salespersonquotahistory  → staging.salespersonquotahistory
sales.salesterritory           → staging.salesterritory
sales.salesterritoryhistory    → staging.salesterritoryhistory
sales.salesreason              → staging.salesreason
sales.salesorderheadersalesreason → staging.salesorderheadersalesreason
sales.countryregioncurrency    → staging.countryregioncurrency
```

Giữ nguyên pattern: pandas read_sql_query → lowercase columns → to_sql with if_exists="replace"

## 3. File 2: `sql/staging/clean_sales_staging.sql` — Rewrite

```sql
-- 1. Sales Order (giữ nguyên)
DELETE FROM staging.salesorderdetail WHERE orderqty <= 0 OR unitprice < 0;
DELETE FROM staging.salesorderheader WHERE orderdate IS NULL;

-- 2. Product (MỚI)
DELETE FROM staging.product WHERE listprice < 0 OR standardcost < 0;

-- 3. Employee (MỚI)
DELETE FROM staging.employee WHERE hiredate IS NULL;

-- 4. SpecialOffer (MỚI)
DELETE FROM staging.specialoffer WHERE enddate < startdate;

-- 5. CurrencyRate (MỚI)
DELETE FROM staging.currencyrate WHERE averagerate <= 0;

-- 6. Inventory (MỚI)
DELETE FROM staging.productinventory WHERE quantity < 0;
```

## 4. Phase 4: Post-ETL — Rewrite (3 nhóm)

### 4a. Marts: `src/marts/build_marts.py` + `sql/marts/`

**`mart_sales_kpi_monthly.sql`** — cập nhật:
- Join với `dwh.dim_sales_territory` để có territory_group
- Thêm `order_year`, `order_month`

**Marts mới:**
- `sql/marts/mart_macro_monthly.sql`: GDP, CPI, oil, interest, exchange theo territory/tháng
- `sql/marts/mart_product_profitability.sql`: lợi nhuận theo sản phẩm/tháng

**`build_marts.py`**: thêm 2 marts mới vào execution list

### 4b. Quality: `sql/quality/check_null_keys.sql` + `src/data_quality.py`

**`check_null_keys.sql`** — thêm checks:
- Null keys trên `fact_reseller_sales`, `fact_macro_economic_monthly`, `fact_currency_rate`
- Unmatched foreign keys trên tất cả fact-dì
- Negative values trên tất cả fact tables
- Duplicate surrogate keys trên dimensions

**`data_quality.py`**: giữ nguyên cấu trúc

### 4c. ML: `src/ml/run_ml.py` + feature SQLs

**`feature_customer_churn.sql`** — thêm:
- `territory_id`, `product_category` từ dim_product
- Macro-economic features từ fact_macro_economic_monthly

**`feature_revenue_forecast.sql`** — rewrite:
- Nguồn macro chuyển từ `staging.macro_*` → `dwh.fact_macro_economic_monthly`
- Thêm GDP, inflation, population

**`run_ml.py`**: giữ nguyên cấu trúc

## 5. Danh sách file thay đổi

| File | Hành động |
|------|----------|
| `src/etl/extract_to_staging.py` | Rewrite: 38 → ~120 dòng |
| `sql/staging/clean_sales_staging.sql` | Rewrite: 8 → ~20 dòng |
| `sql/marts/mart_sales_kpi_monthly.sql` | Rewrite: 40 → ~60 dòng |
| `sql/marts/mart_macro_monthly.sql` | **Tạo mới** |
| `sql/marts/mart_product_profitability.sql` | **Tạo mới** |
| `src/marts/build_marts.py` | Edit: thêm 2 marts |
| `sql/quality/check_null_keys.sql` | Rewrite: 41 → ~100 dòng |
| `src/data_quality.py` | Edit nhẹ: 0-1 dòng |
| `sql/features/feature_customer_churn.sql` | Edit: thêm features |
| `sql/features/feature_revenue_forecast.sql` | Rewrite: 61 → ~80 dòng |
| `src/ml/run_ml.py` | Edit nhẹ: 0-3 dòng |

**Tổng: 11 files** (~200 dòng mới)

## 6. File không thay đổi

- `sql/init/` (schemas, audit tables)
- `src/common/` (config, database utilities)
- `src/etl/sql_runner.py`
- `src/etl/run_etl.py`
- `sql/dwh/dimensions/dim_customer.sql`, `dim_product.sql`
- `sql/dwh/facts/fact_internet_sales.sql`
- `src/ml/vip_churn/*`, `src/ml/revenue_forecast/*`
- `docker/`, `config/`, `data/`, `Makefile`, `.env`, `docker-compose.yml`

## 7. Luồng ETL tổng thể sau rewrite

```
make run-all:
  1. macro ingestion  ──── staging.macro_territory_monthly  (giữ nguyên)
  2. extract OLTP     ──── staging (29 tables)               ← REWRITE
  3. clean staging    ──── clean staging data                 ← REWRITE
  4. build dimensions ──── dwh.dim_* (11 tables)             (thêm 9 dim SQL mới)
  5. build facts      ──── dwh.fact_* (7 tables)             (thêm 6 fact SQL mới)
  6. build marts      ──── mart.*                            ← REWRITE
  7. quality check    ──── audit quality checks               ← REWRITE
  8. ML pipeline      ──── feature.* → ml.*                  ← REWRITE
```

import sys
import os
import datetime
from sqlalchemy import text
from src.common.database import get_dwh_engine
from src.etl.extract_to_staging import extract_all
from src.etl.run_prj2_macro import run_macro_etl
from src.etl.sql_runner import run_sql_file

def log_etl_step(job_name, step_name, status, records_affected=0, error_message=None, started_at=None):
    """
    Log ETL step metadata into the audit table.
    """
    engine = get_dwh_engine()
    query = """
        INSERT INTO audit.etl_log (job_name, step_name, status, records_affected, error_message, started_at, ended_at)
        VALUES (:job_name, :step_name, :status, :records_affected, :error_message, :started_at, CURRENT_TIMESTAMP)
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(query), {
                "job_name": job_name,
                "step_name": step_name,
                "status": status,
                "records_affected": records_affected,
                "error_message": error_message,
                "started_at": started_at
            })
    except Exception as log_err:
        print(f"Audit Log Warning: Failed to write to audit log: {log_err}")

def run_pipeline():
    job_name = "AdventureWorks_DWH_ETL"
    print(f"=== Starting ETL Pipeline: {job_name} ===")
    
    # 1. Extraction from OLTP to DWH Staging
    step_name = "Extract OLTP to Staging"
    started_at = datetime.datetime.now()
    try:
        log_etl_step(job_name, step_name, "STARTED", started_at=started_at)
        extract_all()
        log_etl_step(job_name, step_name, "COMPLETED", started_at=started_at)
    except Exception as e:
        log_etl_step(job_name, step_name, "FAILED", error_message=str(e), started_at=started_at)
        print("Pipeline aborted due to extraction failure.")
        sys.exit(1)
        
    # 1.5 Macro data fetch from World Bank + FRED APIs
    step_name = "Fetch Macroeconomic Data"
    started_at = datetime.datetime.now()
    try:
        log_etl_step(job_name, step_name, "STARTED", started_at=started_at)
        run_macro_etl()
        log_etl_step(job_name, step_name, "COMPLETED", started_at=started_at)
    except Exception as e:
        log_etl_step(job_name, step_name, "FAILED", error_message=str(e), started_at=started_at)
        print("Pipeline aborted due to macro fetch failure.")
        sys.exit(1)

    # 2. SQL Transform steps in sequence (ordered by FK dependencies)
    sql_steps = [
        # Clean staging
        ("Clean Sales Staging", "sql/staging/clean_sales_staging.sql"),
        # Independent dimensions (no FK deps)
        ("Build Date Dim", "sql/dwh/dimensions/dim_date.sql"),
        ("Build Geography Dim", "sql/dwh/dimensions/dim_geography.sql"),
        ("Build Sales Territory Dim", "sql/dwh/dimensions/dim_sales_territory.sql"),
        ("Build Currency Dim", "sql/dwh/dimensions/dim_currency.sql"),
        ("Build Product Category Dim", "sql/dwh/dimensions/dim_product_category.sql"),
        # Dependent dimensions
        ("Build Product Subcategory Dim", "sql/dwh/dimensions/dim_product_subcategory.sql"),
        ("Build Product Dim", "sql/dwh/dimensions/dim_product.sql"),
        ("Build Customer Dim", "sql/dwh/dimensions/dim_customer.sql"),
        ("Build Reseller Dim", "sql/dwh/dimensions/dim_reseller.sql"),
        ("Build Employee Dim", "sql/dwh/dimensions/dim_employee.sql"),
        ("Build Promotion Dim", "sql/dwh/dimensions/dim_promotion.sql"),
        # Facts
        ("Build Sales Fact", "sql/dwh/facts/fact_internet_sales.sql"),
        ("Build Reseller Sales Fact", "sql/dwh/facts/fact_reseller_sales.sql"),
        ("Build Currency Rate Fact", "sql/dwh/facts/fact_currency_rate.sql"),
        ("Build Sales Quota Fact", "sql/dwh/facts/fact_sales_quota.sql"),
        ("Build Inventory Fact", "sql/dwh/facts/fact_inventory.sql"),
        ("Build Macro Economic Monthly Fact", "sql/dwh/facts/fact_macro_economic_monthly.sql"),
        ("Build Customer RFM Snapshot Fact", "sql/dwh/facts/fact_customer_rfm_snapshot.sql"),
        ("Build Web Traffic Analytics Fact", "sql/dwh/facts/fact_web_traffic_analytics.sql"),
    ]
    
    for step_title, sql_file in sql_steps:
        started_at = datetime.datetime.now()
        try:
            log_etl_step(job_name, step_title, "STARTED", started_at=started_at)
            run_sql_file(sql_file)
            log_etl_step(job_name, step_title, "COMPLETED", started_at=started_at)
        except Exception as e:
            log_etl_step(job_name, step_title, "FAILED", error_message=str(e), started_at=started_at)
            print(f"Pipeline aborted due to failure in step: {step_title}. Error: {e}")
            sys.exit(1)
            
    print("=== ETL Pipeline Finished Successfully ===")

if __name__ == "__main__":
    run_pipeline()

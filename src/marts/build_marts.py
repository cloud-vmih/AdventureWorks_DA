import sys
import os
from src.etl.sql_runner import run_sql_file

def build_all_marts():
    print("=== Building Analytical Data Marts ===")
    marts = [
        ("Sales KPI Monthly Mart", "sql/marts/mart_sales_kpi_monthly.sql")
    ]
    
    for mart_title, sql_file in marts:
        try:
            print(f"Running mart script: {mart_title}...")
            run_sql_file(sql_file)
        except Exception as e:
            print(f"Failed to build mart: {mart_title}. Error: {e}")
            sys.exit(1)
            
    print("=== Marts Rebuild Finished Successfully ===")

if __name__ == "__main__":
    build_all_marts()

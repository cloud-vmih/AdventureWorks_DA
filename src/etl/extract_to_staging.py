import sys
import os
import pandas as pd
from src.common.database import get_oltp_engine, get_dwh_engine

def extract_all():
    print("--- Starting Extraction: OLTP -> DWH Staging ---")
    oltp_engine = get_oltp_engine()
    dwh_engine = get_dwh_engine()
    
    # Queries mapping staging table name to its SQL query in OLTP
    queries = {
        "salesorderheader": "SELECT * FROM sales.salesorderheader",
        "salesorderdetail": "SELECT * FROM sales.salesorderdetail",
        "customer": "SELECT * FROM sales.customer",
        "person": "SELECT businessentityid, persontype, namestyle, title, firstname, middlename, lastname, suffix, emailpromotion, rowguid, modifieddate FROM person.person",
        "product": "SELECT * FROM production.product",
        "productcategory": "SELECT * FROM production.productcategory",
        "productsubcategory": "SELECT * FROM production.productsubcategory",
        "salesterritory": "SELECT * FROM sales.salesterritory"
    }
    
    for table_name, query in queries.items():
        try:
            print(f"Extracting data for staging.{table_name}...")
            df = pd.read_sql_query(query, oltp_engine)
            df.columns = [c.lower() for c in df.columns]
            print(f"Loading {len(df)} rows into staging.{table_name}...")
            df.to_sql(table_name, dwh_engine, schema="staging", if_exists="replace", index=False)
            print(f"Successfully populated staging.{table_name}.")
        except Exception as e:
            print(f"Error loading table staging.{table_name}: {e}")
            raise e
            
    print("--- Extraction Finished Successfully ---")

if __name__ == "__main__":
    extract_all()

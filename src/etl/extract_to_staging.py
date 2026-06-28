import sys
import os
import pandas as pd
from src.common.database import get_oltp_engine, get_dwh_engine

def extract_all():
    print("--- Starting Extraction: OLTP -> DWH Staging ---")
    oltp_engine = get_oltp_engine()
    dwh_engine = get_dwh_engine()

    queries = {
        # Person schema
        "businessentity": "SELECT * FROM person.businessentity",
        "person": "SELECT * FROM person.person",
        "address": "SELECT * FROM person.address",
        "stateprovince": "SELECT * FROM person.stateprovince",
        "countryregion": "SELECT * FROM person.countryregion",
        "businessentityaddress": "SELECT * FROM person.businessentityaddress",
        "emailaddress": "SELECT * FROM person.emailaddress",
        # HumanResources schema
        "employee": "SELECT * FROM humanresources.employee",
        "employeepayhistory": "SELECT * FROM humanresources.employeepayhistory",
        "department": "SELECT * FROM humanresources.department",
        # Production schema
        "product": "SELECT * FROM production.product",
        "productcategory": "SELECT * FROM production.productcategory",
        "productsubcategory": "SELECT * FROM production.productsubcategory",
        "productinventory": "SELECT * FROM production.productinventory",
        "billofmaterials": "SELECT * FROM production.billofmaterials",
        "location": "SELECT * FROM production.location",
        # Purchasing schema
        "vendor": "SELECT * FROM purchasing.vendor",
        "shipmethod": "SELECT * FROM purchasing.shipmethod",
        # Sales schema
        "salesorderheader": "SELECT * FROM sales.salesorderheader",
        "salesorderdetail": "SELECT * FROM sales.salesorderdetail",
        "customer": "SELECT * FROM sales.customer",
        "store": "SELECT * FROM sales.store",
        "specialoffer": "SELECT * FROM sales.specialoffer",
        "specialofferproduct": "SELECT * FROM sales.specialofferproduct",
        "currency": "SELECT * FROM sales.currency",
        "currencyrate": "SELECT * FROM sales.currencyrate",
        "salesperson": "SELECT * FROM sales.salesperson",
        "salespersonquotahistory": "SELECT * FROM sales.salespersonquotahistory",
        "salesterritory": "SELECT * FROM sales.salesterritory",
        "salesterritoryhistory": "SELECT * FROM sales.salesterritoryhistory",
        "salesreason": "SELECT * FROM sales.salesreason",
        "salesorderheadersalesreason": "SELECT * FROM sales.salesorderheadersalesreason",
        "countryregioncurrency": "SELECT * FROM sales.countryregioncurrency",
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

import os
import sys
import pandas as pd
from src.common.config import get_macro_sources
from src.common.database import get_dwh_engine

def ingest_macro_data():
    print("=== Starting Macro Data Ingestion ===")
    config = get_macro_sources()
    dwh_engine = get_dwh_engine()
    
    os.makedirs("data/macro/processed", exist_ok=True)
    
    for source_name, source_cfg in config['macro_sources'].items():
        try:
            raw_path = source_cfg['file_path']
            print(f"Processing macro source '{source_name}' from: {raw_path}")
            
            if not os.path.exists(raw_path):
                raise FileNotFoundError(f"Raw macro file not found at: {raw_path}")
                
            # Read CSV
            df = pd.read_csv(raw_path)
            
            # Verify columns
            expected_cols = source_cfg['columns']
            missing_cols = [c for c in expected_cols if c not in df.columns]
            if missing_cols:
                raise ValueError(f"Source {source_name} is missing expected columns: {missing_cols}")
                
            # Basic standardizations
            df['date'] = pd.to_datetime(df['date'])
            df['month_key'] = df['date'].dt.strftime('%Y%m')
            
            # Save processed CSV
            processed_path = os.path.join("data/macro/processed", f"{source_name}_processed.csv")
            df.to_csv(processed_path, index=False)
            print(f"Saved clean CSV to: {processed_path}")
            
            # Load to DWH staging
            staging_table = f"macro_{source_name}"
            print(f"Loading {len(df)} rows into staging.{staging_table}...")
            # We convert datetime to string to avoid timezone/format conversion issues in sqlalchemy
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            df.to_sql(staging_table, dwh_engine, schema="staging", if_exists="replace", index=False)
            print(f"Successfully loaded staging.{staging_table}.")
            
        except Exception as e:
            print(f"Failed to ingest macro source '{source_name}': {e}")
            sys.exit(1)
            
    print("=== Macro Data Ingestion Finished Successfully ===")

if __name__ == "__main__":
    ingest_macro_data()

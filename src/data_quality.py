from src.common.database import get_dwh_engine
from sqlalchemy import text

def run_quality_checks(sql_file="sql/quality/check_null_keys.sql"):
    print("=== Running Data Quality Checks ===")
    engine = get_dwh_engine()
    
    try:
        with open(sql_file, "r") as f:
            query = f.read()
            
        # Clean query
        lines = query.split("\n")
        clean_lines = [l for l in lines if not l.strip().startswith("--")]
        clean_query = "\n".join(clean_lines).strip()
        
        violations_found = False
        with engine.connect() as conn:
            result = conn.execute(text(clean_query))
            for row in result:
                table, check, violations = row[0], row[1], row[2]
                print(f"Table: {table:22} | Check: {check:24} | Violations: {violations}")
                if violations > 0:
                    violations_found = True
                    
        if violations_found:
            print("--- WARNING: Data quality violations detected! Check staging & ETL steps. ---")
        else:
            print("--- SUCCESS: All data quality checks passed successfully. ---")
            
    except Exception as e:
        print(f"Error running data quality checks: {e}")

if __name__ == "__main__":
    run_quality_checks()

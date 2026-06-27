from sqlalchemy import text
from src.common.database import get_dwh_engine

def run_sql_file(file_path):
    """
    Reads a SQL file and executes its statements against the DWH database.
    """
    print(f"Executing SQL: {file_path}")
    engine = get_dwh_engine()
    
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()
        
    # Remove single-line comments but keep the SQL content intact
    lines = sql_content.split("\n")
    clean_lines = [line for line in lines if not line.strip().startswith("--")]
    sql_to_run = "\n".join(clean_lines).strip()
    
    if not sql_to_run:
        print(f"Warning: SQL file {file_path} is empty or contains only comments.")
        return
        
    with engine.begin() as conn:
        conn.execute(text(sql_to_run))
        
    print(f"Successfully finished: {file_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python sql_runner.py <path_to_sql_file>")
    else:
        run_sql_file(sys.argv[1])

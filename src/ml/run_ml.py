import sys
from src.etl.sql_runner import run_sql_file
from src.ml.vip_churn.train import train_model as train_churn
from src.ml.vip_churn.evaluate import evaluate_model as eval_churn
from src.ml.vip_churn.predict import generate_predictions as pred_churn
from src.ml.revenue_forecast.train import train_model as train_forecast
from src.ml.revenue_forecast.evaluate import evaluate_model as eval_forecast
from src.ml.revenue_forecast.predict import generate_predictions as pred_forecast

def run_ml_pipeline():
    print("=== STARTING MACHINE LEARNING PIPELINE ===")
    
    # 1. Rebuild feature tables in DWH
    print("\n[Step 1/3] Generating ML features in DWH...")
    try:
        run_sql_file("sql/features/feature_customer_churn.sql")
        run_sql_file("sql/features/feature_revenue_forecast.sql")
    except Exception as e:
        print(f"Error generating features: {e}")
        sys.exit(1)
        
    # 2. Run VIP Churn Pipeline
    print("\n[Step 2/3] Running VIP Churn Pipeline...")
    try:
        train_churn()
        eval_churn()
        pred_churn()
    except Exception as e:
        print(f"Error in VIP Churn Pipeline: {e}")
        sys.exit(1)
        
    # 3. Run Revenue Forecast Pipeline
    print("\n[Step 3/3] Running Revenue Forecast Pipeline...")
    try:
        train_forecast()
        eval_forecast()
        pred_forecast()
    except Exception as e:
        print(f"Error in Revenue Forecast Pipeline: {e}")
        sys.exit(1)
        
    print("\n=== MACHINE LEARNING PIPELINE COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_ml_pipeline()

import os
import sys
import pickle
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from src.common.database import get_dwh_engine
from src.common.config import get_model_config

def evaluate_model():
    print("=== Evaluating Revenue Forecast Model ===")
    
    cfg = get_model_config()['models']['revenue_forecast']
    target = cfg['target']
    features = cfg['features']
    model_path = cfg['model_path']
    
    engine = get_dwh_engine()
    
    try:
        query = "SELECT * FROM feature.revenue_forecast_features"
        df = pd.read_sql_query(query, engine)
        
        if len(df) < 5:
            print("Warning: Insufficient data to evaluate.")
            sys.exit(1)
            
        if not os.path.exists(model_path):
            print(f"Error: Trained model not found at {model_path}. Train the model first.")
            sys.exit(1)
            
        with open(model_path, "rb") as f:
            model = pickle.load(f)
            
        X = df[features]
        y = df[target]
        
        # Predict
        y_pred = model.predict(X)
        
        # Calculate metrics
        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        
        # MAPE
        y_non_zero = np.where(y == 0, 1e-5, y)
        mape = np.mean(np.abs((y - y_pred) / y_non_zero)) * 100
        
        metrics_output = f"""Revenue Forecast Model Evaluation Report
========================================
Mean Absolute Error (MAE):             {mae:.2f}
Root Mean Squared Error (RMSE):         {rmse:.2f}
Mean Absolute Percentage Error (MAPE):  {mape:.2f}%
"""
        print(metrics_output)
        
        # Save metrics file
        metrics_file = "models/revenue_forecast/metrics.txt"
        with open(metrics_file, "w") as mf:
            mf.write(metrics_output)
        print(f"Evaluation report saved to: {metrics_file}")
        
    except Exception as e:
        print(f"Error evaluating Revenue Forecast model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    evaluate_model()

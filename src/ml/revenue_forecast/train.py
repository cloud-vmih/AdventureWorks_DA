import os
import sys
import pickle
import pandas as pd
from xgboost import XGBRegressor
from src.common.database import get_dwh_engine
from src.common.config import get_model_config

def train_model():
    print("=== Training Revenue Forecast Model ===")
    
    cfg = get_model_config()['models']['revenue_forecast']
    target = cfg['target']
    features = cfg['features']
    params = cfg['parameters']
    model_path = cfg['model_path']
    
    engine = get_dwh_engine()
    
    try:
        query = "SELECT * FROM feature.revenue_forecast_features"
        df = pd.read_sql_query(query, engine)
        print(f"Loaded {len(df)} records from feature.revenue_forecast_features.")
        
        if len(df) < 5:
            print("Warning: Insufficient data to train model. Need at least 5 records.")
            sys.exit(1)
            
        X = df[features]
        y = df[target]
        
        # Train XGBoost model
        model = XGBRegressor(
            n_estimators=params.get('n_estimators', 100),
            max_depth=params.get('max_depth', 6),
            learning_rate=params.get('learning_rate', 0.1),
            random_state=42
        )
        model.fit(X, y)
        
        # Save model pickle
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
            
        print(f"Model trained and saved to: {model_path}")
        
    except Exception as e:
        print(f"Error during Revenue Forecast training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_status = train_model()

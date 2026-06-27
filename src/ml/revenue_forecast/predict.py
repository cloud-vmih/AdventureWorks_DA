import os
import sys
import pickle
import pandas as pd
from datetime import datetime
from src.common.database import get_dwh_engine
from src.common.config import get_model_config

def generate_predictions():
    print("=== Running Revenue Forecast Prediction ===")
    
    cfg = get_model_config()['models']['revenue_forecast']
    features = cfg['features']
    model_path = cfg['model_path']
    
    engine = get_dwh_engine()
    
    try:
        if not os.path.exists(model_path):
            print(f"Error: Model file {model_path} not found. Run training first.")
            sys.exit(1)
            
        with open(model_path, "rb") as f:
            model = pickle.load(f)
            
        query = "SELECT * FROM feature.revenue_forecast_features"
        df = pd.read_sql_query(query, engine)
        
        if len(df) == 0:
            print("No data found for predictions.")
            sys.exit(0)
            
        X = df[features]
        df['predicted_revenue'] = model.predict(X)
        df['predicted_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Select key columns
        predictions = df[['month_key', 'territory_id', 'revenue', 'predicted_revenue', 'predicted_at']]
        predictions = predictions.rename(columns={'revenue': 'actual_revenue'})
        
        # Load predictions into ML schema
        predictions.to_sql("revenue_forecast_predictions", engine, schema="ml", if_exists="replace", index=False)
        print(f"Successfully generated and loaded predictions for {len(predictions)} territory-months into ml.revenue_forecast_predictions.")
        
    except Exception as e:
        print(f"Error generating revenue forecasts: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_predictions()

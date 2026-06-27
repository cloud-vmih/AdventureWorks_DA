import os
import sys
import pickle
import pandas as pd
from datetime import datetime
from src.common.database import get_dwh_engine
from src.common.config import get_model_config

def generate_predictions():
    print("=== Running VIP Churn Prediction ===")
    
    cfg = get_model_config()['models']['vip_churn']
    features = cfg['features']
    model_path = cfg['model_path']
    
    engine = get_dwh_engine()
    
    try:
        if not os.path.exists(model_path):
            print(f"Error: Model file {model_path} not found. Run training first.")
            sys.exit(1)
            
        with open(model_path, "rb") as f:
            model = pickle.load(f)
            
        query = "SELECT * FROM feature.customer_churn_features"
        df = pd.read_sql_query(query, engine)
        
        if len(df) == 0:
            print("No data found for predictions.")
            sys.exit(0)
            
        X = df[features]
        df['churn_probability'] = model.predict_proba(X)[:, 1]
        df['predicted_label'] = model.predict(X)
        df['predicted_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Select key columns
        predictions = df[['customer_key', 'churn_probability', 'predicted_label', 'predicted_at']]
        
        # Load predictions into ML schema
        predictions.to_sql("vip_churn_predictions", engine, schema="ml", if_exists="replace", index=False)
        print(f"Successfully generated and loaded predictions for {len(predictions)} VIP customers into ml.vip_churn_predictions.")
        
    except Exception as e:
        print(f"Error generating churn predictions: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_predictions()

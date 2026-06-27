import os
import sys
import pickle
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve, auc
from src.common.database import get_dwh_engine
from src.common.config import get_model_config

def evaluate_model():
    print("=== Evaluating VIP Churn Model ===")
    
    cfg = get_model_config()['models']['vip_churn']
    target = cfg['target']
    features = cfg['features']
    model_path = cfg['model_path']
    
    engine = get_dwh_engine()
    
    try:
        query = "SELECT * FROM feature.customer_churn_features"
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
        y_prob = model.predict_proba(X)[:, 1]
        
        # Classification report
        report = classification_report(y, y_pred)
        auc_roc = roc_auc_score(y, y_prob)
        
        precision, recall, _ = precision_recall_curve(y, y_prob)
        auc_pr = auc(recall, precision)
        
        metrics_output = f"""VIP Churn Model Evaluation Report
==================================
AUC-ROC Score: {auc_roc:.4f}
AUC-PR Score:  {auc_pr:.4f}

Classification Report:
{report}
"""
        print(metrics_output)
        
        # Save metrics file
        metrics_file = "models/vip_churn/metrics.txt"
        with open(metrics_file, "w") as mf:
            mf.write(metrics_output)
        print(f"Evaluation report saved to: {metrics_file}")
        
    except Exception as e:
        print(f"Error evaluating VIP Churn model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    evaluate_model()

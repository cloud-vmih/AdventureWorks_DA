import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from src.common.database import get_dwh_engine

def main():
    engine = get_dwh_engine()
    
    # 1. Load Macro Indicators
    print("Loading macro data...")
    query_macro = """
        SELECT 
            LEFT(month_key, 6) as month_key,
            AVG(cpi) as cpi,
            AVG(interest_rate) as interest_rate,
            AVG(gdp) as gdp,
            AVG(inflation) as inflation
        FROM dwh.fact_macro_economic_monthly
        GROUP BY LEFT(month_key, 6)
        ORDER BY month_key
    """
    df_macro = pd.read_sql_query(query_macro, engine)
    
    # 2. Load Sales Monthly
    print("Loading monthly B2C sales...")
    query_sales = """
        SELECT 
            TO_CHAR(order_date, 'YYYYMM') as month_key,
            SUM(line_total) as revenue
        FROM dwh.fact_internet_sales
        GROUP BY TO_CHAR(order_date, 'YYYYMM')
        ORDER BY month_key
    """
    df_sales = pd.read_sql_query(query_sales, engine)
    
    # Merge
    df_merged = pd.merge(df_sales, df_macro, on='month_key', how='inner')
    
    if len(df_merged) < 5:
        print("Error: Not enough data for macro regression!")
        return

    # Clean
    for col in ['revenue', 'cpi', 'interest_rate', 'gdp', 'inflation']:
        df_merged[col] = pd.to_numeric(df_merged[col], errors='coerce').fillna(0.0)

    # 3. Fit OLS Model
    print("Fitting OLS model...")
    X_ols = df_merged[['cpi', 'interest_rate', 'gdp', 'inflation']]
    X_ols_const = sm.add_constant(X_ols)
    y_ols = df_merged['revenue']
    
    ols_model = sm.OLS(y_ols, X_ols_const).fit()
    
    # Export OLS Coefficients
    coef_data = []
    for var in ['const', 'cpi', 'interest_rate', 'gdp', 'inflation']:
        coef_data.append({
            "variable": var,
            "coefficient": float(ols_model.params[var]),
            "p_value": float(ols_model.pvalues[var]),
            "t_value": float(ols_model.tvalues[var]),
            "standard_error": float(ols_model.bse[var])
        })
    df_coef = pd.DataFrame(coef_data)
    df_coef.to_sql('macro_ols_coefficients', engine, schema='ml', if_exists='replace', index=False)
    print("Saved ml.macro_ols_coefficients.")

    # 4. Fit Random Forest and get Feature Importance
    print("Fitting Random Forest model...")
    X_rf = df_merged[['cpi', 'interest_rate', 'gdp', 'inflation']]
    y_rf = df_merged['revenue']
    
    rf = RandomForestRegressor(n_estimators=100, max_depth=4, random_state=42)
    rf.fit(X_rf, y_rf)
    
    # Export RF Feature Importance
    fi_data = []
    for var, imp in zip(['cpi', 'interest_rate', 'gdp', 'inflation'], rf.feature_importances_):
        fi_data.append({
            "variable": var,
            "importance": float(imp)
        })
    df_fi = pd.DataFrame(fi_data).sort_values("importance", ascending=False)
    df_fi.to_sql('macro_rf_feature_importance', engine, schema='ml', if_exists='replace', index=False)
    print("Saved ml.macro_rf_feature_importance.")

    # 5. Model Performance Metrics
    print("Generating model performance metrics...")
    ols_r2 = ols_model.rsquared
    ols_adj_r2 = ols_model.rsquared_adj
    rf_r2 = rf.score(X_rf, y_rf) # train R2
    
    df_metrics = pd.DataFrame([
        {"model_name": "OLS Linear Regression", "metric_name": "R-squared", "metric_value": ols_r2},
        {"model_name": "OLS Linear Regression", "metric_name": "Adjusted R-squared", "metric_value": ols_adj_r2},
        {"model_name": "RandomForestRegressor", "metric_name": "Train R-squared", "metric_value": rf_r2}
    ])
    df_metrics.to_sql('macro_model_metrics', engine, schema='ml', if_exists='replace', index=False)
    print("Saved ml.macro_model_metrics.")

    # 6. Indexed Trend Data
    print("Generating indexed trend data...")
    # Index all variables to 100 at the first month key
    df_indexed = df_merged.copy()
    first_row = df_indexed.iloc[0]
    
    df_indexed['indexed_revenue'] = (df_indexed['revenue'] / (first_row['revenue'] + 1e-5)) * 100.0
    df_indexed['indexed_cpi'] = (df_indexed['cpi'] / (first_row['cpi'] + 1e-5)) * 100.0
    df_indexed['indexed_interest_rate'] = (df_indexed['interest_rate'] / (first_row['interest_rate'] + 1e-5)) * 100.0
    df_indexed['indexed_gdp'] = (df_indexed['gdp'] / (first_row['gdp'] + 1e-5)) * 100.0
    df_indexed['indexed_inflation'] = (df_indexed['inflation'] / (first_row['inflation'] + 1e-5)) * 100.0
    
    df_indexed_export = df_indexed[['month_key', 'indexed_revenue', 'indexed_cpi', 'indexed_interest_rate', 'indexed_gdp', 'indexed_inflation']]
    df_indexed_export.to_sql('macro_indexed_trend', engine, schema='ml', if_exists='replace', index=False)
    print("Saved ml.macro_indexed_trend.")
    print("--- CHAPTER 5 ANALYTICS EXPORT COMPLETED ---")

if __name__ == "__main__":
    main()

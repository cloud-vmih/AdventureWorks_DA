import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from src.common.database import get_dwh_engine

def main():
    engine = get_dwh_engine()
    
    # Load raw product data
    print("Loading product profitability monthly data...")
    df_raw = pd.read_sql("SELECT * FROM mart.mart_product_profitability_monthly", engine)
    
    if df_raw.empty:
        print("Error: mart.mart_product_profitability_monthly is empty!")
        return

    # Aggregate to product level
    df_prod = df_raw.groupby(['product_key', 'product_name', 'category_name', 'subcategory_name']).agg(
        revenue=('revenue', 'sum'),
        cogs=('cogs', 'sum'),
        gross_profit=('gross_profit', 'sum'),
        units_sold=('quantity', 'sum'),
        avg_discount=('avg_discount_rate', 'mean')
    ).reset_index()
    
    df_prod['gross_margin'] = df_prod['gross_profit'] / (df_prod['revenue'] + 1e-5)
    
    # 1. Product Portfolio Matrix
    print("Computing product portfolio...")
    rev_mid = df_prod['revenue'].median()
    margin_mid = df_prod['gross_margin'].median()
    
    def classify_portfolio(row):
        rev = row['revenue']
        margin = row['gross_margin']
        if rev >= rev_mid and margin >= margin_mid:
            return 'Star'
        elif rev >= rev_mid and margin < margin_mid:
            return 'Volume-Low Margin'
        elif rev < rev_mid and margin >= margin_mid:
            return 'Niche-High Margin'
        else:
            return 'Weak'
            
    df_prod['portfolio'] = df_prod.apply(classify_portfolio, axis=1)
    df_prod.to_sql('product_portfolio', engine, schema='ml', if_exists='replace', index=False)
    print("Saved ml.product_portfolio.")

    # 2. ABC Analysis
    print("Computing ABC analysis...")
    # ABC by Revenue
    df_abc_rev = df_prod.sort_values('revenue', ascending=False).copy()
    df_abc_rev['cum_revenue'] = df_abc_rev['revenue'].cumsum()
    tot_rev = df_abc_rev['revenue'].sum()
    df_abc_rev['cum_revenue_pct'] = df_abc_rev['cum_revenue'] / (tot_rev + 1e-5)
    df_abc_rev['abc_revenue'] = np.where(df_abc_rev['cum_revenue_pct'] <= 0.80, 'A', np.where(df_abc_rev['cum_revenue_pct'] <= 0.95, 'B', 'C'))
    
    # ABC by Profit
    df_abc_prof = df_prod.sort_values('gross_profit', ascending=False).copy()
    df_abc_prof['cum_profit'] = df_abc_prof['gross_profit'].cumsum()
    tot_prof = df_abc_prof['gross_profit'].sum()
    df_abc_prof['cum_profit_pct'] = df_abc_prof['cum_profit'] / (tot_prof + 1e-5)
    df_abc_prof['abc_profit'] = np.where(df_abc_prof['cum_profit_pct'] <= 0.80, 'A', np.where(df_abc_prof['cum_profit_pct'] <= 0.95, 'B', 'C'))
    
    # Merge
    df_abc = df_prod[['product_key', 'product_name', 'category_name', 'subcategory_name', 'revenue', 'gross_profit']].copy()
    df_abc = df_abc.merge(df_abc_rev[['product_key', 'cum_revenue_pct', 'abc_revenue']], on='product_key')
    df_abc = df_abc.merge(df_abc_prof[['product_key', 'cum_profit_pct', 'abc_profit']], on='product_key')
    df_abc.to_sql('product_abc_analysis', engine, schema='ml', if_exists='replace', index=False)
    print("Saved ml.product_abc_analysis.")

    # 3. Product Discount Effectiveness
    print("Computing discount effectiveness...")
    df_disc = df_prod.copy()
    
    def check_discount(row):
        disc = row['avg_discount']
        margin = row['gross_margin']
        if disc > 0.05:
            if margin < 0.10:
                return 'Ineffective - Margin Diluted'
            else:
                return 'Effective - Promoted High Margin'
        elif disc > 0:
            return 'Moderate Discount'
        else:
            return 'No Discount'
            
    df_disc['effectiveness'] = df_disc.apply(check_discount, axis=1)
    df_disc.to_sql('product_discount_effectiveness', engine, schema='ml', if_exists='replace', index=False)
    print("Saved ml.product_discount_effectiveness.")

    # 4. K-Means Product Clustering
    print("Running K-Means Product Clustering...")
    cluster_features = ['revenue', 'gross_margin', 'units_sold']
    X = df_prod[cluster_features].copy()
    X['gross_margin'] = X['gross_margin'].fillna(0.0)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df_prod['cluster_label'] = kmeans.fit_predict(X_scaled)
    
    # Profile cluster names based on centers
    centers = kmeans.cluster_centers_
    # scaler inverse to get real values of centers
    real_centers = scaler.inverse_transform(centers)
    
    # Rank clusters by revenue center
    cluster_ranks = np.argsort(real_centers[:, 0]) # lowest revenue to highest revenue index
    
    cluster_names = {}
    cluster_names[cluster_ranks[3]] = "Star Products (High Revenue, High Margin)"
    cluster_names[cluster_ranks[2]] = "Volume Leaders (Moderate Revenue, High Volume)"
    cluster_names[cluster_ranks[1]] = "Niche Products (Low Revenue, High Margin)"
    cluster_names[cluster_ranks[0]] = "Slow Moving/Low Margin"
    
    df_prod['cluster_name'] = df_prod['cluster_label'].map(cluster_names)
    df_prod.to_sql('product_cluster_result', engine, schema='ml', if_exists='replace', index=False)
    print("Saved ml.product_cluster_result.")

    # 5. Product Category Forecast
    print("Computing product category forecast...")
    df_cat_monthly = df_raw.groupby(['month_key', 'category_name']).agg(
        revenue=('revenue', 'sum'),
        quantity=('quantity', 'sum')
    ).reset_index()
    
    df_cat_monthly['month'] = pd.to_datetime(df_cat_monthly['month_key'], format='%Y%m')
    df_cat_monthly = df_cat_monthly.sort_values('month')
    
    forecasts = []
    for cat in df_cat_monthly['category_name'].unique():
        df_cat = df_cat_monthly[df_cat_monthly['category_name'] == cat].copy()
        
        # We need historical lags
        df_cat['lag_1'] = df_cat['revenue'].shift(1)
        df_cat['lag_2'] = df_cat['revenue'].shift(2)
        df_cat['lag_3'] = df_cat['revenue'].shift(3)
        df_cat['month_num'] = df_cat['month'].dt.month
        df_cat['quarter'] = df_cat['month'].dt.quarter
        
        # Train-test split (use last 3 months as validation or train all for future)
        # To forecast 3 months ahead, we'll train an XGBoost model on all non-null lag data
        df_train = df_cat.dropna(subset=['lag_1', 'lag_2', 'lag_3'])
        
        if len(df_train) < 6:
            # Not enough data, use simple naive forecast
            last_rev = df_cat['revenue'].iloc[-1]
            for i in range(1, 4):
                next_month = df_cat['month'].iloc[-1] + pd.DateOffset(months=i)
                forecasts.append({
                    "month_key": next_month.strftime("%Y%m"),
                    "category_name": cat,
                    "actual_revenue": None,
                    "forecast_revenue_naive": last_rev,
                    "forecast_revenue_xgb": last_rev,
                    "mae": 0.0
                })
            continue
            
        features = ['lag_1', 'lag_2', 'lag_3', 'month_num', 'quarter']
        X_train = df_train[features]
        y_train = df_train['revenue']
        
        model = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42)
        model.fit(X_train, y_train)
        
        # Calculate training MAE as proxy for error
        preds_train = model.predict(X_train)
        mae = np.mean(np.abs(y_train - preds_train))
        
        # Add actuals
        for idx, row in df_cat.iterrows():
            forecasts.append({
                "month_key": row['month_key'],
                "category_name": cat,
                "actual_revenue": row['revenue'],
                "forecast_revenue_naive": row['lag_1'] if not pd.isna(row['lag_1']) else row['revenue'],
                "forecast_revenue_xgb": row['revenue'], # historical fit
                "mae": mae
            })
            
        # Predict 3 steps ahead
        last_lags = [df_cat['revenue'].iloc[-1], df_cat['revenue'].iloc[-2], df_cat['revenue'].iloc[-3]]
        curr_date = df_cat['month'].iloc[-1]
        
        for i in range(1, 4):
            next_month = curr_date + pd.DateOffset(months=i)
            features_pred = pd.DataFrame([{
                "lag_1": last_lags[0],
                "lag_2": last_lags[1],
                "lag_3": last_lags[2],
                "month_num": next_month.month,
                "quarter": (next_month.month - 1) // 3 + 1
            }])
            pred_val = float(model.predict(features_pred)[0])
            pred_val = max(pred_val, 0.0) # non-negative
            
            forecasts.append({
                "month_key": next_month.strftime("%Y%m"),
                "category_name": cat,
                "actual_revenue": None,
                "forecast_revenue_naive": last_lags[0],
                "forecast_revenue_xgb": pred_val,
                "mae": mae
            })
            # Update lags for multi-step
            last_lags = [pred_val] + last_lags[:2]
            
    df_fore = pd.DataFrame(forecasts)
    df_fore.to_sql('product_category_forecast', engine, schema='ml', if_exists='replace', index=False)
    print("Saved ml.product_category_forecast.")

    # 6. Product Strategy Actions
    print("Computing product strategy actions...")
    strategies = []
    for idx, row in df_prod.iterrows():
        p_name = row['product_name']
        cat = row['category_name']
        port = row['portfolio']
        rev = row['revenue']
        margin = row['gross_margin']
        disc = row['avg_discount']
        
        action = ""
        priority = "Medium"
        
        if port == 'Star':
            action = "Duy trì tồn kho tối ưu, tăng quảng cáo và củng cố vị thế dẫn đầu."
            priority = "High"
        elif port == 'Volume-Low Margin':
            if disc > 0.05:
                action = "Chiết khấu quá cao làm giảm margin. Cần giảm discount để tối ưu hóa biên lợi nhuận."
                priority = "High"
            else:
                action = "Tối ưu hóa giá vốn (COGS) hoặc tăng nhẹ giá bán để cải thiện margin."
                priority = "Medium"
        elif port == 'Niche-High Margin':
            action = "Tăng tiếp cận khách hàng VIP, quảng bá tính cao cấp của sản phẩm để kích thích doanh số."
            priority = "High"
        else: # Weak
            action = "Giảm dần lượng nhập kho, bundle (bán kèm) với sản phẩm Star hoặc thanh lý giảm giá dọn kho."
            priority = "Low"
            
        strategies.append({
            "product_key": row['product_key'],
            "product_name": p_name,
            "category_name": cat,
            "portfolio": port,
            "revenue": rev,
            "gross_margin": margin,
            "avg_discount": disc,
            "recommended_action": action,
            "priority": priority
        })
        
    df_strat = pd.DataFrame(strategies)
    df_strat.to_sql('product_strategy_actions', engine, schema='ml', if_exists='replace', index=False)
    print("Saved ml.product_strategy_actions.")
    print("--- CHAPTER 4 ANALYTICS EXPORT COMPLETED ---")

if __name__ == "__main__":
    main()

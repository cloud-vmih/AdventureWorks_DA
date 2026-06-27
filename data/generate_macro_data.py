import os
import pandas as pd
import numpy as np

def generate_data():
    print("Generating simulated macro-economic data...")
    os.makedirs("data/macro/raw", exist_ok=True)
    
    dates = pd.date_range(start="2020-01-01", end="2025-12-01", freq="MS")
    countries = ["US", "CA", "FR", "DE", "GB", "AU"]
    
    # 1. CPI
    cpi_records = []
    for country in countries:
        base_cpi = 100.0
        for d in dates:
            # Add some trend + random walk
            base_cpi += np.random.uniform(0.1, 0.5)
            cpi_records.append({
                "date": d.strftime("%Y-%m-%d"),
                "country_code": country,
                "cpi": round(base_cpi, 2)
            })
    pd.DataFrame(cpi_records).to_csv("data/macro/raw/cpi.csv", index=False)
    print("Generated cpi.csv")
    
    # 2. Interest Rates
    ir_records = []
    for country in countries:
        rate = 1.5 if country == "US" else 1.0
        for d in dates:
            # Macro shock: rate hikes in 2022-2023
            if d.year == 2022:
                rate += np.random.uniform(0.1, 0.4)
            elif d.year == 2023:
                rate += np.random.uniform(0.05, 0.2)
            else:
                rate += np.random.uniform(-0.1, 0.1)
            rate = max(0.25, min(8.0, rate))
            ir_records.append({
                "date": d.strftime("%Y-%m-%d"),
                "country_code": country,
                "interest_rate": round(rate, 2)
            })
    pd.DataFrame(ir_records).to_csv("data/macro/raw/interest_rate.csv", index=False)
    print("Generated interest_rate.csv")
    
    # 3. Oil Prices (global)
    oil_records = []
    oil_price = 60.0
    for d in dates:
        # Volatility
        oil_price += np.random.uniform(-4.0, 5.0)
        # Spike in 2022
        if d.year == 2022 and d.month in [3, 4, 5, 6]:
            oil_price += np.random.uniform(5.0, 10.0)
        oil_price = max(20.0, oil_price)
        oil_records.append({
            "date": d.strftime("%Y-%m-%d"),
            "oil_price": round(oil_price, 2)
        })
    pd.DataFrame(oil_records).to_csv("data/macro/raw/oil_price.csv", index=False)
    print("Generated oil_price.csv")
    
    # 4. Exchange Rates
    fx_records = []
    for country in countries:
        base_rate = 1.0
        if country == "CA": base_rate = 1.3
        elif country == "FR" or country == "DE": base_rate = 0.9
        elif country == "GB": base_rate = 0.8
        elif country == "AU": base_rate = 1.4
        
        for d in dates:
            # Small fluctuations
            rate = base_rate + np.random.uniform(-0.02, 0.02)
            fx_records.append({
                "date": d.strftime("%Y-%m-%d"),
                "country_code": country,
                "exchange_rate": round(rate, 4)
            })
    pd.DataFrame(fx_records).to_csv("data/macro/raw/exchange_rate.csv", index=False)
    print("Generated exchange_rate.csv")
    
    print("All simulated macro economic files generated successfully.")

if __name__ == "__main__":
    generate_data()

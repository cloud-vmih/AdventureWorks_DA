import sys
import os
import pandas as pd
from sqlalchemy import text
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

sys.path.append(os.path.abspath(os.path.join(".")))
from src.common.database import get_dwh_engine

engine = get_dwh_engine()

def compute_rules(tbl, channel, min_supp=0.02):
    print(f"Extracting transactions for {channel} using SQL aggregation...")
    query = f"""
        SELECT 
            f.sales_order_number,
            STRING_AGG(DISTINCT p.product_name, ';') as product_list
        FROM dwh.{tbl} f
        JOIN dwh.dim_product p ON f.product_key = p.product_key
        GROUP BY f.sales_order_number
    """
    df = pd.read_sql_query(query, engine)
    
    if df.empty:
        print(f"No data for {channel}!")
        return pd.DataFrame()
        
    print("Splitting product lists...")
    order_groups = df['product_list'].str.split(';').tolist()
    
    # Filter out single item baskets
    multi_item_baskets = [basket for basket in order_groups if basket and len(basket) > 1]
    print(f"Total baskets: {len(order_groups)}, Multi-item baskets: {len(multi_item_baskets)}")
    
    if not multi_item_baskets:
        print("No multi-item baskets found!")
        return pd.DataFrame()
        
    print("Running TransactionEncoder...")
    te = TransactionEncoder()
    te_ary = te.fit(multi_item_baskets).transform(multi_item_baskets)
    basket_sets = pd.DataFrame(te_ary, columns=te.columns_)
    
    print(f"Running apriori with min_support={min_supp} and max_len=2...")
    # Limit max_len to 2 to prevent combinatorial explosion and focus on pairwise cross-selling
    frequent_itemsets = apriori(basket_sets, min_support=min_supp, use_colnames=True, max_len=2)
    
    if frequent_itemsets.empty:
        print("No frequent itemsets found!")
        return pd.DataFrame()
        
    print(f"Frequent itemsets count: {len(frequent_itemsets)}")
    
    print("Generating association rules...")
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
    
    if rules.empty:
        print("No rules found!")
        return pd.DataFrame()
        
    rules['channel'] = channel
    
    rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(list(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(list(x)))
    
    cols_to_keep = ['antecedents', 'consequents', 'antecedent support', 'consequent support', 
                    'support', 'confidence', 'lift', 'leverage', 'conviction', 'zhangs_metric', 'channel']
    return rules[cols_to_keep]

# Run with 1% support for B2C and 3% for B2B (limiting max_len to 2 prevents OOM)
df_b2c = compute_rules("fact_internet_sales", "B2C", min_supp=0.01)
df_b2b = compute_rules("fact_reseller_sales", "B2B", min_supp=0.03)

df_all = pd.concat([df_b2c, df_b2b])

if not df_all.empty:
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS ml;"))
        conn.execute(text("DROP TABLE IF EXISTS ml.association_rules;"))
        conn.commit()
    
    df_all.to_sql("association_rules", engine, schema="ml", if_exists="replace", index=False)
    print("MBA rules successfully computed and saved to DWH.")
else:
    print("No rules generated.")

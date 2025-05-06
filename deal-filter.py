import pandas as pd
import numpy as np
import re
from pathlib import Path
import plotly.express as px
from datetime import datetime
import os
import json

# 📂 Paths
CSV_PATH = 'product-ids/uniqlo-products.csv'
ID_PATH = 'product-ids/filtered-ids.txt'
TARGET_ID_PATH = 'product-ids/target-ids.txt'
BLOCK_PATH = 'product-ids/blocked_ids.json'

OUTPUT_CSV = 'product-ids/filtered-uniqlo-products.csv'


# 🧹 Load and clean product data
df = pd.read_csv(CSV_PATH)

def clean_price(price_str):
    if pd.isna(price_str):
        return None
    price_str = price_str.replace('€', '').replace(',', '.').strip()
    match = re.findall(r'\d+\.?\d*', price_str)
    return float(match[0]) if match else None

def save_or_append_df(df: pd.DataFrame, csv_path: str):
    """
    Saves a DataFrame to a CSV file. Appends to the file if it exists, including only data rows (no header).
    If the file does not exist, creates it with headers.

    Parameters:
        df (pd.DataFrame): DataFrame to save
        csv_path (str): Full path to the target CSV file
    """
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode='a', header=False, index=False)
        print(f"➕ Appended {len(df)} rows to {csv_path}")
    else:
        df.to_csv(csv_path, index=False)
        print(f"📄 Created new file and saved {len(df)} rows to {csv_path}")

df['Promo Price'] = df['Price (Promo)'].apply(clean_price)
df['Original Price'] = df['Price (Original)'].apply(clean_price)
df['Discount %'] = ((df['Original Price'] - df['Promo Price']) / df['Original Price']) * 100
df['Discount %'] = df['Discount %'].round(2)

df['Reviews'] = df['Reviews'].replace('', pd.NA).fillna(0)
df['Rating'] = df['Rating'].replace('', pd.NA).fillna(0)

df['Reviews'] = df['Reviews'].replace('[^0-9]', '', regex=True).astype(float)
df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
df.dropna(subset=['Reviews', 'Rating', 'Discount %'], inplace=True)

# 📈 Smart review score (rating × log scale reviews)
df['Review_Score'] = df['Rating'] * np.log10(df['Reviews'] + 1)
df['Review_Score'] = df['Review_Score'].round(2)
# 🎯 Quantiles (rounded to 1 digit)
df['Review_Score_Quantile'] = df['Review_Score'].rank(pct=True).round(2)
df['Discount_Quantile'] = df['Discount %'].rank(pct=True).round(2)

# 🕒 Extract and format the unique timestamp from the 'Fetched At' column
try:
    unique_timestamp = df['Fetched At'].dropna().unique()[0]
    timestamp_dt = pd.to_datetime(unique_timestamp)
    timestamp_str = timestamp_dt.strftime('%Y-%m-%d %H:%M')
    title_with_time = f'🧠 UNIQLO Product Insights ({timestamp_str})'
except Exception as e:
    title_with_time = '🧠 UNIQLO Product Insights'
    print(f"⚠️ Could not format 'Fetched At' timestamp: {e}")

# 🏷️ Categorize products
def classify_action(row):
    r_q = row['Review_Score_Quantile']
    d_q = row['Discount_Quantile']


    if r_q >= 0.9 and d_q >= 0.80:
        return 'SUPER'
    elif r_q >= 0.9 and 0.5 <= d_q < 0.80:
        return 'WAIT FOR SALE'
    elif r_q >= 0.80 and d_q >= 0.80:
        return 'GOOD DEAL'
    elif r_q >= 0.80 and 0.4 <= d_q < 0.80:
        return 'DECENT'
    elif 0.7 <= r_q < 0.8 and d_q >= 0.8:
        return 'CHEAP UPPER MID'
    elif r_q < 0.5 and d_q >= 0.9:
        return 'CHEAP BUT MID'  # if clearer
    elif r_q < 0.3 and d_q < 0.3:
        return 'AVOID'
    else:
        return 'NEUTRAL'
        #if r_q >= 0.8 and d_q < 0.4:
        #    return 'TOP BUT EXPENSIVE'
        #elif 0.5 <= r_q < 0.8 and d_q >= 0.8:
        #    return 'FAIR DEAL'
        #elif 0.5 <= r_q < 0.8 and d_q < 0.8:
        #    return 'OK DEAL'   # clearer alternative to 'MID MID'
        #elif r_q < 0.5 and d_q < 0.9:
        #    return 'LOW QUALITY'  # clearer alternative to 'NOT TOP'
        #else:
        #    return 'NEUTRAL'
            
df['Action'] = df.apply(classify_action, axis=1)

# 🎯 Select best products based on Action
selected_actions = {'SUPER', 'GOOD DEAL', 'CHEAP UPPER MID'}
filtered_ids = df[df['Action'].isin(selected_actions)]['Product ID'].dropna().astype(str).tolist()

if True:
# 🧱 Load block list, don't want to use it know and here
    blocked_ids = {}
    if Path(BLOCK_PATH).exists():
        with open(BLOCK_PATH, 'r') as f:
            blocked_ids = json.load(f)
    print(blocked_ids )      
    filtered_ids = [pid for pid in filtered_ids if blocked_ids.get(pid) is not True]

# 📄 Load existing interested IDs
existing_ids = set()
if Path(TARGET_ID_PATH).exists():
    with open(TARGET_ID_PATH, 'r') as f:
        existing_ids = set(line.strip() for line in f if line.strip())

# ➕ Append new IDs (no duplicates)
updated_ids = sorted(existing_ids.union(filtered_ids))
with open(ID_PATH, 'w') as f:
    for pid in updated_ids:
        f.write(pid + '\n')

print(f"✅ Added {len(filtered_ids)} new IDs. Total now: {len(updated_ids)}")

# ✅ Optionally: Save enriched CSV
df.to_csv(CSV_PATH, index=False)
print(f"💾 Updated dataset with metrics saved to {CSV_PATH}")

save_or_append_df(df, 'product-ids/uniqlo-raw-history.csv')

# 🔍 Filter rows by Product ID
filtered_df = df[df['Product ID'].astype(str).isin(updated_ids)]

columns_to_drop = ['Price (Promo)', 'Price (Original)']
filtered_df_csv = filtered_df.drop(columns=[col for col in columns_to_drop if col in filtered_df.columns])


# 💾 Save filtered dataset
filtered_df_csv.to_csv(OUTPUT_CSV, index=False)

print(f"✅ Filtered {len(filtered_df)} rows out of {len(df)}")
print(f"📁 Saved filtered file to: {OUTPUT_CSV}")


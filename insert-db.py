import os
import re
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from supabase import create_client
from dotenv import load_dotenv

# 🔪 Load credentials
load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# 📦 CSV paths
DF_PRODUCTS = pd.read_csv("product-ids/uniqlo-products.csv")
DF_SIZES = pd.read_csv("product-ids/uniqlo-with-sizes.csv")
df_pre = pd.merge(DF_PRODUCTS, DF_SIZES[["Product ID", "Product URL", "Available Sizes"]], on=["Product ID", "Product URL"], how="left")
df_pre["Available Sizes"] = df_pre["Available Sizes"].fillna("Unknown")

def extract_color_code(url: str) -> str:
    try:
        path = urlparse(url).path.rstrip('/').split('/')[-1]
        color_param = parse_qs(urlparse(url).query).get("colorDisplayCode", [None])[0]
        return f"{path}{color_param}" if path and color_param else None
    except:
        return None


def upload_main_data(df):
    for _, row in df.iterrows():
        product_id = row["Product ID"]
        name = row["Product Name"]
        general_url = row["Product URL"]
        variant_url = row["Color Variant URLs"].split('|')[0].strip() if pd.notna(row["Color Variant URLs"]) else general_url
        color_code = extract_color_code(variant_url)
        #print(color_code)
        #print(variant_url)
        gender = "woman" if "/damen" in general_url.lower() else "man" if "/men" in general_url.lower() else "unknown"
        
        sizes_field = str(row.get("Available Sizes", "")).strip()
        #print(sizes_field)
        if sizes_field == "Unknown" or not sizes_field:
            sizes_field = f"{color_code}-X: Unknown"
            #print(sizes_field)

        if sizes_field == "Unavailable":
            sizes_field = f"{color_code}-X: Unavailable"
            #print(sizes_field)

        for block in sizes_field.split('|'):
            #print(block)
            match = re.match(r'(\d{4})-[^:]+:\s*(.+)', block.strip())
            if not match:
                print(f"⚠️ Failed to parse color block for {product_id}: {block}")
                continue

            color_code, size_str = match.groups()
            sizes = [s.strip() for s in size_str.split(',') if s.strip()]

            # 🔍 Insert or update parent
            parent_resp = supabase.table("parent").select("id", "name").eq("product_id", product_id).execute()
            if parent_resp.data:
                parent_id = parent_resp.data[0]["id"]
                if parent_resp.data[0]["name"] != name:
                    supabase.table("parent").update({"name": name}).eq("id", parent_id).execute()
            else:
                insert = supabase.table("parent").insert({
                    "product_id": product_id,
                    "name": name,
                    "gender": gender,
                    "general_url": general_url
                }).execute()
                parent_id = insert.data[0]["id"]

            for size in sizes:
                # 🎨 Insert variant if missing
                variant_resp = supabase.table("product_variants").select("id").match({
                            "parent_id": parent_id,
                            "color": color_code,
                            "size": size
                        }).execute()                
                if variant_resp.data:
                    variant_id = variant_resp.data[0]["id"]
                else:
                    insert = supabase.table("product_variants").insert({
                        "parent_id": parent_id,
                        "color": color_code,
                        "size": size,
                        "variant_url": variant_url
                    }).execute()
                    variant_id = insert.data[0]["id"]

                # 📊 Insert timeseries
                try:
                    supabase.table("timeseries_values").insert({
                        "variant_id": variant_id,
                        "promo_price": float(row["Promo Price"]),
                        "original_price": float(row["Original Price"]),
                        "rating": float(row["Rating"]),
                        "reviews": int(float(row["Reviews"])),
                        "discount_percent": float(row["Discount %"]),
                        "action": row["Action"],
                        "fetched_at": pd.to_datetime(row["Fetched At"]).isoformat()
                    }).execute()
                except Exception as e:
                    print(f"⚠️ Failed timeseries insert for {product_id}: {e}")


# 🚀 Run both
upload_main_data(df)

print("✅ Supabase sync complete.")

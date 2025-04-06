import pandas as pd
import argparse
import re
import os

# ✅ Default sizes to keep
DEFAULT_SIZES = {"M", "L", "XL", "26INCH", "27INCH", "28INCH", "29INCH", "39-42"}

def clean_and_extract_sizes(size_str):
    if pd.isna(size_str) or str(size_str).strip().lower() == 'unavailable':
        return set()

    size_str = re.sub(r'\s+', ' ', str(size_str)).strip()  # normalize whitespace

    all_sizes = set()
    for variant in size_str.split('|'):
        if ':' in variant:
            _, sizes_part = variant.split(':', 1)
        else:
            sizes_part = variant
        sizes = [s.strip().upper() for s in sizes_part.split(',') if s.strip()]
        all_sizes.update(sizes)
    return all_sizes

def should_keep(row, wanted_sizes):
    sizes_ok = not clean_and_extract_sizes(row['Available Sizes']).isdisjoint(wanted_sizes)
    discount_ok = pd.notna(row['Discount %']) and float(row['Discount %']) >= 50
    return sizes_ok and discount_ok

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


def main(input_csv, output_csv, wanted_sizes):
    df = pd.read_csv(input_csv)
    initial_count = len(df)

    df_filtered = df[df.apply(lambda row: should_keep(row, wanted_sizes), axis=1)]
    final_count = len(df_filtered)

    df_filtered.to_csv(output_csv, index=False)
    save_or_append_df(df_filtered, 'product-ids/verified-history.csv')

    print(f"✅ Kept {final_count} rows (from {initial_count}) based on size and discount ≥ 50%")
    print(f"📁 Saved to: {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter UNIQLO rows by size and discount")
    parser.add_argument("--input", default="uniqlo-products-with-sizes.csv", help="Input CSV path")
    parser.add_argument("--output", default="uniqlo-products-with-sizes-filtered.csv", help="Output CSV path")
    parser.add_argument("--sizes", nargs="*", default=list(DEFAULT_SIZES), help="Sizes to keep (e.g. M L XL)")

    args = parser.parse_args()
    main(args.input, args.output, set(s.upper() for s in args.sizes))

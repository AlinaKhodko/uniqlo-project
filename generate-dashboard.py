import pandas as pd
import numpy as np
import re
import argparse
import dash
from dash import Dash, dash_table, html
import dash_bootstrap_components as dbc

# 🎯 Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate UNIQLO product dashboard")
parser.add_argument('--csv', required=True, help='Path to input CSV file')
args = parser.parse_args()

CSV_PATH = args.csv

# 🧹 Load and clean product data
df = pd.read_csv(CSV_PATH)

df = pd.read_csv(CSV_PATH)

# Add hyperlink column for clickable product names in Dash
df['Name with Link'] = df.apply(
    lambda row: f"[ {row['Product Name']} ]({row['Product URL']})", axis=1
)

# Choose columns to show
columns = [
    {"name": "Product ID", "id": "Product ID"},
    {"name": "Name", "id": "Name with Link", "presentation": "markdown"},
    {"name": "Promo Price", "id": "Promo Price"},
    {"name": "Rating", "id": "Rating"},
    {"name": "Reviews", "id": "Reviews"},
    {"name": "Discount %", "id": "Discount %"},
    {"name": "Action", "id": "Action"},
    {"name": "Available Sizes", "id": "Available Sizes"},
]

# Create the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = dbc.Container([
    html.H2("💃💸 UNIQLO 🇯🇵🇺🇦 Best Deal Hunter 🎯", className="my-3"),
    dash_table.DataTable(
        columns=columns,
        data=df.to_dict("records"),
        style_cell={"textAlign": "left", "padding": "6px"},
        style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
        style_table={"overflowX": "auto"},
        markdown_options={"link_target": "_blank"},
        page_size=20,
        filter_action="native",
        sort_action="native"
    )
], fluid=True)

if __name__ == "__main__":
    app.run(debug=True)

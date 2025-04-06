import pandas as pd
import numpy as np
import re
import argparse
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 🎯 Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate UNIQLO product dashboard")
parser.add_argument('--csv', required=True, help='Path to input CSV file')
parser.add_argument('--output', required=True, help='Path to output HTML dashboard')
args = parser.parse_args()

CSV_PATH = args.csv
CHART_PATH = args.output

# 🧹 Load and clean product data
df = pd.read_csv(CSV_PATH)

# 🕒 Extract timestamp for the title
try:
    unique_timestamp = df['Fetched At'].dropna().unique()[0]
    timestamp_dt = pd.to_datetime(unique_timestamp)
    timestamp_str = timestamp_dt.strftime('%Y-%m-%d %H:%M')
    title_with_time = f'🧠 UNIQLO Product Insights ({timestamp_str})'
except Exception as e:
    title_with_time = '🧠 UNIQLO Product Insights'
    print(f"⚠️ Could not format 'Fetched At' timestamp: {e}")

# 🎨 Custom colors by action
color_map = {
    'SUPER': '#2ECC71',
    'GOOD DEAL': '#3498DB',
    'WAIT FOR SALE': '#F1C40F',
    'DECENT': '#95A5A6',
    'CHEAP BUT MID': '#E67E22',
    'AVOID': '#E74C3C',
    'NEUTRAL': '#D0D3D4'
}

# 📊 Count distribution
action_counts = df['Action'].value_counts().reset_index()
action_counts.columns = ['Action', 'Count']
action_counts['Color'] = action_counts['Action'].map(color_map)

# 📈 Bar chart
bar_fig = px.bar(
    action_counts.sort_values('Count'),
    x='Count',
    y='Action',
    orientation='h',
    text='Count',
    color='Action',
    color_discrete_map=color_map,
    title='🛍️ Product Count by Action Category',
    template='plotly_white',
    height=400
)
bar_fig.update_traces(textposition='outside')
bar_fig.update_layout(
    margin=dict(l=80, r=40, t=60, b=40),
    yaxis_title='',
    xaxis_title='Number of Products',
    showlegend=False
)

# 📋 Create tables for selected categories
categories_to_show = ['SUPER', 'GOOD DEAL', 'CHEAP BUT MID']
top_tables = []

# ✅ Conditionally add 'Available Sizes' if it exists in the DataFrame
if 'Available Sizes' in df.columns:
    for action in categories_to_show:
        subset = df[df['Action'] == action].sort_values(
            by=['Discount %', 'Review_Score'], ascending=[False, False]
        ).head(10)

        table = go.Table(
            header=dict(
                values=['Product ID', 'Name', 'Promo Price', 'Rating', 'Reviews', 'Discount %', 'Action', 'Available Sizes'],
                fill_color=color_map.get(action, '#CCCCCC'),
                font=dict(color='white'),
                align='left'
            ),
            cells=dict(
                values=[
                    subset['Product ID'],
                    subset['Product Name'],
                    subset['Promo Price'],
                    subset['Rating'],
                    subset['Reviews'],
                    subset['Discount %'],
                    subset['Action'],
                    subset['Available Sizes']

                ],
                align='left'
            )
        )
        top_tables.append((action, table))

else:
    for action in categories_to_show:
        subset = df[df['Action'] == action].sort_values(
            by=['Discount %', 'Review_Score'], ascending=[False, False]
        ).head(10)


        table = go.Table(
            header=dict(
                values=['Product ID', 'Name', 'Promo Price', 'Rating', 'Reviews', 'Discount %', 'Action'],
                fill_color=color_map.get(action, '#CCCCCC'),
                font=dict(color='white'),
                align='left'
            ),
            cells=dict(
                values=[
                    subset['Product ID'],
                    subset['Product Name'],
                    subset['Promo Price'],
                    subset['Rating'],
                    subset['Reviews'],
                    subset['Discount %'],
                    subset['Action']

                ],
                align='left'
            )
        )
        top_tables.append((action, table))

# 🧱 Combine bar chart and tables
fig = make_subplots(
    rows=1 + len(top_tables),
    cols=1,
    shared_xaxes=False,
    vertical_spacing=0.07,
    row_heights=[0.3] + [0.7 / len(top_tables)] * len(top_tables),
    specs=[[{"type": "xy"}]] + [[{"type": "table"}] for _ in top_tables]
)

# Row 1: Bar chart
for trace in bar_fig['data']:
    fig.add_trace(trace, row=1, col=1)

# Rows 2+: Tables
for idx, (title, table) in enumerate(top_tables):
    fig.add_trace(table, row=idx + 2, col=1)
    fig.add_annotation(
        text=f"Top 10 in {title}",
        showarrow=False,
        font=dict(size=14),
        xref='paper',
        yref='paper',
        x=0,
        y=1 - (idx + 1) * 0.25,
        xanchor='left',
        yanchor='top'
    )

fig.update_layout(
    height=1200,
    title=title_with_time,
    margin=dict(l=60, r=60, t=60, b=60),
    template='plotly_white'
)

# 💾 Save HTML
fig.write_html(CHART_PATH)
print(f"📊 Dashboard saved to {CHART_PATH}")



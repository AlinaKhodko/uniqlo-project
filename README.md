# 🛍️ UNIQLO Deal Tracker Automation

Automatically scrapes the latest UNIQLO women’s sale items, filters the best deals, tracks sizes, generates visual insights, and notifies you via Telegram — all on a scheduled GitHub Actions workflow.

## 🔧 Features

- ✅ Scrapes UNIQLO sale product listings using Puppeteer
- ✅ Parses HTML to extract product details and variants
- ✅ Calculates smart review + discount scores
- ✅ Filters out items based on:
  - Too small/large sizes (`XS`, `XXL`, etc.)
  - Low discounts
  - Blocked color variants (e.g. "only ROSA")
-  Generates a [Plotly/Dash dashboard](https://plotly.com/dash/) with:
  - Review vs. Discount categorization
  - Product tables by best score
- ✅ Sends Telegram alerts with direct product links

---

## 🚀 How It Works

### Workflow Trigger

The automation runs:
- 🕒 Every 30 minutes (`cron`), or
- 🔘 Manually (via GitHub Actions "Run Workflow")

### Workflow Steps

1. `fetch-html.js`: Scrape raw HTML from UNIQLO site
2. `html-to-csv.js`: Parse product list to `uniqlo-products.csv`
3. `deal-filter.py`: Calculate scores, categories, and enrich the dataset
4. `fetch-sizes.js`: Scrape available sizes per color
5. `filter-sizes.py`: Remove unwanted sizes and low-discount items
6. `send-telegram.py`: Sends a nice message with new deal links

### Folder Structure
```
---
├── data/                      # 📂 Data and dashboards
│   ├── uniqlo-raw.html        # 🧼 Raw HTML
│   ├── uniqlo-products.csv    # 📦 Parsed CSV
│   ├── sizes-filtered.csv     # 🎯 Final filtered dataset
├── plots/                      # 📂 Data and dashboards
│   ├── general_overview.html  # 📈 Plotly dashboard
│   ├── filtered_overview.html  # 📈 Plotly dashboard
│   ├── verified_overview.html  # 📈 Plotly dashboard
├── product-ids/               # 📂 Products
│   ├── blocked_colors.json        # 🚫 Color blacklist
│   ├── interested-product-ids.txt # 💡 Best product memory
│   ├── target-ids.txt
├── fetch-html.js              # ⬇️ Scraper script
├── html-to-csv.js             # 🧠 Extract product rows
├── fetch-sizes.js             # 📏 Scrape available sizes
├── deal-filter.py             # 🧮 Score and categorize
├── filter-sizes.py            # 🧹 Drop weak rows
├── send-telegram.py           # 📩 Telegram notifications
├── requirements.txt           # 📦 Python dependencies
└── .github/
    └── workflows/
        └── main.yml           # ⚙️ GitHub Actions
```

⚠️ Disclaimer
This project is not affiliated with, endorsed by, or in any way officially connected with UNIQLO or its affiliates.
All product names, logos, and brands are property of their respective owners.

The tool respects robots.txt directives and does not access restricted or user-authenticated areas of the website.
No personal data is collected, stored, or processed.

Use of this tool is intended strictly for personal, lawful, and non-commercial purposes.

MIT

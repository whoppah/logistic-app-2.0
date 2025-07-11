# logistic-app-2.0

In the `backend/logistics` are the core backend modules responsible for **parsing**, **computing Delta**, and **processing logistics invoices** with order data pulled from the CMS database. It computes price discrepancies (Δ - Delta) between what partners billed and what should have been charged based on internal pricing logic (in JSON format 'backend/logistics/pricing_data').

---

## Purpose

- **Process invoices from logistics partners**
- **Extract and parse data** from PDFs and Excel sheets
- **Query CMS (PostgreSQL)** for matching order info
- **Apply pricing models** (JSON-based or logic-driven)
- **Compute Δ (Delta)** per item
- **Export results** to Google Sheets
- **React to Slack uploads** with ✅ or 🟥

---

## Structure Overview

The module is functionally divided into:

| Layer                     | Description                                                              |
|--------------------------|--------------------------------------------------------------------------|
| Parsers                  | Read & format raw invoice files (PDF/XLSX)                               |
| Delta computation        | Calculate the delta using CMS data and expected pricing                 |
| CMS data access          | Extract live order data using SQLAlchemy and retry logic                 |
| Google Sheets export     | Format and upload delta results to Google Sheets                        |
| Slack integration        | Monitor, download, process, and react to invoice uploads                |
| Django backend           | API                                                                     |
| React .jsx app           | Frontend                                                                | 
| Task queue (Celery)      | Async file processing for dashboard and Slack-based ingestion           |

---

## Backend structure

### 1. Invoice Parsing Functions

Each logistics partner has its own parsing logic tailored to their file formats.

| Function | Input Type | Description |
|---------|------------|-------------|
| `brenger_read_pdf()` | PDF from Redis | Extracts Brenger invoice line items and totals |
| `magic_movers_read_xlsx()` | Excel from Redis | Parses Magic Movers Excel and classifies items |
| `wuunder_read_pdf()` | PDF | Handles multi-line, nested Wuunder invoice items |
| `libero_logistics_read_xlsx()` | Excel + PDF | Reads Excel and gets metadata from PDF |
| `swdevries_read_xlsx()` | Excel | Reads Swdevries invoice with dynamic headers |
| `transpoksi_read_pdf()` | PDF | Simple PDF reader with totals verification |

All parsers:
- Load files from Redis
- Parse invoice metadata (dates, totals)
- Clean and normalize data
- Format into `pandas.DataFrame`

---

### 2. Delta Calculation

Each partner has specific delta calculation rules. Deltas represent overcharges or mismatches between billed and expected pricing.

| Function | Description |
|----------|-------------|
| `compute_delta_brenger()` | Joins CMS + invoice by ID and uses pricing JSON |
| `compute_delta_magic_movers()` | Uses internal logic (transport, surcharges, packing) |
| `compute_delta_wuunder()` | Compares to `shipping_excl_vat` in CMS |
| `compute_delta_other_partners()` | Generic matcher using JSON rules, time-aware |
| `germany_price_libero_logistics()` | Special pricing override for German routes |

Delta summary is appended to result:
- ✅ If `sum(Δ) <= threshold`
- 🟥 Otherwise

---

### 3. CMS Order Extraction

| Function | Description |
|----------|-------------|
| `get_df_from_query_db(partner)` | Builds a dynamic PostgreSQL query using SQLAlchemy |
| `execute_query_with_retries()` | Retry logic for transient DB errors |

The query returns:
- Order metadata
- Product category
- Dimensions, weight, etc.
- External courier info
- Shipping cost from CMS

---

### 4. Export to Google Sheets

| Function | Description |
|----------|-------------|
| `export_to_spreadsheet(df, partner)` | Creates or appends to a Google Sheet and highlights Δ rows |

- Authenticated via Service Account key
- Each partner has a tab
- Yellow highlight on positive delta rows

---

### 5. Slack Automation

| Function | Description |
|----------|-------------|
| `download_file(file_id)` | Downloads file from Slack to Redis |
| `check_condition_and_react()` | Processes recent Slack messages and reacts ✅ / 🟥 |
| `check_delta_in_dataframe()` | Core handler for calling invoice + delta logic |
| `extract_partner(msg)` | Regex matcher for “Partner: X” from Slack text |

---

### 6. Flask & Celery Routes

| Route | Description |
|-------|-------------|
| `/upload` | Upload files via web UI |
| `/run-process` | Trigger Slack scan manually |
| `/launch-dashboard` | Cache results in Redis and launch dashboard |
| `/api/dashboard/<id>` | Returns JSON of dashboard view |
| `/check-task-status` | Polled by frontend to show progress |
| `/show-data` | HTML rendering of results |

---
## Dashboard (React Frontend)

The dashboard is a single-page React app served statically by Flask.

- Shows per-partner Delta summaries (e.g., total overcharges)
- Interactive bar chart (built with Recharts)
- Route: `/dash/:dashboardId` (data is pulled from Redis)

To use:
- Upload invoice(s)
- Visit `http://localhost:5000/launch-dashboard`
- You'll be redirected to a live dashboard view for that dataset

## Dev Setup

```bash
# Install Python deps
pip install -r requirements.txt

# Set env variables
cp logistics.env.example logistics.env
# Edit secrets accordingly

# Start services
redis-server
celery -A facturen_logistiek worker --loglevel=info
python app.py



# Banking Customer & Transaction Analytics Dashboard
> **A Business Intelligence & Data Analytics Portfolio Project**

An end-to-end data analytics dashboard that cleans banking customer and transaction records, stores them in an indexed relational SQLite database, computes multi-dimensional SQL and Pandas KPIs, and delivers interactive visual analytics and automated business insights via Streamlit.

---

## 1. Project Overview
This project simulates an operational Business Intelligence system for a retail and commercial banking environment. It tracks customer demographics, payment channel performance, branch-level volumes, transaction failure rates, and rule-based customer segments across synthetic Indian banking data.

The project is structured to demonstrate a complete, human-engineered analytics lifecycle from raw data collection to executive dashboarding.

---

## 2. Problem Statement
Retail banks process tens of thousands of transactions daily across multiple payment channels (UPI, Cards, ATMs, NEFT, IMPS). Operations teams and business leaders struggle with:
- Monitoring transaction failure rates and spotting channel bottlenecks.
- Understanding which branches and cities drive deposit and transaction volumes.
- Identifying high-value customers versus dormant accounts for targeted retention.
- Converting raw log extracts into clean, actionable executive metrics.

---

## 3. Objectives
- Build a reproducible **data cleaning pipeline** in Pandas that handles duplicates, string anomalies, nulls, and negative values.
- Design a relational schema in **SQLite** with primary/foreign keys and analytical indexing.
- Implement **14 production-grade SQL analytical queries** for operational and executive KPIs.
- Construct an **interactive Streamlit dashboard** with responsive filters, Plotly visualizations, and customer segmentation.
- Generate **dynamic, data-backed business insights** that adapt to filter selections without hardcoding assumptions.

---

## 4. Tech Stack
- **Language**: Python 3.10+
- **Data Manipulation**: Pandas, NumPy
- **Database & Querying**: SQLite, SQL
- **Dashboard & Visualization**: Streamlit, Plotly Express & Graph Objects
- **Cloud & Deployment**: Docker, Google Cloud Run, Streamlit Community Cloud
- **Version Control**: Git, GitHub

---

## 5. Data Pipeline Architecture

```text
+-----------------------+
|  Raw Data Generator   |
| (data/raw/*.csv)      |
+-----------+-----------+
            |
            v
+-----------------------+
|   Pandas Cleaning     |
| (src/data_cleaning.py)|  --> Checks shape, nulls, duplicates, invalid values
+-----------+-----------+
            |
            v
+-----------------------+
|   Database Storage    |
| (database/banking.db) |  --> SQLite relational tables with foreign keys & indexes
+-----------+-----------+
            |
            +------------------------------+
            |                              |
            v                              v
+-----------------------+      +-----------------------+
|     SQL Analytics     |      |   Python Analytics    |
| (sql/analytics.sql)   |      | (src/analytics.py)    |
+-----------+-----------+      +-----------+-----------+
            |                              |
            +--------------+---------------+
                           |
                           v
            +------------------------------+
            |     Streamlit Dashboard      |
            |          (app.py)            |
            +--------------+---------------+
                           |
                           v
            +------------------------------+
            |   Dynamic Business Insights  |
            |     (src/insights.py)        |
            +------------------------------+
```

---

## 6. Dataset Description
The dataset contains two realistic synthetic tables generated with reproducible distributions:

### Customers (`customers.csv` / `customers` table)
- `customer_id`: Unique identifier (e.g., `CUST00001`)
- `age`: Customer age (18 to 72)
- `gender`: Male, Female, Other
- `city`: Realistic Indian cities (Delhi, Mumbai, Bangalore, Hyderabad, Kolkata, Ranchi, Patna, Pune, Chennai, Ahmedabad)
- `occupation`: Salaried, Self-Employed, Business, Student, Retired, Freelancer
- `account_type`: Savings, Current, Salary
- `customer_since`: Account opening date (2020–2026)

### Transactions (`transactions.csv` / `transactions` table)
- `transaction_id`: Unique transaction code (e.g., `TXN0000001`)
- `customer_id`: Foreign key reference to customer
- `transaction_date`: Timestamp of transaction
- `transaction_type`: UPI, Card, ATM, NEFT, IMPS
- `amount`: Transaction amount in ₹
- `transaction_status`: Success, Failed, Pending
- `channel`: Mobile, Internet, ATM, Branch
- `branch`: City branch location

---

## 7. Data Cleaning Pipeline (`src/data_cleaning.py`)
Demonstrates core Pandas wrangling operations:
- **Deduplication**: Drops duplicate customer and transaction records via `.drop_duplicates()`.
- **String Standardization**: Trims whitespace and normalizes categorical casing using `.str.strip().str.title()` and `.str.upper()`.
- **Missing Value Imputation**: Imputes unrecorded customer occupations with `'Other / Unspecified'` and digital branches with `'Digital / Central Processing'`.
- **Numeric Validation**: Filters out erroneous negative and zero transaction amounts (`amount > 0`).
- **Date Conversion**: Parses inconsistent date formats safely with `pd.to_datetime(format='mixed', errors='coerce')`.
- **Referential Integrity**: Validates that all transactions map to an existing customer record.

---

## 8. Database Design (`src/database.py`)
The SQLite schema creates two relational tables with active foreign key constraints:

```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    city TEXT NOT NULL,
    occupation TEXT NOT NULL,
    account_type TEXT NOT NULL,
    customer_since TEXT NOT NULL
);

CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    amount REAL NOT NULL,
    transaction_status TEXT NOT NULL,
    channel TEXT NOT NULL,
    branch TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);
```

Indexes are created on `transactions(customer_id)`, `transactions(transaction_date)`, `transactions(transaction_type)`, `transactions(transaction_status)`, and `transactions(channel)` for sub-millisecond query performance.

---

## 9. SQL Analysis (`sql/analytics_queries.sql`)
Includes 14 dedicated business queries answering key managerial questions:
1. **Total Transaction Value**: Cumulative financial volume from successful transactions.
2. **Total Transaction Count**: Overall throughput.
3. **Successful Transaction Count**: Completed volume.
4. **Failed Transaction Count**: Error monitoring.
5. **Average Transaction Value**: Average ticket size.
6. **Monthly Transaction Value**: Month-over-month volume and financial trends.
7. **Transaction Value by Type**: Breakdown across UPI, Cards, ATM, NEFT, IMPS.
8. **Transaction Value by Branch**: Branch performance rankings.
9. **Top 10 Customers**: Identification of highest-spending accounts.
10. **Customer Activity**: Frequency and recency per customer.
11. **Active vs Inactive Customer Counts**: Account utilization rate.
12. **Failed Transaction Rate by Channel**: Pinpointing gateway issues.
13. **Transactions by Channel**: Channel share breakdown.
14. **City-wise Customer Distribution**: Geographic market penetration.

---

## 10. Dashboard Features (`app.py`)
- **Interactive Sidebar Filters**:
  - Date Range picker
  - Multi-select for City, Branch, Transaction Type, Status, and Channel
  - Instant Filter Reset button
- **Executive Metric Cards**:
  - Total Customers, Active Customers (% of total), Total Transactions, Total Value (₹), Average Value (₹), and Success Rate (%)
- **Section 1: Transaction Overview**:
  - Monthly transaction value line chart
  - Monthly transaction count bar chart
- **Section 2: Transaction Analysis**:
  - Payment type value distribution
  - Channel share donut chart
  - Success vs Failed vs Pending status breakdown
- **Section 3: Branch & Location Analysis**:
  - Horizontal bar chart of branch transaction volume
  - City customer count breakdown
- **Section 4: Customer Analysis & Segmentation**:
  - Top 10 Spenders table with demographics
  - Customer segmentation distribution donut chart and summary table
- **Section 5: Dynamic Business Insights**:
  - Automated diagnostic takeaways derived from current filtered data
- **Data Export**:
  - Download filtered transactional dataset as CSV

---

## 11. Customer Segmentation Rules
Implemented in `src/analytics.py` using business logic:
- 🌟 **High Value**: Total spend ≥ ₹40,000 AND transaction frequency ≥ 5
- 👤 **Regular**: Total spend ≥ ₹5,000 OR transaction frequency ≥ 3
- ⏳ **Low Activity**: Total spend < ₹5,000 with 1–2 transactions
- 💤 **Inactive**: 0 successful transactions in the selected period

---

## 12. Project Structure
```text
banking-bi-dashboard/
├── app.py                     # Main Streamlit web application
├── requirements.txt           # Minimal Python dependencies
├── Dockerfile                 # Container setup for Google Cloud Run
├── README.md                  # Comprehensive documentation
├── INTERVIEW_NOTES.md         # 17 technical interview questions & answers
├── .gitignore                 # Secrets and artifact exclusion
├── .streamlit/
│   └── config.toml            # Theme and styling configuration
├── data/
│   ├── raw/                   # Raw generated CSV files
│   │   ├── customers.csv
│   │   └── transactions.csv
│   └── processed/             # Cleaned CSV files
│       ├── customers_cleaned.csv
│       └── transactions_cleaned.csv
├── database/
│   └── banking.db             # Local SQLite database
├── sql/
│   └── analytics_queries.sql  # 14 documented SQL analytical queries
└── src/
    ├── generate_data.py       # Synthetic data generation script
    ├── data_cleaning.py       # Pandas cleaning & validation pipeline
    ├── database.py            # SQLite schema, data loader, & health check
    ├── analytics.py           # Metrics, aggregations, & customer segmentation
    └── insights.py            # Dynamic data-driven insights engine
```

---

## 13. How to Run Locally

### Prerequisites
- Python 3.10 or higher
- Git

### Step-by-Step Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/banking-bi-dashboard.git
   cd banking-bi-dashboard
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate synthetic data & run cleaning pipeline**:
   ```bash
   python src/generate_data.py
   python src/data_cleaning.py
   ```

5. **Initialize SQLite database & load clean data**:
   ```bash
   python src/database.py
   ```

6. **Launch the Streamlit Dashboard**:
   ```bash
   python -m streamlit run app.py
   ```
   Open `http://localhost:8501` in your browser.

---

## 14. Deployment Architecture

### Architecture Reality Check
Streamlit is an active Python server application requiring WebSocket support and a running Python process. Because of this, it cannot be hosted as a static website on simple static file hosts.

### Recommended Deployment Options
1. **Streamlit Community Cloud**:
   - Push repository to GitHub.
   - Connect repository directly at [share.streamlit.io](https://share.streamlit.io).
   - Set entry point to `app.py`.

2. **Google Cloud Run (Containerized)**:
   - Build and submit the container image:
     ```bash
     gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/banking-dashboard
     ```
   - Deploy to Cloud Run:
     ```bash
     gcloud run deploy banking-dashboard \
       --image gcr.io/YOUR_PROJECT_ID/banking-dashboard \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated \
       --port 8501
     ```

---

## 15. Future Improvements
- **Automated Airflow DAGs**: Schedule daily data extraction and cleaning jobs.
- **Data Warehouse Migration**: Migrate database layer to Google BigQuery or Snowflake for 10M+ transaction scale.
- **Alert Notifications**: Integrate Slack/Email webhooks when channel failure rates exceed 8%.
- **Cohort Analysis**: Add customer retention cohorts tracking month-by-month transaction activity.

---

## 16. Resume-Ready Project Entry

```text
Banking Customer & Transaction Analytics Dashboard
Python | Pandas | SQL | SQLite | Streamlit | Plotly

• Built an interactive banking analytics dashboard analyzing 5,000 customers and 39,988 transactions across transaction types, channels, branches and locations.
• Cleaned and transformed customer and transaction data using Pandas and stored structured data in SQLite for analytical querying.
• Used SQL and Python to calculate transaction KPIs, customer activity, branch performance, transaction success rates and customer segments.
• Developed an interactive Streamlit dashboard with filters, KPI cards, visualizations and dynamically generated data-driven business insights.
```

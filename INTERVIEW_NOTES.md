# Interview Preparation Notes
## Banking Customer & Transaction Analytics Dashboard

This document provides clear, realistic, student-level answers to 17 common technical and behavioral questions about this project. These answers reflect the actual code and architecture implemented in the repository, making them easy to explain and defend in an internship interview.

---

### 1. Why did you choose this project?
"I wanted to build an end-to-end data project that reflects a realistic Business Intelligence workflow rather than just training an isolated machine learning model. In commercial banking, executives and branch managers don't need complex black-box algorithms to make daily decisions—they need reliable, clean operational metrics: which channels have high failure rates, which branches process the highest transaction value, and how customer segments behave over time. This project allowed me to demonstrate every layer of the BI lifecycle: raw data generation, Pandas data cleaning, relational modeling in SQLite, SQL analytical queries, interactive Streamlit visualization, and data-backed business insights."

---

### 2. What is Business Intelligence (BI)?
"Business Intelligence is the practice of combining data collection, data storage, data transformation, and data visualization to translate raw operational data into actionable business decisions. Unlike predictive modeling which attempts to forecast future events, BI focuses on diagnostic and descriptive analytics: understanding what happened, where bottlenecks or transaction volume concentrations exist, and why certain KPIs are fluctuating."

---

### 3. Why did you use Pandas?
"Pandas is the industry standard for exploratory data analysis (EDA) and data wrangling in Python. I used it during the ingestion and preprocessing stage (`src/data_cleaning.py`) to perform operations that are awkward or verbose in pure SQL—such as parsing mixed date formats, stripping irregular whitespace from text fields, identifying and imputing missing categorical attributes, detecting duplicate rows, and validating numeric thresholds before loading clean records into the database."

---

### 4. Why did you use SQL?
"SQL is the universal language of relational databases and enterprise data warehouses. Using SQL allowed me to model data with clear referential integrity (primary keys and foreign keys), create indexes for rapid lookups, and execute structured analytical aggregations. Writing clean SQL queries (`sql/analytics_queries.sql`) demonstrates that I can compute multi-dimensional metrics using `GROUP BY`, conditional `CASE` statements, and table `JOIN`s, which is a core requirement for any BI role."

---

### 5. Why SQLite?
"SQLite was the ideal database choice for this project for three key reasons:
1. **Zero configuration & zero latency**: SQLite runs serverless in-process, requiring no external database server or daemon setup.
2. **Standard SQL compliance**: It supports standard relational schemas, foreign keys, transaction ACID properties, and SQLite date/time functions.
3. **Portability**: The entire database lives in a single portable file (`database/banking.db`), making the project 100% reproducible for evaluators and interviewers running it locally."

---

### 6. What is the difference between Pandas and SQL?
| Feature | SQL | Pandas |
| :--- | :--- | :--- |
| **Execution Location** | Runs inside the database engine; highly optimized for disk storage, indexes, and large sets. | Runs entirely in-memory within Python. |
| **Schema Enforcement** | Strict schemas, constraints, types, and referential integrity (PK/FK). | Flexible DataFrame structure; dynamic type coercion. |
| **Use Case in this Project** | Analytical querying, multi-table joins, and persistent structured storage. | Data wrangling, messy text cleaning, date parsing, and dynamic filter manipulation for the UI. |

---

### 7. How did you clean the data?
"In `src/data_cleaning.py`, I followed a systematic pipeline:
1. **Deduplication**: Identified and dropped duplicate customer IDs and duplicate transaction IDs using `drop_duplicates()`.
2. **String Standardization**: Stripped leading/trailing whitespace and standardized casing across cities, channels, and transaction types using `.str.strip().str.title()` and `.str.upper()`.
3. **Date Parsing**: Converted mixed date formats into standardized ISO timestamps using `pd.to_datetime()` with `errors='coerce'`.
4. **Validation**: Filtered out erroneous records such as negative or zero transaction amounts (`amount > 0`).
5. **Referential Integrity**: Verified that every transaction references a valid `customer_id` present in the customers table, filtering any orphaned records."

---

### 8. How did you handle missing values?
"I applied domain-appropriate strategies rather than blindly dropping rows:
- For **customer occupation**, where values were occasionally omitted, I imputed missing records with `'Other / Unspecified'` rather than discarding valid customer demographics.
- For **branch names on pure digital transactions** (such as mobile UPI or web portal transfers), missing branch entries were categorized under `'Digital / Central Processing'`.
- For **corrupted critical fields** (e.g. unparseable dates or negative amounts), those invalid rows were filtered out to maintain data accuracy."

---

### 9. What KPIs did you calculate?
"The dashboard calculates six top-level executive KPIs:
1. **Total Customers**: Count of registered customer accounts in the filtered scope.
2. **Active Customers**: Count of distinct customers with at least one transaction in the selected window.
3. **Total Transactions**: Total transaction requests initiated.
4. **Total Transaction Value**: Cumulative sum of successful transaction amounts (in ₹).
5. **Average Transaction Value**: Mean ticket size per successful transaction.
6. **Transaction Success Rate**: Percentage of transactions with `'Success'` status vs `'Failed'` and `'Pending'`."

---

### 10. How did you calculate transaction success rate?
"Using both SQL and Python:
- **In SQL**:
  ```sql
  ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Success' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct
  ```
- **In Python (`src/analytics.py`)**:
  ```python
  success_rate = (len(successful_txns) / total_transactions) * 100.0
  ```
I also computed the reciprocal **Failure Rate** and broken it down by payment channel to pinpoint operational vulnerabilities."

---

### 11. How did you create customer segments?
"I created a simple, explainable, rule-based segmentation model based on customer behavior:
- **High Value**: Total spend ≥ ₹40,000 AND transaction frequency ≥ 5.
- **Regular**: Total spend between ₹5,000 and ₹40,000, OR frequency ≥ 3.
- **Low Activity**: Total spend < ₹5,000 with 1–2 transactions.
- **Inactive**: Registered customers with 0 successful transactions in the analyzed period.

I deliberately chose a transparent business-rules approach over an opaque K-Means algorithm because in commercial banking, business stakeholders need clear, deterministic criteria that can be directly mapped to marketing strategies."

---

### 12. Why Streamlit?
"Streamlit allowed me to build an interactive, data-driven web application entirely in Python without needing a heavy JavaScript frontend framework like React. It natively supports reactive state: when a user changes a sidebar filter (e.g. selecting a branch or date range), the downstream KPIs, Plotly figures, and insights automatically recompute in real time."

---

### 13. What business decisions can the dashboard support?
1. **Channel Reliability & IT Operations**: Highlighting channels with elevated failure rates (e.g., ATM or UPI gateway outages) allows engineering teams to investigate network latencies.
2. **Branch Resource Allocation**: Identifying branches with high transaction volumes helps regional managers allocate tellers and cash reserves effectively.
3. **Targeted Retention Marketing**: Highlighting inactive or low-activity customers enables automated re-engagement campaigns (e.g., cashback on first UPI transaction).
4. **VIP Relationship Management**: The Top 10 Spenders view allows relationship managers to prioritize premium wealth-management services for high-net-worth accounts."

---

### 14. What challenges did you face?
"Two key challenges stood out:
1. **Handling Inconsistent Raw Formats**: Simulating real-world transaction logs meant dealing with inconsistent date formats and whitespace. I had to ensure our Pandas cleaning script parsed dates robustly with fallback handling.
2. **Dynamic Insights Logic**: Ensuring the 'Business Insights' section was genuinely dynamic rather than hardcoded text. If an executive filters by 'Card' and 'Mumbai', the bullet points must accurately identify the top-performing branch and failure rate specific to that slice of data."

---

### 15. How would you scale the project?
"If moving from a local student project to a commercial bank scale:
1. **Database Migration**: Move from local SQLite to PostgreSQL or a cloud data warehouse like Google BigQuery or Snowflake.
2. **Automated ETL Pipeline**: Use an orchestration tool like Apache Airflow or Prefect to run nightly batch cleaning jobs.
3. **Caching & Pre-aggregation**: Pre-compute daily/monthly summary tables (materialized views) so the dashboard queries small aggregated tables instead of scanning raw transaction logs."

---

### 16. Why would a bank use a BI dashboard?
"Banking generates millions of transactions across disparate payment rails (ATM, UPI, POS, NEFT, IMPS). Without a centralized BI dashboard, executives and operational heads cannot see cross-channel trends, identify gateway drop-offs, track branch transaction volumes, or monitor customer dormancy. A BI dashboard provides a single source of truth for informed decision-making."

---

### 17. What would you change if the dataset had 100 million rows?
"At 100 million rows:
1. **Storage**: In-memory Pandas and SQLite would bottleneck. I would store raw logs in cloud object storage (S3 / Google Cloud Storage) partitioned by date (`year=YYYY/month=MM`).
2. **Processing**: Replace single-node Pandas with distributed compute like PySpark or SQL pushdown in BigQuery / DuckDB.
3. **Data Modeling**: Implement a Star Schema with a central Transaction Fact table and Customer/Branch Dimension tables.
4. **Dashboard Layer**: Query indexed aggregate tables or a BI semantic layer so the dashboard loads in under 2 seconds."

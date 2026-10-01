-- ==============================================================================
-- Banking Customer & Transaction Analytics Dashboard
-- Core Analytical SQL Queries
-- Database: SQLite
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 1: Total Transaction Value (Overall Volume in Currency)
-- Used In: KPI Cards (Main Dashboard Header)
-- ------------------------------------------------------------------------------
SELECT 
    ROUND(SUM(amount), 2) AS total_transaction_value
FROM transactions
WHERE transaction_status = 'Success';


-- ------------------------------------------------------------------------------
-- Query 2: Total Transaction Count
-- Used In: KPI Cards (Main Dashboard Header)
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_transactions
FROM transactions;


-- ------------------------------------------------------------------------------
-- Query 3: Successful Transaction Count
-- Used In: KPI Cards & Success/Failure Overview
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS successful_transactions
FROM transactions
WHERE transaction_status = 'Success';


-- ------------------------------------------------------------------------------
-- Query 4: Failed Transaction Count
-- Used In: Risk / Operations Monitoring
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS failed_transactions
FROM transactions
WHERE transaction_status = 'Failed';


-- ------------------------------------------------------------------------------
-- Query 5: Average Transaction Value (Ticket Size)
-- Used In: KPI Cards
-- ------------------------------------------------------------------------------
SELECT 
    ROUND(AVG(amount), 2) AS avg_transaction_value
FROM transactions
WHERE transaction_status = 'Success';


-- ------------------------------------------------------------------------------
-- Query 6: Monthly Transaction Value & Volume Trend
-- Used In: Section 1 - Transaction Overview (Trend Line / Bar Chart)
-- ------------------------------------------------------------------------------
SELECT 
    strftime('%Y-%m', transaction_date) AS month,
    COUNT(*) AS total_transactions,
    ROUND(SUM(CASE WHEN transaction_status = 'Success' THEN amount ELSE 0 END), 2) AS total_value,
    ROUND(AVG(CASE WHEN transaction_status = 'Success' THEN amount ELSE NULL END), 2) AS avg_value
FROM transactions
GROUP BY month
ORDER BY month ASC;


-- ------------------------------------------------------------------------------
-- Query 7: Transaction Value & Count by Transaction Type
-- Used In: Section 2 - Transaction Analysis (UPI, Card, ATM, NEFT, IMPS Breakdown)
-- ------------------------------------------------------------------------------
SELECT 
    transaction_type,
    COUNT(*) AS txn_count,
    ROUND(SUM(amount), 2) AS total_amount,
    ROUND(AVG(amount), 2) AS avg_amount,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM transactions), 2) AS volume_share_pct
FROM transactions
WHERE transaction_status = 'Success'
GROUP BY transaction_type
ORDER BY total_amount DESC;


-- ------------------------------------------------------------------------------
-- Query 8: Transaction Value by Branch
-- Used In: Section 3 - Branch / Location Analysis
-- ------------------------------------------------------------------------------
SELECT 
    branch,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_branch_value,
    ROUND(AVG(amount), 2) AS avg_branch_amount
FROM transactions
WHERE transaction_status = 'Success'
GROUP BY branch
ORDER BY total_branch_value DESC;


-- ------------------------------------------------------------------------------
-- Query 9: Top 10 Customers by Transaction Value
-- Used In: Section 4 - Customer Analysis (High-Net-Worth Identification Table)
-- ------------------------------------------------------------------------------
SELECT 
    c.customer_id,
    c.city,
    c.occupation,
    c.account_type,
    COUNT(t.transaction_id) AS total_transactions,
    ROUND(SUM(t.amount), 2) AS total_spend
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.transaction_status = 'Success'
GROUP BY c.customer_id, c.city, c.occupation, c.account_type
ORDER BY total_spend DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- Query 10: Customer Activity (Distribution of Transactions per Customer)
-- Used In: Section 4 - Customer Activity Analysis
-- ------------------------------------------------------------------------------
SELECT 
    c.customer_id,
    c.city,
    c.account_type,
    COUNT(t.transaction_id) AS transaction_count,
    ROUND(COALESCE(SUM(t.amount), 0), 2) AS total_amount,
    MAX(t.transaction_date) AS last_transaction_date
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id, c.city, c.account_type
ORDER BY transaction_count DESC;


-- ------------------------------------------------------------------------------
-- Query 11: Number of Active vs Inactive Customers
-- Active defined as having at least one successful transaction in the database period
-- Used In: KPI Cards & Customer Segmentation Overview
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT customer_id) AS active_customers,
    (SELECT COUNT(*) FROM customers) - COUNT(DISTINCT customer_id) AS inactive_customers,
    ROUND(100.0 * COUNT(DISTINCT customer_id) / (SELECT COUNT(*) FROM customers), 2) AS active_rate_pct
FROM transactions
WHERE transaction_status = 'Success';


-- ------------------------------------------------------------------------------
-- Query 12: Failed Transaction Rate by Channel
-- Used In: Operational Health & Risk Insights
-- ------------------------------------------------------------------------------
SELECT 
    channel,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) AS failed_count,
    ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Success' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct
FROM transactions
GROUP BY channel
ORDER BY failure_rate_pct DESC;


-- ------------------------------------------------------------------------------
-- Query 13: Transactions by Channel Distribution
-- Used In: Section 2 - Channel Distribution Donut/Bar Chart
-- ------------------------------------------------------------------------------
SELECT 
    channel,
    COUNT(*) AS txn_count,
    ROUND(SUM(amount), 2) AS total_value,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM transactions), 2) AS percentage_share
FROM transactions
GROUP BY channel
ORDER BY txn_count DESC;


-- ------------------------------------------------------------------------------
-- Query 14: City-wise Customer Distribution & Account Penetration
-- Used In: Section 3 - Geographic Customer Reach
-- ------------------------------------------------------------------------------
SELECT 
    city,
    COUNT(*) AS total_customers,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customers), 2) AS city_customer_pct,
    SUM(CASE WHEN account_type = 'Savings' THEN 1 ELSE 0 END) AS savings_count,
    SUM(CASE WHEN account_type = 'Salary' THEN 1 ELSE 0 END) AS salary_count,
    SUM(CASE WHEN account_type = 'Current' THEN 1 ELSE 0 END) AS current_count
FROM customers
GROUP BY city
ORDER BY total_customers DESC;

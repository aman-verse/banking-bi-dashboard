"""
Banking Customer & Transaction Analytics Dashboard
Python Analytics & Customer Segmentation Module

Provides core data transformations, metric calculations, and
explainable rule-based customer segmentation.
"""

import os
import sqlite3
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "banking.db")


def load_raw_tables(db_path=DB_PATH):
    """Loads customers and transactions tables from the SQLite database."""
    conn = sqlite3.connect(db_path)
    try:
        customers_df = pd.read_sql_query("SELECT * FROM customers;", conn)
        transactions_df = pd.read_sql_query("SELECT * FROM transactions;", conn)
        
        # Ensure proper datetime parsing
        customers_df["customer_since"] = pd.to_datetime(customers_df["customer_since"])
        transactions_df["transaction_date"] = pd.to_datetime(transactions_df["transaction_date"])
        
        return customers_df, transactions_df
    finally:
        conn.close()


def apply_filters(
    customers_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    start_date=None,
    end_date=None,
    cities=None,
    branches=None,
    txn_types=None,
    statuses=None,
    channels=None
):
    """
    Applies dashboard sidebar filters to transactions and customer data.
    Maintains relational consistency between customers and transactions.
    """
    txns = transactions_df.copy()
    custs = customers_df.copy()

    # Filter customers by city first
    if cities:
        custs = custs[custs["city"].isin(cities)]
        txns = txns[txns["customer_id"].isin(custs["customer_id"])]

    # Filter transactions by date range
    if start_date:
        start_ts = pd.to_datetime(start_date)
        txns = txns[txns["transaction_date"] >= start_ts]
    if end_date:
        end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        txns = txns[txns["transaction_date"] <= end_ts]

    # Filter by transaction attributes
    if branches:
        txns = txns[txns["branch"].isin(branches)]
    if txn_types:
        txns = txns[txns["transaction_type"].isin(txn_types)]
    if statuses:
        txns = txns[txns["transaction_status"].isin(statuses)]
    if channels:
        txns = txns[txns["channel"].isin(channels)]

    return custs, txns


def format_currency_inr(val):
    """
    Formats numeric amounts into clean Indian currency notations:
    - >= 10,000,000 (1 Crore): ₹X.XX Cr
    - >= 100,000 (1 Lakh): ₹X.XX Lakh
    - Otherwise: ₹X,XXX
    """
    if val is None or pd.isna(val):
        return "₹0"
    if abs(val) >= 10_000_000:
        return f"₹{val / 10_000_000:.2f} Cr"
    elif abs(val) >= 100_000:
        return f"₹{val / 100_000:.2f} Lakh"
    else:
        return f"₹{val:,.0f}"


def calculate_kpis(filtered_custs: pd.DataFrame, filtered_txns: pd.DataFrame):
    """
    Calculates executive summary KPIs for the top metric cards.
    
    Definitions:
    - Total Customers: Number of customer accounts in the current scope.
    - Active Customers: Customers who have >= 1 successful transaction in scope.
    - Total Transactions: Total transaction records in scope.
    - Total Transaction Value: Sum of successful transaction amounts.
    - Average Transaction Value: Mean ticket size for successful transactions.
    - Success Rate: (Successful transactions / Total transactions) * 100.
    """
    total_customers = len(filtered_custs)
    
    if filtered_txns.empty:
        return {
            "total_customers": total_customers,
            "active_customers": 0,
            "total_transactions": 0,
            "total_value": 0.0,
            "avg_value": 0.0,
            "success_rate": 0.0,
            "failed_rate": 0.0,
            "failed_count": 0
        }

    successful_txns = filtered_txns[filtered_txns["transaction_status"] == "Success"]
    failed_txns = filtered_txns[filtered_txns["transaction_status"] == "Failed"]

    # Active customers: customers with at least one successful transaction in filter window
    active_customers = successful_txns["customer_id"].nunique()
    total_transactions = len(filtered_txns)

    total_value = float(successful_txns["amount"].sum())
    avg_value = float(total_value / len(successful_txns)) if not successful_txns.empty else 0.0

    success_rate = (len(successful_txns) / total_transactions) * 100.0 if total_transactions > 0 else 0.0
    failed_rate = (len(failed_txns) / total_transactions) * 100.0 if total_transactions > 0 else 0.0

    return {
        "total_customers": total_customers,
        "active_customers": active_customers,
        "total_transactions": total_transactions,
        "total_value": round(total_value, 2),
        "avg_value": round(avg_value, 2),
        "success_rate": round(success_rate, 2),
        "failed_rate": round(failed_rate, 2),
        "failed_count": len(failed_txns)
    }


def get_monthly_trends(filtered_txns: pd.DataFrame):
    """
    Computes monthly aggregation of transaction volume and financial value.
    """
    if filtered_txns.empty:
        return pd.DataFrame(columns=["month", "total_transactions", "total_value", "avg_value"])

    df = filtered_txns.copy()
    df["month"] = df["transaction_date"].dt.strftime("%Y-%m")

    grouped = df.groupby("month").agg(
        total_transactions=("transaction_id", "count"),
        total_value=("amount", lambda s: s[df.loc[s.index, "transaction_status"] == "Success"].sum()),
        avg_value=("amount", lambda s: s[df.loc[s.index, "transaction_status"] == "Success"].mean())
    ).reset_index()

    grouped["total_value"] = grouped["total_value"].round(2)
    grouped["avg_value"] = grouped["avg_value"].round(2).fillna(0.0)
    grouped = grouped.sort_values("month")
    return grouped


def get_transaction_type_breakdown(filtered_txns: pd.DataFrame):
    """
    Calculates total volume and value by payment instrument type.
    """
    if filtered_txns.empty:
        return pd.DataFrame(columns=["transaction_type", "count", "total_amount", "volume_pct"])

    df = filtered_txns.copy()
    total_count = len(df)

    grouped = df.groupby("transaction_type").agg(
        count=("transaction_id", "count"),
        total_amount=("amount", lambda s: s[df.loc[s.index, "transaction_status"] == "Success"].sum())
    ).reset_index()

    grouped["volume_pct"] = ((grouped["count"] / total_count) * 100).round(2)
    grouped["total_amount"] = grouped["total_amount"].round(2)
    grouped = grouped.sort_values(by="total_amount", ascending=False)
    return grouped


def get_channel_breakdown(filtered_txns: pd.DataFrame):
    """
    Aggregates transactions across channels (Mobile, ATM, Branch, Internet).
    """
    if filtered_txns.empty:
        return pd.DataFrame(columns=["channel", "count", "total_amount", "failure_rate_pct"])

    df = filtered_txns.copy()
    grouped = df.groupby("channel").agg(
        count=("transaction_id", "count"),
        total_amount=("amount", lambda s: s[df.loc[s.index, "transaction_status"] == "Success"].sum()),
        failed_count=("transaction_status", lambda s: (s == "Failed").sum())
    ).reset_index()

    grouped["failure_rate_pct"] = ((grouped["failed_count"] / grouped["count"]) * 100).round(2)
    grouped["total_amount"] = grouped["total_amount"].round(2)
    grouped = grouped.sort_values(by="count", ascending=False)
    return grouped


def get_status_breakdown(filtered_txns: pd.DataFrame):
    """
    Returns breakdown of transaction statuses (Success, Failed, Pending).
    """
    if filtered_txns.empty:
        return pd.DataFrame(columns=["transaction_status", "count", "percentage"])

    counts = filtered_txns["transaction_status"].value_counts().reset_index()
    counts.columns = ["transaction_status", "count"]
    counts["percentage"] = ((counts["count"] / len(filtered_txns)) * 100).round(2)
    return counts


def get_branch_performance(filtered_txns: pd.DataFrame):
    """
    Calculates total value and count per bank branch.
    """
    if filtered_txns.empty:
        return pd.DataFrame(columns=["branch", "transaction_count", "total_amount"])

    df = filtered_txns.copy()
    grouped = df.groupby("branch").agg(
        transaction_count=("transaction_id", "count"),
        total_amount=("amount", lambda s: s[df.loc[s.index, "transaction_status"] == "Success"].sum())
    ).reset_index()

    grouped["total_amount"] = grouped["total_amount"].round(2)
    grouped = grouped.sort_values(by="total_amount", ascending=False)
    return grouped


def get_city_distribution(filtered_custs: pd.DataFrame):
    """
    Analyzes customer distribution and account types across Indian cities.
    """
    if filtered_custs.empty:
        return pd.DataFrame(columns=["city", "total_customers", "savings_pct"])

    grouped = filtered_custs.groupby("city").agg(
        total_customers=("customer_id", "count"),
        savings_count=("account_type", lambda s: (s == "Savings").sum()),
        salary_count=("account_type", lambda s: (s == "Salary").sum()),
        current_count=("account_type", lambda s: (s == "Current").sum())
    ).reset_index()

    grouped["pct_of_total"] = ((grouped["total_customers"] / len(filtered_custs)) * 100).round(2)
    grouped = grouped.sort_values(by="total_customers", ascending=False)
    return grouped


def get_top_customers(filtered_txns: pd.DataFrame, customers_df: pd.DataFrame, top_n=10):
    """
    Identifies top spending customers with profile details.
    """
    if filtered_txns.empty:
        return pd.DataFrame()

    successful_txns = filtered_txns[filtered_txns["transaction_status"] == "Success"]
    if successful_txns.empty:
        return pd.DataFrame()

    grouped = successful_txns.groupby("customer_id").agg(
        total_spend=("amount", "sum"),
        total_transactions=("transaction_id", "count"),
        last_transaction=("transaction_date", "max")
    ).reset_index()

    # Join customer demographic details
    merged = grouped.merge(customers_df, on="customer_id", how="inner")
    merged["total_spend"] = merged["total_spend"].round(2)
    merged["last_transaction"] = merged["last_transaction"].dt.strftime("%Y-%m-%d")
    merged = merged.sort_values(by="total_spend", ascending=False).head(top_n)

    result_cols = [
        "customer_id", "city", "occupation", "account_type",
        "total_transactions", "total_spend", "last_transaction"
    ]
    return merged[result_cols]


def segment_customers(customers_df: pd.DataFrame, transactions_df: pd.DataFrame):
    """
    Simple, explainable, rule-based customer segmentation.
    
    Segmentation Logic:
    1. High Value: Total successful spend >= ₹40,000 AND transaction frequency >= 5
    2. Regular: Total spend >= ₹5,000 OR transaction frequency >= 3
    3. Low Activity: Total spend < ₹5,000 with 1 to 2 transactions
    4. Inactive: 0 transactions (or no successful transactions) in the analyzed period
    """
    success_txns = transactions_df[transactions_df["transaction_status"] == "Success"]

    # Calculate metrics per customer
    agg_df = success_txns.groupby("customer_id").agg(
        total_spend=("amount", "sum"),
        frequency=("transaction_id", "count"),
        last_active=("transaction_date", "max")
    ).reset_index()

    # Merge with full customer base to retain zero-activity accounts
    cust_metrics = customers_df[["customer_id", "city", "occupation", "account_type"]].merge(
        agg_df, on="customer_id", how="left"
    )

    cust_metrics["total_spend"] = cust_metrics["total_spend"].fillna(0.0).round(2)
    cust_metrics["frequency"] = cust_metrics["frequency"].fillna(0).astype(int)

    def assign_segment(row):
        spend = row["total_spend"]
        freq = row["frequency"]
        if freq == 0 or spend == 0:
            return "Inactive"
        elif spend >= 40000 and freq >= 5:
            return "High Value"
        elif spend >= 5000 or freq >= 3:
            return "Regular"
        else:
            return "Low Activity"

    cust_metrics["segment"] = cust_metrics.apply(assign_segment, axis=1)

    # Create segment summary
    summary = cust_metrics.groupby("segment").agg(
        customer_count=("customer_id", "count"),
        total_segment_spend=("total_spend", "sum"),
        avg_spend=("total_spend", "mean"),
        avg_frequency=("frequency", "mean")
    ).reset_index()

    total_customers = len(cust_metrics)
    summary["pct_of_customers"] = ((summary["customer_count"] / total_customers) * 100).round(2)
    summary["total_segment_spend"] = summary["total_segment_spend"].round(2)
    summary["avg_spend"] = summary["avg_spend"].round(2)
    summary["avg_frequency"] = summary["avg_frequency"].round(1)

    # Order segments logically
    order_dict = {"High Value": 1, "Regular": 2, "Low Activity": 3, "Inactive": 4}
    summary["order"] = summary["segment"].map(order_dict)
    summary = summary.sort_values("order").drop(columns=["order"])

    return cust_metrics, summary

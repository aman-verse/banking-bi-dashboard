"""
Banking Customer & Transaction Analytics Dashboard
Data Cleaning Pipeline
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def clean_customers(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize customer demographic data."""
    print("Cleaning customers data...")
    df = raw_df.copy()

    # Deduplication
    initial_dups = df.duplicated().sum()
    df = df.drop_duplicates(subset=["customer_id"])

    # Standardize string fields
    df["city"] = df["city"].astype(str).str.strip().str.title()
    df["gender"] = df["gender"].astype(str).str.strip().str.title()
    df["account_type"] = df["account_type"].astype(str).str.strip().str.title()
    
    # Handle missing occupations
    missing_occupations = df["occupation"].isna().sum()
    df["occupation"] = df["occupation"].fillna("Other / Unspecified")
    df["occupation"] = df["occupation"].astype(str).str.strip().str.title()

    # Data types and date parsing
    df["age"] = df["age"].astype(int)
    df["customer_since"] = pd.to_datetime(df["customer_since"], errors="coerce")
    df = df.dropna(subset=["customer_since"])
    df["customer_since"] = df["customer_since"].dt.strftime("%Y-%m-%d")

    df = df.sort_values(by="customer_id").reset_index(drop=True)
    print(f"Customers cleaned: {len(df):,} rows (removed {initial_dups} duplicates)")
    return df


def clean_transactions(raw_df: pd.DataFrame, valid_customer_ids: set) -> pd.DataFrame:
    """Clean and validate banking transactions data."""
    print("Cleaning transactions data...")
    df = raw_df.copy()

    # Deduplication
    initial_dups = df.duplicated(subset=["transaction_id"]).sum()
    df = df.drop_duplicates(subset=["transaction_id"])

    # Standardize categories
    df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.upper()
    df["transaction_status"] = df["transaction_status"].astype(str).str.strip().str.title()
    df["channel"] = df["channel"].astype(str).str.strip().str.title()
    
    # Handle missing branch values
    df["branch"] = df["branch"].fillna("Digital / Central Processing")
    df["branch"] = df["branch"].astype(str).str.strip().str.title()

    # Validate amounts (must be positive)
    invalid_amounts = (df["amount"] <= 0).sum()
    df = df[df["amount"] > 0]
    df["amount"] = df["amount"].round(2)

    # Date parsing
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["transaction_date"])
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Referential integrity check
    df = df[df["customer_id"].isin(valid_customer_ids)]
    df = df.sort_values(by="transaction_date").reset_index(drop=True)
    
    print(f"Transactions cleaned: {len(df):,} rows (removed {initial_dups} duplicates, {invalid_amounts} invalid amounts)")
    return df


def run_pipeline():
    """Executes the full Pandas cleaning pipeline and exports clean CSVs."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    raw_cust_path = os.path.join(RAW_DIR, "customers.csv")
    raw_txn_path = os.path.join(RAW_DIR, "transactions.csv")

    if not os.path.exists(raw_cust_path) or not os.path.exists(raw_txn_path):
        raise FileNotFoundError("Raw data files not found! Please run src/generate_data.py first.")

    raw_customers = pd.read_csv(raw_cust_path)
    raw_transactions = pd.read_csv(raw_txn_path)

    clean_cust_df = clean_customers(raw_customers)
    valid_customers = set(clean_cust_df["customer_id"].unique())
    clean_txn_df = clean_transactions(raw_transactions, valid_customers)

    out_cust_path = os.path.join(PROCESSED_DIR, "customers_cleaned.csv")
    out_txn_path = os.path.join(PROCESSED_DIR, "transactions_cleaned.csv")

    clean_cust_df.to_csv(out_cust_path, index=False)
    clean_txn_df.to_csv(out_txn_path, index=False)

    print(f"Data cleaning complete: {len(clean_cust_df):,} customers and {len(clean_txn_df):,} transactions saved.")
    return clean_cust_df, clean_txn_df


if __name__ == "__main__":
    run_pipeline()

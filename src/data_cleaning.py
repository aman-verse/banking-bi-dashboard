"""
Banking Customer & Transaction Analytics Dashboard
Data Cleaning Pipeline

Performs structured data cleaning using Pandas:
- Inspecting shapes, nulls, and duplicates
- Deduplication and type casting
- Date parsing and standardization
- Categorical string cleanup (trimming, casing)
- Validation of business constraints (positive transaction amounts)
- Referential integrity check between customers and transactions
- Exports clean datasets to data/processed/
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def clean_customers(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize customer demographic data."""
    print("\n--- Cleaning Customers Data ---")
    print(f"Initial shape: {raw_df.shape}")
    
    df = raw_df.copy()

    # 1. Check & remove exact duplicates
    initial_dups = df.duplicated().sum()
    df = df.drop_duplicates(subset=["customer_id"])
    print(f"Duplicates removed: {initial_dups}")

    # 2. Standardize text columns (strip whitespace, consistent title case)
    df["city"] = df["city"].astype(str).str.strip().str.title()
    df["gender"] = df["gender"].astype(str).str.strip().str.title()
    df["account_type"] = df["account_type"].astype(str).str.strip().str.title()
    
    # 3. Handle missing values
    missing_occupations = df["occupation"].isna().sum()
    df["occupation"] = df["occupation"].fillna("Other / Unspecified")
    df["occupation"] = df["occupation"].astype(str).str.strip().str.title()
    print(f"Handled missing occupations (imputed with 'Other / Unspecified'): {missing_occupations}")

    # 4. Correct data types and dates
    df["age"] = df["age"].astype(int)
    df["customer_since"] = pd.to_datetime(df["customer_since"], errors="coerce")
    
    # Drop records if date couldn't be parsed
    df = df.dropna(subset=["customer_since"])
    df["customer_since"] = df["customer_since"].dt.strftime("%Y-%m-%d")

    # 5. Sort by customer_id
    df = df.sort_values(by="customer_id").reset_index(drop=True)
    
    print(f"Final cleaned customers shape: {df.shape}")
    return df


def clean_transactions(raw_df: pd.DataFrame, valid_customer_ids: set) -> pd.DataFrame:
    """Clean and validate banking transactions data."""
    print("\n--- Cleaning Transactions Data ---")
    print(f"Initial shape: {raw_df.shape}")
    
    df = raw_df.copy()

    # 1. Remove duplicate transaction IDs
    initial_dups = df.duplicated(subset=["transaction_id"]).sum()
    df = df.drop_duplicates(subset=["transaction_id"])
    print(f"Duplicates removed: {initial_dups}")

    # 2. Standardize categorical text fields
    df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.upper()
    df["transaction_status"] = df["transaction_status"].astype(str).str.strip().str.title()
    df["channel"] = df["channel"].astype(str).str.strip().str.title()
    
    # 3. Handle missing branch values (e.g. for pure digital/mobile transactions)
    missing_branches = df["branch"].isna().sum()
    df["branch"] = df["branch"].fillna("Digital / Central Processing")
    df["branch"] = df["branch"].astype(str).str.strip().str.title()
    print(f"Imputed missing branch values: {missing_branches}")

    # 4. Validate transaction amounts (must be positive numbers)
    invalid_amounts = (df["amount"] <= 0).sum()
    df = df[df["amount"] > 0]
    print(f"Removed invalid (<= 0) transaction amounts: {invalid_amounts}")
    df["amount"] = df["amount"].round(2)

    # 5. Robust Date Parsing
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], format="mixed", errors="coerce")
    invalid_dates = df["transaction_date"].isna().sum()
    if invalid_dates > 0:
        df = df.dropna(subset=["transaction_date"])
        print(f"Dropped records with unparseable dates: {invalid_dates}")
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # 6. Referential Integrity Check: ensure customer exists
    initial_rows = len(df)
    df = df[df["customer_id"].isin(valid_customer_ids)]
    orphaned_txns = initial_rows - len(df)
    if orphaned_txns > 0:
        print(f"Filtered out orphaned transactions without matching customer: {orphaned_txns}")

    # 7. Sort by transaction date
    df = df.sort_values(by="transaction_date").reset_index(drop=True)
    
    print(f"Final cleaned transactions shape: {df.shape}")
    return df


def run_pipeline():
    """Executes the full Pandas cleaning pipeline and exports clean CSVs."""
    print("=" * 60)
    print("STARTING DATA CLEANING PIPELINE")
    print("=" * 60)

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    raw_cust_path = os.path.join(RAW_DIR, "customers.csv")
    raw_txn_path = os.path.join(RAW_DIR, "transactions.csv")

    if not os.path.exists(raw_cust_path) or not os.path.exists(raw_txn_path):
        raise FileNotFoundError("Raw data files not found! Please run src/generate_data.py first.")

    raw_customers = pd.read_csv(raw_cust_path)
    raw_transactions = pd.read_csv(raw_txn_path)

    # Clean customers
    clean_cust_df = clean_customers(raw_customers)
    valid_customers = set(clean_cust_df["customer_id"].unique())

    # Clean transactions
    clean_txn_df = clean_transactions(raw_transactions, valid_customers)

    # Save cleaned datasets
    out_cust_path = os.path.join(PROCESSED_DIR, "customers_cleaned.csv")
    out_txn_path = os.path.join(PROCESSED_DIR, "transactions_cleaned.csv")

    clean_cust_df.to_csv(out_cust_path, index=False)
    clean_txn_df.to_csv(out_txn_path, index=False)

    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Clean Customers saved:    {out_cust_path} ({len(clean_cust_df):,} rows)")
    print(f"Clean Transactions saved: {out_txn_path} ({len(clean_txn_df):,} rows)")
    print("Data cleaning completed successfully!")

    return clean_cust_df, clean_txn_df


if __name__ == "__main__":
    run_pipeline()

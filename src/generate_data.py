"""
Banking Customer & Transaction Analytics Dashboard
Data Generation Script

Generates realistic synthetic banking data for customers and transactions.
Includes realistic data quality anomalies (duplicates, null values, 
whitespace, casing inconsistencies, invalid amounts) for the Pandas cleaning pipeline.
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Set fixed seed for reproducibility
np.random.seed(42)
random.seed(42)

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def generate_customers_data(num_customers=5000):
    """Generates synthetic customer demographic and account records."""
    cities = [
        "Ranchi", "Patna", "Delhi", "Mumbai", "Bangalore",
        "Kolkata", "Hyderabad", "Pune", "Chennai", "Ahmedabad"
    ]
    city_weights = [0.08, 0.07, 0.16, 0.18, 0.15, 0.08, 0.12, 0.08, 0.04, 0.04]
    
    occupations = ["Salaried", "Self-Employed", "Business", "Student", "Retired", "Freelancer"]
    occupation_weights = [0.45, 0.20, 0.15, 0.08, 0.07, 0.05]
    
    genders = ["Male", "Female", "Other"]
    gender_weights = [0.55, 0.43, 0.02]
    
    account_types = ["Savings", "Current", "Salary"]
    account_weights = [0.65, 0.15, 0.20]

    start_date = datetime(2020, 1, 1)
    end_date = datetime(2026, 6, 30)
    date_range_days = (end_date - start_date).days

    customer_ids = [f"CUST{i:05d}" for i in range(1, num_customers + 1)]
    
    # Generate demographic fields
    ages = np.random.randint(18, 72, size=num_customers)
    assigned_genders = random.choices(genders, weights=gender_weights, k=num_customers)
    assigned_cities = random.choices(cities, weights=city_weights, k=num_customers)
    assigned_occupations = random.choices(occupations, weights=occupation_weights, k=num_customers)
    assigned_accounts = random.choices(account_types, weights=account_weights, k=num_customers)
    
    cust_since_dates = [
        (start_date + timedelta(days=random.randint(0, date_range_days))).strftime("%Y-%m-%d")
        for _ in range(num_customers)
    ]

    customers_df = pd.DataFrame({
        "customer_id": customer_ids,
        "age": ages,
        "gender": assigned_genders,
        "city": assigned_cities,
        "occupation": assigned_occupations,
        "account_type": assigned_accounts,
        "customer_since": cust_since_dates
    })

    # Inject realistic raw inconsistencies
    # 1. Missing occupations for some customers (approx 1.5%)
    missing_idx = random.sample(range(num_customers), int(num_customers * 0.015))
    customers_df.loc[missing_idx, "occupation"] = None

    # 2. Whitespace and case discrepancies in cities
    for idx in random.sample(range(num_customers), 40):
        val = customers_df.loc[idx, "city"]
        customers_df.loc[idx, "city"] = f"  {val.lower()}  " if idx % 2 == 0 else f"{val.upper()} "

    # 3. Add small number of duplicate rows
    duplicates = customers_df.iloc[:20].copy()
    customers_df = pd.concat([customers_df, duplicates], ignore_index=True)

    return customers_df


def generate_transactions_data(customers_df, num_transactions=40000):
    """Generates synthetic transactional records linked to customer IDs."""
    valid_customer_ids = customers_df["customer_id"].unique().tolist()
    
    txn_types = ["UPI", "Card", "ATM", "NEFT", "IMPS"]
    type_weights = [0.44, 0.22, 0.16, 0.08, 0.10]
    
    statuses = ["Success", "Failed", "Pending"]
    status_weights = [0.89, 0.08, 0.03]
    
    channel_mapping = {
        "UPI": ["Mobile"],
        "Card": ["Internet", "Branch"],
        "ATM": ["ATM"],
        "NEFT": ["Internet", "Branch"],
        "IMPS": ["Mobile", "Internet"]
    }

    branches = [
        "Main Downtown Branch", "Tech Park Branch", "Metro Station Branch",
        "Commercial Area Branch", "Suburban Plaza Branch", "City Center Branch"
    ]

    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 9, 30)
    date_range_seconds = int((end_date - start_date).total_seconds())

    txn_ids = [f"TXN{i:07d}" for i in range(1, num_transactions + 1)]
    
    # Assign customer IDs (Pareto-like: 20% active users do 60% transactions)
    core_customers = random.sample(valid_customer_ids, int(len(valid_customer_ids) * 0.25))
    other_customers = [c for c in valid_customer_ids if c not in set(core_customers)]
    
    assigned_custs = []
    for _ in range(num_transactions):
        if random.random() < 0.65:
            assigned_custs.append(random.choice(core_customers))
        else:
            assigned_custs.append(random.choice(other_customers))

    assigned_types = random.choices(txn_types, weights=type_weights, k=num_transactions)
    assigned_statuses = random.choices(statuses, weights=status_weights, k=num_transactions)
    
    assigned_channels = []
    assigned_amounts = []
    
    for t_type in assigned_types:
        avail_channels = channel_mapping[t_type]
        assigned_channels.append(random.choice(avail_channels))
        
        # Realistic banking transaction amounts per type
        if t_type == "UPI":
            # Small to medium tickets
            amt = round(random.choice([
                random.uniform(20, 500),
                random.uniform(500, 3000),
                random.uniform(3000, 10000)
            ]), 2)
        elif t_type == "ATM":
            # Cash withdrawals usually multiples of 500 or 1000
            amt = float(random.choice([500, 1000, 2000, 3000, 5000, 10000]))
        elif t_type == "Card":
            amt = round(random.uniform(150, 25000), 2)
        elif t_type == "IMPS":
            amt = round(random.uniform(1000, 50000), 2)
        else:  # NEFT
            amt = round(random.uniform(5000, 150000), 2)
        assigned_amounts.append(amt)

    assigned_branches = random.choices(branches, k=num_transactions)
    
    # Generate timestamp within 18-month window
    assigned_timestamps = [
        (start_date + timedelta(seconds=random.randint(0, date_range_seconds))).strftime("%Y-%m-%d %H:%M:%S")
        for _ in range(num_transactions)
    ]

    transactions_df = pd.DataFrame({
        "transaction_id": txn_ids,
        "customer_id": assigned_custs,
        "transaction_date": assigned_timestamps,
        "transaction_type": assigned_types,
        "amount": assigned_amounts,
        "transaction_status": assigned_statuses,
        "channel": assigned_channels,
        "branch": assigned_branches
    })

    # Realistic raw imperfections for cleaning
    # 1. Negative or zero amount anomalies (5-10 records)
    for idx in random.sample(range(num_transactions), 12):
        transactions_df.loc[idx, "amount"] = -1 * abs(transactions_df.loc[idx, "amount"])

    # 2. Whitespace and lowercase channel / type
    for idx in random.sample(range(num_transactions), 80):
        c = transactions_df.loc[idx, "channel"]
        transactions_df.loc[idx, "channel"] = f"  {c.lower()} "

    for idx in random.sample(range(num_transactions), 60):
        t = transactions_df.loc[idx, "transaction_type"]
        transactions_df.loc[idx, "transaction_type"] = f"{t.lower()} "

    # 3. Missing branch on some online transactions (approx 1%)
    for idx in random.sample(range(num_transactions), int(num_transactions * 0.01)):
        transactions_df.loc[idx, "branch"] = None

    # 4. Inconsistent date formatting in a few rows
    for idx in random.sample(range(num_transactions), 30):
        dt_val = transactions_df.loc[idx, "transaction_date"]
        # Convert "YYYY-MM-DD HH:MM:SS" to "DD/MM/YYYY HH:MM"
        try:
            d_obj = datetime.strptime(dt_val, "%Y-%m-%d %H:%M:%S")
            transactions_df.loc[idx, "transaction_date"] = d_obj.strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass

    # 5. Duplicate transaction rows (approx 35 rows)
    dups = transactions_df.iloc[:35].copy()
    transactions_df = pd.concat([transactions_df, dups], ignore_index=True)

    return transactions_df


def main():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    
    print("[1/2] Generating customer dataset (5,000 customers)...")
    customers_df = generate_customers_data(num_customers=5000)
    customers_path = os.path.join(RAW_DATA_DIR, "customers.csv")
    customers_df.to_csv(customers_path, index=False)
    print(f"  [OK] Saved raw customers to: {customers_path} ({len(customers_df)} rows)")

    print("[2/2] Generating transactions dataset (40,000 transactions)...")
    transactions_df = generate_transactions_data(customers_df, num_transactions=40000)
    transactions_path = os.path.join(RAW_DATA_DIR, "transactions.csv")
    transactions_df.to_csv(transactions_path, index=False)
    print(f"  [OK] Saved raw transactions to: {transactions_path} ({len(transactions_df)} rows)")
    print("Data generation completed successfully!")


if __name__ == "__main__":
    main()

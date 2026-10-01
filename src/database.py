"""
Banking Customer & Transaction Analytics Dashboard
SQLite Database Manager

Responsibilities:
- Initializes SQLite database schema with primary and foreign key constraints
- Loads cleaned CSV datasets into SQLite tables
- Builds analytical indexes for high performance
- Executes database health checks and sample analytical queries
"""

import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "banking.db")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def get_connection(db_path=DB_PATH):
    """Returns a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database(conn):
    """Creates the customers and transactions tables with appropriate constraints."""
    cursor = conn.cursor()

    # Drop existing tables if re-initializing
    cursor.execute("DROP TABLE IF EXISTS transactions;")
    cursor.execute("DROP TABLE IF EXISTS customers;")

    # Customers table DDL
    cursor.execute("""
    CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        city TEXT NOT NULL,
        occupation TEXT NOT NULL,
        account_type TEXT NOT NULL,
        customer_since TEXT NOT NULL
    );
    """)

    # Transactions table DDL
    cursor.execute("""
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
    """)

    # Create analytical indexes
    cursor.execute("CREATE INDEX idx_transactions_customer ON transactions(customer_id);")
    cursor.execute("CREATE INDEX idx_transactions_date ON transactions(transaction_date);")
    cursor.execute("CREATE INDEX idx_transactions_type ON transactions(transaction_type);")
    cursor.execute("CREATE INDEX idx_transactions_status ON transactions(transaction_status);")
    cursor.execute("CREATE INDEX idx_transactions_channel ON transactions(channel);")
    cursor.execute("CREATE INDEX idx_customers_city ON customers(city);")

    conn.commit()
    print("Database tables and indexes created successfully.")


def load_cleaned_data(conn):
    """Loads cleaned CSV data into the SQLite database."""
    cust_file = os.path.join(PROCESSED_DIR, "customers_cleaned.csv")
    txn_file = os.path.join(PROCESSED_DIR, "transactions_cleaned.csv")

    if not os.path.exists(cust_file) or not os.path.exists(txn_file):
        raise FileNotFoundError("Cleaned CSV files not found! Please run src/data_cleaning.py first.")

    customers_df = pd.read_csv(cust_file)
    transactions_df = pd.read_csv(txn_file)

    print(f"Loading {len(customers_df):,} customers into database...")
    customers_df.to_sql("customers", conn, if_exists="append", index=False)

    print(f"Loading {len(transactions_df):,} transactions into database...")
    transactions_df.to_sql("transactions", conn, if_exists="append", index=False)

    conn.commit()
    print("Data loading completed successfully.")


def validate_database(conn):
    """Performs validation checks to verify row counts and data integrity."""
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM customers;")
    cust_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions;")
    txn_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT customer_id) FROM customers;")
    unique_custs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT transaction_id) FROM transactions;")
    unique_txns = cursor.fetchone()[0]

    # Verify no foreign key violations
    cursor.execute("""
    SELECT COUNT(*) FROM transactions t 
    LEFT JOIN customers c ON t.customer_id = c.customer_id 
    WHERE c.customer_id IS NULL;
    """)
    fk_violations = cursor.fetchone()[0]

    print("\n" + "=" * 50)
    print("DATABASE VALIDATION REPORT")
    print("=" * 50)
    print(f"Total Customers:               {cust_count:,}")
    print(f"Unique Customer IDs:           {unique_custs:,}")
    print(f"Total Transactions:            {txn_count:,}")
    print(f"Unique Transaction IDs:        {unique_txns:,}")
    print(f"Foreign Key Violations:        {fk_violations}")
    print("Validation Status:             [PASSED]" if fk_violations == 0 and cust_count == unique_custs else "[FAILED]")
    print("=" * 50 + "\n")


def execute_query(sql_query, params=None, db_path=DB_PATH):
    """Executes a SQL query and returns results as a Pandas DataFrame."""
    conn = get_connection(db_path)
    try:
        if params:
            df = pd.read_sql_query(sql_query, conn, params=params)
        else:
            df = pd.read_sql_query(sql_query, conn)
        return df
    finally:
        conn.close()


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection(DB_PATH)
    try:
        init_database(conn)
        load_cleaned_data(conn)
        validate_database(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

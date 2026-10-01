"""
Banking Customer & Transaction Analytics Dashboard
Optional Firebase Firestore Integration Module

Architecture:
- Local Analytics: SQLite (default, zero-latency, full SQL capabilities)
- Cloud Storage: Firebase Firestore (optional dual-write or cloud sync)

Security Notice:
- Service account credentials, private keys, and API secrets are NEVER hardcoded.
- Credentials are read securely via Streamlit secrets (`st.secrets["firebase"]`)
  or the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.
"""

import os
import json
import pandas as pd

# Check if firebase_admin is installed
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False


def is_firebase_configured():
    """
    Checks if Firebase Firestore credentials are provided via
    Streamlit secrets or standard Google Cloud environment variable.
    """
    if not FIREBASE_AVAILABLE:
        return False, "firebase-admin package is not installed."

    if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ and os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
        return True, "Configured via GOOGLE_APPLICATION_CREDENTIALS"

    # Check Streamlit secrets if running inside Streamlit
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "firebase" in st.secrets:
            return True, "Configured via Streamlit secrets"
    except Exception:
        pass

    return False, "Credentials not detected. Set GOOGLE_APPLICATION_CREDENTIALS or configure .streamlit/secrets.toml."


def get_firestore_client():
    """
    Initializes and returns a Firestore client instance securely.
    Returns None if not configured.
    """
    configured, msg = is_firebase_configured()
    if not configured:
        return None

    if not firebase_admin._apps:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            else:
                cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Failed to initialize Firebase Admin SDK: {e}")
            return None

    return firestore.client()


def sync_processed_data_to_firestore(batch_limit=500):
    """
    Optional utility to upload cleaned transactions and customer records
    to a Firebase Firestore cloud collection in batches.
    """
    db = get_firestore_client()
    if db is None:
        print("[INFO] Firestore not configured. Operating in local SQLite mode.")
        return False

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cust_path = os.path.join(base_dir, "data", "processed", "customers_cleaned.csv")
    txn_path = os.path.join(base_dir, "data", "processed", "transactions_cleaned.csv")

    if not os.path.exists(cust_path) or not os.path.exists(txn_path):
        print("[ERROR] Cleaned CSV files not found. Run src/data_cleaning.py first.")
        return False

    cust_df = pd.read_csv(cust_path).head(batch_limit)
    txn_df = pd.read_csv(txn_path).head(batch_limit)

    print(f"Uploading sample {len(cust_df)} customers to Firestore 'customers' collection...")
    batch = db.batch()
    for _, row in cust_df.iterrows():
        doc_ref = db.collection("customers").document(row["customer_id"])
        batch.set(doc_ref, row.to_dict())
    batch.commit()

    print(f"Uploading sample {len(txn_df)} transactions to Firestore 'transactions' collection...")
    batch = db.batch()
    for _, row in txn_df.iterrows():
        doc_ref = db.collection("transactions").document(row["transaction_id"])
        batch.set(doc_ref, row.to_dict())
    batch.commit()

    print("[SUCCESS] Data synchronized to Firebase Firestore successfully.")
    return True

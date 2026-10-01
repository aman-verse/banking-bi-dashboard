"""
Banking Customer & Transaction Analytics Dashboard
Streamlit Web Application

An end-to-end interactive Business Intelligence dashboard for banking
transaction monitoring, customer segmentation, and executive insights.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

from src.database import DB_PATH
from src.analytics import (
    load_raw_tables,
    apply_filters,
    calculate_kpis,
    format_currency_inr,
    get_monthly_trends,
    get_transaction_type_breakdown,
    get_channel_breakdown,
    get_status_breakdown,
    get_branch_performance,
    get_city_distribution,
    get_top_customers,
    segment_customers
)
from src.insights import generate_business_insights

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Banking Customer & Transaction Analytics Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean, human/student-developed yet polished UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0F2942;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.8rem;
    }
    .metric-card-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .insight-card {
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 12px;
        border-left: 5px solid;
    }
    .insight-info {
        background-color: #EFF6FF;
        border-left-color: #3B82F6;
        color: #1E3A8A;
    }
    .insight-success {
        background-color: #ECFDF5;
        border-left-color: #10B981;
        color: #065F46;
    }
    .insight-warning {
        background-color: #FFFBEB;
        border-left-color: #F59E0B;
        color: #92400E;
    }
    .insight-title {
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }
    .insight-body {
        font-size: 0.9rem;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Data Loading (Cached for performance)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading banking database records...")
def get_data(db_mtime):
    return load_raw_tables()

try:
    db_mtime = os.path.getmtime(DB_PATH) if os.path.exists(DB_PATH) else 0
    all_customers, all_transactions = get_data(db_mtime)
except Exception as e:
    st.error(f"Error loading database. Please ensure SQLite database exists. Details: {e}")
    st.stop()


# -----------------------------------------------------------------------------
# Sidebar: Filter Controls
# -----------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/fluency/96/bank-building.png", width=64)
st.sidebar.title("Dashboard Filters")
st.sidebar.markdown("Filter transaction activity and customer scope:")

# 1. Date Range Filter
min_date = all_transactions["transaction_date"].min().date()
max_date = all_transactions["transaction_date"].max().date()

date_range = st.sidebar.date_input(
    "Transaction Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="Select start and end dates to filter transactions"
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_filter, end_filter = date_range
else:
    start_filter, end_filter = min_date, max_date

# 2. City Filter
city_options = sorted(all_customers["city"].unique().tolist())
selected_cities = st.sidebar.multiselect("City", options=city_options, default=[], placeholder="All Cities")

# 3. Branch Filter (Dependent on selected cities)
if selected_cities:
    city_cust_ids = set(all_customers[all_customers["city"].isin(selected_cities)]["customer_id"])
    branch_options = sorted(all_transactions[all_transactions["customer_id"].isin(city_cust_ids)]["branch"].unique().tolist())
else:
    branch_options = sorted(all_transactions["branch"].unique().tolist())

selected_branches = st.sidebar.multiselect("Branch", options=branch_options, default=[], placeholder="All Branches")

# 4. Transaction Type Filter
type_options = sorted(all_transactions["transaction_type"].unique().tolist())
selected_types = st.sidebar.multiselect("Transaction Type", options=type_options, default=[], placeholder="All Types (UPI, Card...)")

# 5. Transaction Status Filter
status_options = sorted(all_transactions["transaction_status"].unique().tolist())
selected_statuses = st.sidebar.multiselect("Transaction Status", options=status_options, default=[], placeholder="All Statuses")

# 6. Channel Filter
channel_options = sorted(all_transactions["channel"].unique().tolist())
selected_channels = st.sidebar.multiselect("Channel", options=channel_options, default=[], placeholder="All Channels")

# Reset button indicator
if st.sidebar.button("Reset All Filters", width="stretch"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Portfolio Project: Banking BI Analytics")


# -----------------------------------------------------------------------------
# Apply Filters to Data
# -----------------------------------------------------------------------------
filtered_custs, filtered_txns = apply_filters(
    customers_df=all_customers,
    transactions_df=all_transactions,
    start_date=start_filter,
    end_date=end_filter,
    cities=selected_cities if selected_cities else None,
    branches=selected_branches if selected_branches else None,
    txn_types=selected_types if selected_types else None,
    statuses=selected_statuses if selected_statuses else None,
    channels=selected_channels if selected_channels else None
)

kpis = calculate_kpis(filtered_custs, filtered_txns)
segmented_custs, segment_summary = segment_customers(filtered_custs, filtered_txns)


# -----------------------------------------------------------------------------
# Main Header
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">Banking Customer & Transaction Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive analysis of customer behavior, channel adoption, branch volumes, and operational KPIs</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Top Executive KPI Metric Cards
# -----------------------------------------------------------------------------
if filtered_txns.empty:
    st.warning("No transactions match the selected filters. Please adjust your date range or filter criteria.")

kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)

with kpi_col1:
    st.metric(
        label="Total Customers",
        value=f"{kpis['total_customers']:,}",
        help="Number of customers in the selected customer scope"
    )

with kpi_col2:
    active_pct = (kpis['active_customers'] / max(kpis['total_customers'], 1)) * 100
    st.metric(
        label="Active Customers",
        value=f"{kpis['active_customers']:,}",
        delta=f"{active_pct:.1f}% active" if kpis['total_customers'] > 0 else None,
        delta_color="normal",
        help="Customers who have at least one successful transaction within the selected filter/date range"
    )

with kpi_col3:
    st.metric(
        label="Total Transactions",
        value=f"{kpis['total_transactions']:,}",
        help="Number of transaction records after applying filters"
    )

with kpi_col4:
    st.metric(
        label="Total Transaction Value",
        value=format_currency_inr(kpis['total_value']),
        help="Sum of successful transaction amounts for the filtered transactions"
    )

with kpi_col5:
    st.metric(
        label="Average Transaction Value",
        value=f"₹{kpis['avg_value']:,.0f}",
        help="Total transaction value / successful transaction count"
    )

with kpi_col6:
    st.metric(
        label="Success Rate",
        value=f"{kpis['success_rate']:.1f}%",
        delta=f"{kpis['failed_rate']:.1f}% failed" if kpis['total_transactions'] > 0 else None,
        delta_color="inverse",
        help="Successful transactions / total transactions × 100"
    )

st.markdown("---")


# -----------------------------------------------------------------------------
# Section 1: Transaction Overview
# -----------------------------------------------------------------------------
st.subheader("1. Transaction Overview")
monthly_df = get_monthly_trends(filtered_txns)

if not monthly_df.empty:
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        fig_trend_val = px.line(
            monthly_df,
            x="month",
            y="total_value",
            markers=True,
            title="Monthly Transaction Value (₹)",
            labels={"month": "Month", "total_value": "Total Value (₹)"},
            color_discrete_sequence=["#1E40AF"]
        )
        fig_trend_val.update_layout(
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=40, b=20),
            hovermode="x unified"
        )
        st.plotly_chart(fig_trend_val, width="stretch")

    with col_t2:
        fig_trend_cnt = px.bar(
            monthly_df,
            x="month",
            y="total_transactions",
            title="Monthly Transaction Volume (Count)",
            labels={"month": "Month", "total_transactions": "Number of Transactions"},
            color_discrete_sequence=["#3B82F6"]
        )
        fig_trend_cnt.update_layout(
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_trend_cnt, width="stretch")
else:
    st.info("No transactions match the selected filters.")


# -----------------------------------------------------------------------------
# Section 2: Transaction Analysis
# -----------------------------------------------------------------------------
st.subheader("2. Transaction Analysis")

if filtered_txns.empty:
    st.info("No data available for the selected filters.")
else:
    col_a1, col_a2, col_a3 = st.columns(3)

    type_df = get_transaction_type_breakdown(filtered_txns)
    channel_df = get_channel_breakdown(filtered_txns)
    status_df = get_status_breakdown(filtered_txns)

    with col_a1:
        if not type_df.empty:
            fig_type = px.bar(
                type_df,
                x="transaction_type",
                y="total_amount",
                text="total_amount",
                title="Transaction Value by Type (₹)",
                labels={"transaction_type": "Payment Type", "total_amount": "Total Value (₹)"},
                color="transaction_type",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_type.update_traces(texttemplate='₹%{text:.2s}', textposition='outside')
            fig_type.update_layout(showlegend=False, plot_bgcolor="white", margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_type, width="stretch")
        else:
            st.write("No type data.")

    with col_a2:
        if not channel_df.empty:
            fig_channel = px.pie(
                channel_df,
                names="channel",
                values="count",
                title="Transaction Count by Channel",
                hole=0.45,
                color_discrete_sequence=["#2563EB", "#059669", "#D97706", "#7C3AED"]
            )
            fig_channel.update_layout(margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_channel, width="stretch")
        else:
            st.write("No channel data.")

    with col_a3:
        if not status_df.empty:
            status_colors = {"Success": "#10B981", "Failed": "#EF4444", "Pending": "#F59E0B"}
            fig_status = px.pie(
                status_df,
                names="transaction_status",
                values="count",
                title="Transaction Status Breakdown",
                hole=0.45,
                color="transaction_status",
                color_discrete_map=status_colors
            )
            fig_status.update_layout(margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_status, width="stretch")
        else:
            st.write("No status data.")


# -----------------------------------------------------------------------------
# Section 3: Branch / Location Analysis
# -----------------------------------------------------------------------------
st.subheader("3. Branch / Location Analysis")

if filtered_txns.empty and filtered_custs.empty:
    st.info("No data available for the selected filters.")
else:
    col_b1, col_b2 = st.columns(2)

    branch_df = get_branch_performance(filtered_txns)
    city_df = get_city_distribution(filtered_custs)

    with col_b1:
        if not branch_df.empty:
            fig_branch = px.bar(
                branch_df,
                x="total_amount",
                y="branch",
                orientation="h",
                title="Branch-wise Transaction Value (₹)",
                labels={"total_amount": "Total Value (₹)", "branch": "Bank Branch"},
                color="total_amount",
                color_continuous_scale="Blues"
            )
            fig_branch.update_layout(
                plot_bgcolor="white",
                yaxis=dict(autorange="reversed"),
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_branch, width="stretch")
        else:
            st.info("No branch data available for selected filters.")

    with col_b2:
        if not city_df.empty:
            fig_city = px.bar(
                city_df,
                x="city",
                y="total_customers",
                title="City-wise Customer Distribution",
                labels={"city": "Indian City", "total_customers": "Registered Customers"},
                color="total_customers",
                color_continuous_scale="Tealgrn"
            )
            fig_city.update_layout(
                plot_bgcolor="white",
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_city, width="stretch")
        else:
            st.info("No city data available for selected filters.")


# -----------------------------------------------------------------------------
# Section 4: Customer Analysis & Segmentation
# -----------------------------------------------------------------------------
st.subheader("4. Customer Analysis & Segmentation")

if filtered_txns.empty:
    st.info("No data available for the selected filters.")
else:
    tab_cust1, tab_cust2 = st.tabs(["Top 10 High-Value Customers", "Customer Segmentation Rules & Distribution"])

    with tab_cust1:
        top_customers_df = get_top_customers(filtered_txns, filtered_custs, top_n=10)
        if not top_customers_df.empty:
            st.dataframe(
                top_customers_df.style.format({
                    "total_spend": "₹{:,.2f}",
                    "total_transactions": "{:,}"
                }),
                width="stretch",
                hide_index=True
            )
        else:
            st.info("No customer transactions matching criteria.")

    with tab_cust2:
        st.caption("Customer segments are based on transaction frequency, transaction value and recent activity.")
        seg_col1, seg_col2 = st.columns([1, 1])
        
        with seg_col1:
            st.markdown("""
            **Rule-Based Customer Segmentation Criteria:**
            - 🌟 **High Value**: Total spend ≥ ₹40,000 & Frequency ≥ 5 transactions
            - 👤 **Regular**: Total spend ≥ ₹5,000 OR Frequency ≥ 3 transactions
            - ⏳ **Low Activity**: Total spend < ₹5,000 with 1–2 transactions
            - 💤 **Inactive**: 0 successful transactions in the selected period
            """)
            
            st.dataframe(
                segment_summary.style.format({
                    "customer_count": "{:,}",
                    "total_segment_spend": "₹{:,.2f}",
                    "avg_spend": "₹{:,.2f}",
                    "pct_of_customers": "{:.1f}%",
                    "avg_frequency": "{:.1f}"
                }),
                width="stretch",
                hide_index=True
            )

        with seg_col2:
            seg_colors = {
                "High Value": "#10B981",
                "Regular": "#3B82F6",
                "Low Activity": "#F59E0B",
                "Inactive": "#94A3B8"
            }
            fig_seg = px.pie(
                segment_summary,
                names="segment",
                values="customer_count",
                title="Customer Base Share by Segment",
                color="segment",
                color_discrete_map=seg_colors,
                hole=0.4
            )
            fig_seg.update_layout(margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_seg, width="stretch")


# -----------------------------------------------------------------------------
# Section 5: Business Insights
# -----------------------------------------------------------------------------
st.subheader("5. Business Insights")
st.markdown("Key observations from the selected data.")

insights_list = generate_business_insights(filtered_custs, filtered_txns, kpis, segment_summary)

for ins in insights_list:
    css_class = f"insight-{ins.get('type', 'info')}"
    st.markdown(f"""
    <div class="insight-card {css_class}">
        <div class="insight-title">{ins['title']}</div>
        <div class="insight-body">{ins['message']}</div>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
f_col1, f_col2 = st.columns([3, 1])
with f_col1:
    st.caption("Banking Customer & Transaction Analytics Dashboard | Built with Python, Pandas, SQLite, Streamlit & Plotly")
with f_col2:
    csv_data = filtered_txns.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data (CSV)",
        data=csv_data,
        file_name="filtered_banking_transactions.csv",
        mime="text/csv",
        width="stretch"
    )

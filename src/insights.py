"""
Banking Customer & Transaction Analytics Dashboard
Dynamic Business Insights Generator
"""

import pandas as pd


def generate_business_insights(filtered_custs: pd.DataFrame, filtered_txns: pd.DataFrame, kpis: dict, seg_summary: pd.DataFrame):
    """
    Analyzes current filtered data and produces dynamic, descriptive
    observations for the BI dashboard.
    """
    if filtered_txns.empty:
        return [
            {
                "type": "info",
                "title": "No Transactions Available",
                "message": "No business insights can be generated for the current selection."
            }
        ]

    insights = []
    total_count = len(filtered_txns)
    successful_txns = filtered_txns[filtered_txns["transaction_status"] == "Success"]

    # 1. Dominant Payment Channel / Instrument
    type_counts = filtered_txns["transaction_type"].value_counts()
    if not type_counts.empty:
        top_type = type_counts.index[0]
        top_type_pct = round((type_counts.iloc[0] / total_count) * 100, 1)
        insights.append({
            "type": "info",
            "title": f"Dominant Payment Channel: {top_type}",
            "message": (
                f"**{top_type}** accounts for **{top_type_pct}%** of transaction volume "
                f"({type_counts.iloc[0]:,} transactions) in the selected dataset."
            )
        })

    # 2. Branch Transaction Value Performance
    if not successful_txns.empty:
        branch_values = successful_txns.groupby("branch")["amount"].sum()
        if not branch_values.empty:
            top_branch = branch_values.idxmax()
            top_branch_val = branch_values.max()
            total_val = successful_txns["amount"].sum()
            branch_share = round((top_branch_val / total_val) * 100, 1) if total_val > 0 else 0
            
            insights.append({
                "type": "success",
                "title": f"Top Transaction-Value Branch: {top_branch}",
                "message": (
                    f"**{top_branch}** leads in total transaction value among the currently selected records, "
                    f"processing **₹{top_branch_val:,.2f}** ({branch_share}% of successful transaction value)."
                )
            })

    # 3. Channel Failure Rate
    channel_groups = filtered_txns.groupby("channel")
    channel_fail_rates = {}
    for ch, grp in channel_groups:
        fails = (grp["transaction_status"] == "Failed").sum()
        rate = (fails / len(grp)) * 100
        channel_fail_rates[ch] = (rate, fails, len(grp))

    if channel_fail_rates:
        worst_channel, (worst_rate, fail_cnt, total_ch) = max(channel_fail_rates.items(), key=lambda x: x[1][0])
        overall_fail_rate = kpis.get("failed_rate", 0.0)
        
        status_type = "warning" if worst_rate > 7.0 else "info"
        insights.append({
            "type": status_type,
            "title": f"Channel Performance: {worst_channel} Failure Rate",
            "message": (
                f"The **{worst_channel}** channel has an **{worst_rate:.2f}%** failure rate "
                f"({fail_cnt:,} failed out of {total_ch:,} requests) compared with an overall transaction "
                f"failure rate of **{overall_fail_rate}%**."
            )
        })

    # 4. Customer Spending Concentration
    if not seg_summary.empty and "High Value" in seg_summary["segment"].values:
        hv_row = seg_summary[seg_summary["segment"] == "High Value"].iloc[0]
        hv_cust_pct = hv_row.get("pct_of_customers", 0)
        hv_spend = hv_row.get("total_segment_spend", 0)
        total_spend = seg_summary["total_segment_spend"].sum()
        hv_spend_pct = round((hv_spend / total_spend) * 100, 1) if total_spend > 0 else 0

        insights.append({
            "type": "success",
            "title": "High-Value Customer Concentration",
            "message": (
                f"High-value customers represent **{hv_cust_pct}%** of customers but account for "
                f"**{hv_spend_pct}%** (₹{hv_spend:,.2f}) of transaction value, indicating that transaction "
                f"activity is concentrated among this segment. This segment can be prioritized for further retention analysis."
            )
        })

    # 5. Geographic Customer Distribution
    if not filtered_custs.empty:
        city_counts = filtered_custs["city"].value_counts()
        top_city = city_counts.index[0]
        top_city_pct = round((city_counts.iloc[0] / len(filtered_custs)) * 100, 1)
        insights.append({
            "type": "info",
            "title": f"Customer Concentration: {top_city}",
            "message": (
                f"Customer concentration is highest in **{top_city}** (**{top_city_pct}%** with "
                f"{city_counts.iloc[0]:,} accounts), making it a useful segment for deeper product and transaction analysis."
            )
        })

    # 6. Customer Dormancy
    if not seg_summary.empty and "Inactive" in seg_summary["segment"].values:
        inact_row = seg_summary[seg_summary["segment"] == "Inactive"].iloc[0]
        inact_pct = inact_row.get("pct_of_customers", 0)
        inact_cnt = inact_row.get("customer_count", 0)
        if inact_cnt > 0:
            insights.append({
                "type": "warning",
                "title": f"Customer Dormancy: {inact_cnt:,} Inactive Accounts",
                "message": (
                    f"**{inact_cnt:,}** customers ({inact_pct}%) recorded no successful transactions "
                    f"during the selected period. This group may be useful for further customer-engagement analysis."
                )
            })

    return insights

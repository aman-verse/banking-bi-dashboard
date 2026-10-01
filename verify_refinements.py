import sqlite3
import urllib.request
import pandas as pd
from src.analytics import load_raw_tables, apply_filters, calculate_kpis, format_currency_inr, segment_customers
from src.insights import generate_business_insights

# 1. Database validation
conn = sqlite3.connect('database/banking.db')
c_cnt = conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
t_cnt = conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
fk_err = conn.execute('''
    SELECT COUNT(*) FROM transactions t 
    LEFT JOIN customers c ON t.customer_id = c.customer_id 
    WHERE c.customer_id IS NULL
''').fetchone()[0]
conn.close()

assert c_cnt == 5000, f'Expected 5000 customers, got {c_cnt}'
assert t_cnt == 39988, f'Expected 39988 transactions, got {t_cnt}'
assert fk_err == 0, f'FK violations: {fk_err}'
print(f'[1/6] DB Verification: PASSED (5,000 customers, 39,988 transactions, 0 FK errors)')

# 2. Analytics & KPI verification
custs, txns = load_raw_tables()
kpis = calculate_kpis(custs, txns)
assert kpis['total_customers'] == 5000
assert kpis['total_transactions'] == 39988
formatted_val = format_currency_inr(kpis['total_value'])
assert 'Cr' in formatted_val
print(f'[2/6] KPI Calculations: PASSED (Value: {formatted_val}, Avg: ₹{kpis["avg_value"]:,.0f}, Success: {kpis["success_rate"]}%)')

# 3. Filter verification (Mumbai only)
m_custs, m_txns = apply_filters(custs, txns, cities=['Mumbai'])
m_kpis = calculate_kpis(m_custs, m_txns)
assert len(m_custs) > 0 and len(m_txns) > 0
print(f'[3/6] Filter Test (Mumbai): PASSED ({len(m_custs)} customers, {len(m_txns)} transactions)')

# 4. Empty filter verification
e_custs, e_txns = apply_filters(custs, txns, start_date='2010-01-01', end_date='2010-01-02')
e_kpis = calculate_kpis(e_custs, e_txns)
e_insights = generate_business_insights(e_custs, e_txns, e_kpis, None)
assert e_kpis['total_transactions'] == 0
assert 'No business insights' in e_insights[0]['message']
print(f'[4/6] Empty Filter Test: PASSED ({e_insights[0]["message"]})')

# 5. Dynamic Insights wording check
seg_df, seg_sum = segment_customers(custs, txns)
insights = generate_business_insights(custs, txns, kpis, seg_sum)
for ins in insights:
    text = (ins['title'] + ' ' + ins['message']).lower()
    assert 'revenue' not in text, f'Found unauthorized revenue term: {ins}'
    assert 'roi' not in text, f'Found unauthorized ROI term: {ins}'
    assert 'maximize retention' not in text, f'Found unauthorized retention claim: {ins}'
print(f'[5/6] Insights Wording Polish: PASSED ({len(insights)} insights generated, zero revenue/ROI claims)')

# 6. Streamlit Server Health
res = urllib.request.urlopen('http://localhost:8501/_stcore/health')
assert res.status == 200
print(f'[6/6] Streamlit Live Server: PASSED (HTTP 200 at http://localhost:8501)')

print('\nALL 6 VERIFICATION CHECKS PASSED PERFECTLY!')

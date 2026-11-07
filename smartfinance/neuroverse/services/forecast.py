"""Deterministic demonstration forecast; use integer pence throughout."""
from datetime import date, timedelta

SCENARIO_LABELS = {
    'baseline': 'Current plan',
    'emergency': 'Unexpected £150 expense',
    'bill_shift': 'Utilities paid after payday (if agreed)',
}

def project(balance_pence, transactions, horizon=30, scenario='baseline', today=None):
    today = today or date.today()
    if scenario not in SCENARIO_LABELS:
        raise ValueError('Unknown scenario')
    events = {}
    for txn in transactions:
        when = date.fromisoformat(txn.date)
        if when < today or when > today + timedelta(days=horizon):
            continue
        if scenario == 'bill_shift' and txn.description == 'Utilities' and txn.source == 'scheduled':
            when += timedelta(days=10)
        events[when] = events.get(when, 0) + txn.amount_pence
    if scenario == 'emergency':
        shock = today + timedelta(days=6)
        events[shock] = events.get(shock, 0) - 15000

    result = [{'date': today.isoformat(), 'day': 0, 'balance_pence': balance_pence}]
    balance = balance_pence
    for i in range(1, horizon + 1):
        when = today + timedelta(days=i)
        balance += events.get(when, 0)
        result.append({'date': when.isoformat(), 'day': i, 'balance_pence': balance})
    lowest = min(result, key=lambda item: item['balance_pence'])
    first_shortfall = next((x for x in result if x['balance_pence'] < 0), None)
    return {'timeline': result, 'lowest': lowest, 'shortfall': first_shortfall, 'end_balance_pence': balance, 'scenario': scenario}

def money(pence):
    sign = '−' if pence < 0 else ''
    return f'{sign}£{abs(pence)/100:,.2f}'

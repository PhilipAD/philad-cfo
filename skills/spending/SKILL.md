---
name: spending
description: >
  Spending analysis — categorise transactions, identify anomalies, optimise
  budget. Activates on: spending, transactions, how much did I spend,
  where is my money going, budget, categories, expenses, overspending,
  subscriptions, bills, food, dining, transport, shopping, anomaly, unusual charge,
  cash flow, outgoings.
allowed-tools: Read Bash Write
---

# Spending Analysis Skill

## Overview

Analyses Phil's transaction data from Plaid to provide category-level spend
summaries, identify anomalies, and surface optimisation opportunities.

## Step-by-Step Instructions

### 1. Load Transaction Data

```bash
# Latest spending breakdown
philad-cfo analyze spending

# Or read cached transaction logs
ls ~/.philad-cfo/kb/transactions/
cat ~/.philad-cfo/kb/transactions/$(date +%Y-%m-%d).md
```

### 2. Categorise Spending

The Plaid client auto-categorises transactions. Main categories to watch:

| Category | Target % of Net Income |
| -------- | --------------------- |
| Housing | ≤ 30% |
| Food & Dining | ≤ 15% |
| Transport | ≤ 10% |
| Shopping | ≤ 10% |
| Subscriptions | ≤ 5% |
| Entertainment | ≤ 5% |

### 3. Identify Anomalies

Look for:
- Single transactions > £200 that are not rent/mortgage/salary
- Category totals > 150% of the previous month average
- Duplicate charges (same merchant, same amount, same week)
- New recurring charges (potential new subscription)

### 4. Calculate Savings Rate

```bash
philad-cfo analyze savings
```

Savings Rate = (Monthly Net − Total Spend) / Monthly Net × 100

Benchmarks:
- < 10% — below target, review discretionary spend
- 10–20% — acceptable
- 20–30% — good
- 30%+ — excellent (accelerated mortgage deposit building)

### 5. Report Format

Present to user:
1. **Total spend** and **savings rate** this month
2. **Top 5 categories** with amounts and % of income
3. **Anomalies** if any (flag explicitly)
4. **One actionable recommendation** to reduce spend

### 6. Persist Analysis

```bash
philad-cfo analyze spending   # Writes to ~/.philad-cfo/kb/spending_analysis.md
```

---
name: net-worth
description: >
  Net worth tracking — total assets minus liabilities across all accounts.
  Activates on: net worth, total assets, how much am I worth, account balances,
  what do I have, assets, liabilities, wealth, balance sheet, financial snapshot,
  current balance, bank balance, account summary.
allowed-tools: Read Bash Write
---

# Net Worth Skill

## Overview

Calculates and tracks Phil's total net worth from Plaid bank/credit accounts
and IBKR investment portfolio. Writes snapshots to KB for historical tracking.

## Step-by-Step Instructions

### 1. Read Cached Snapshot First

```bash
cat ~/.philad-cfo/kb/snapshot.md
cat ~/.philad-cfo/kb/net_worth/history.md
```

If the snapshot is fresh (today's date), use it. Otherwise proceed to live fetch.

### 2. Fetch Live Data

```bash
philad-cfo net-worth --live
```

Or via sync:

```bash
philad-cfo sync plaid    # Updates snapshot.md
```

### 3. Calculate Net Worth

Net Worth = Σ(Assets) − Σ(Liabilities)

- **Assets**: current accounts, savings, ISA, investments, cash
- **Liabilities**: credit card balances, loans, outstanding bills

Credit cards and loans are automatically negated by the Plaid client.

### 4. Add IBKR Portfolio

```bash
philad-cfo positions
cat ~/.philad-cfo/kb/investments/positions.md
```

Add `net_liquidation` from IBKR to the Plaid net worth for the total picture.

### 5. Report Format

Always present:
1. **Total net worth** — single bold figure
2. **Breakdown table** — assets vs liabilities
3. **Month-on-month change** — compare to last history entry
4. **Trend** — improving / stable / declining

```bash
philad-cfo net-worth
```

### 6. Update KB

```bash
philad-cfo sync
```

This writes `snapshot.md` and appends to `net_worth/history.md`.

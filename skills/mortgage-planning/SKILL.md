---
name: mortgage-planning
description: >
  Mortgage readiness and planning for UK property purchase. Activates on:
  mortgage, house, property, deposit, LTV, loan to value, afford a house,
  when can I buy, how much to save, first time buyer, remortgage, stamp duty,
  solicitor, conveyancing, property price, house price, buying a home,
  mortgage rate, fixed rate, interest rate, lender, HSBC, Nationwide, Halifax,
  mortgage advisor, readiness score.
allowed-tools: Read Bash Write
---

# Mortgage Planning Skill

## Overview

Tracks Phil's progress toward buying a property. Calculates LTV, deposit gap,
monthly savings needed, and mortgage affordability. Uses Perplexity for
live rate research.

## Step-by-Step Instructions

### 1. Load Mortgage Config and Plan

```bash
cat ~/.philad-cfo/config.yaml     # mortgage section
cat ~/.philad-cfo/kb/mortgage/plan.md
```

Key config fields:
- `mortgage.target_price` — target property price
- `mortgage.current_deposit` — current deposit saved
- `mortgage.monthly_saving` — monthly saving amount
- `mortgage.target_ltv` — target LTV (default 0.80 = 80%)

### 2. Run Readiness Calculator

```bash
philad-cfo mortgage calc
```

This calculates:
- Required deposit = target_price × (1 − target_ltv)
- Deposit gap = required − current
- Months to goal = gap / monthly_saving
- Readiness score = current_deposit / required × 100 (capped at 100)
- Estimated monthly payment at current rates

### 3. Check Mortgage Status

```bash
philad-cfo mortgage status
```

Shows the saved plan from KB.

### 4. Research Current Rates

```bash
philad-cfo research "current UK mortgage rates 80 LTV 2-year fixed 2026"
```

Or use the Perplexity mortgage helper directly from Python:
```python
from src.perplexity_client import PerplexityClient
from src.config import load_config
cfg = load_config()
client = PerplexityClient(cfg.perplexity)
print(client.mortgage_rate_research(ltv=0.80, term_years=2))
```

### 5. Affordability Check

Lender stress test: typically qualify for 4–4.5× gross annual income.

```
Max loan ≈ annual_gross × 4.5
Max property ≈ max_loan + current_deposit
```

### 6. Stamp Duty (First Time Buyer, England 2025/26)

| Property Price | Rate |
| -------------- | ---- |
| Up to £425,000 | 0% |
| £425,001–£625,000 | 5% on portion above £425k |
| Above £625,000 | Standard rates apply (FTB relief lost) |

### 7. Report to User

Present:
1. **Readiness score** (X/100) with label (Not Ready / Getting Close / Ready)
2. **Deposit gap** and **months to target**
3. **Estimated monthly payment** at current market rates
4. **Recommended next action** (increase savings, research lenders, etc.)

### 8. Update KB

```bash
philad-cfo mortgage calc   # Writes to ~/.philad-cfo/kb/mortgage/plan.md
```

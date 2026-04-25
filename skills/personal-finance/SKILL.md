---
name: personal-finance
description: >
  Core personal finance knowledge and guidance for a UK household. Activates on:
  budget, savings, income, expenses, tax, pension, ISA, emergency fund,
  savings rate, financial health, afford, pay off, debt, interest, compound,
  financial goal, financial plan, net income, take home.
allowed-tools: Read Bash
---

# Personal Finance Skill

## Overview

Provides core financial analysis and advice in the context of Phil's
UK household finances. All figures default to GBP.

## Step-by-Step Instructions

### 1. Load Financial Context

```bash
cat ~/.philad-cfo/config.yaml          # Income and goal config
cat ~/.philad-cfo/kb/snapshot.md       # Current net worth snapshot
```

Key config fields to note:
- `income.monthly_net` — take-home pay
- `income.annual_gross` — gross salary
- `mortgage.current_deposit` / `mortgage.monthly_saving`

### 2. Calculate Key Ratios

**Savings Rate** = (Monthly Net Income − Monthly Spend) / Monthly Net Income × 100

Target: 20%+ is healthy; 30%+ is accelerated wealth-building.

```bash
philad-cfo analyze savings
```

**Emergency Fund** = 3–6 months of monthly expenses.

### 3. UK-Specific Context

- **ISA allowance**: £20,000/year (2025/26) — prioritise over taxable savings.
- **Pension**: Check if employer match is being maximised.
- **Tax bands** (2025/26): 0% up to £12,570, 20% to £50,270, 40% above.

### 4. Summarise for User

Provide a structured response:
1. Current financial health summary (savings rate, emergency fund status)
2. One immediate action item
3. One medium-term recommendation

Keep answers specific to Phil's numbers — do not use generic placeholders.

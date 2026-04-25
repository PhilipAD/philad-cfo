---
name: philad-cfo
description: >
  AI Personal CFO agent for Philip. Activates on any message containing:
  financial, CFO, money, budget, net worth, spending, savings, mortgage,
  invest, portfolio, IBKR, Plaid, wealth, income, expenses, afford, deposit,
  property, house purchase, trading, watchlist, IONQ, DWAVE, SNDK, VERT.
  This is the root skill — it loads context and delegates to sub-skills.
allowed-tools: Read Write Bash Grep Glob
---

# philad-cfo Root Skill

## What This System Is

philad-cfo is Philip's self-hosted AI CFO system. It aggregates financial data
from Plaid (banking), IBKR (investments), and manual config (income, mortgage
goals) into a local knowledge base, then uses AI agents and Perplexity for
analysis and reporting.

## Before You Begin

1. Read `AGENTS.md` — it is the primary onboarding document.
2. Check `~/.philad-cfo/config.yaml` exists. If not, run `philad-cfo init`.
3. Read the latest snapshot: `cat ~/.philad-cfo/kb/snapshot.md`

## Skill Routing

Match the user's intent to a sub-skill:

| Intent | Sub-skill |
| ------ | --------- |
| Net worth, account balances | `skills/net-worth/SKILL.md` |
| Spending, budgeting, categories | `skills/spending/SKILL.md` |
| Mortgage, property, deposit | `skills/mortgage-planning/SKILL.md` |
| Investments, positions, trading signals | `skills/investment-monitor/SKILL.md` |
| Research queries, market data | `skills/research/SKILL.md` |
| General finance, explanations | `skills/personal-finance/SKILL.md` |

## Quick Context Load

```bash
# Current snapshot
cat ~/.philad-cfo/kb/snapshot.md

# Latest positions
cat ~/.philad-cfo/kb/investments/positions.md

# Mortgage plan
cat ~/.philad-cfo/kb/mortgage/plan.md
```

## Running Core Commands

```bash
philad-cfo sync            # Pull latest from Plaid + IBKR
philad-cfo net-worth       # Print net worth
philad-cfo daily-report    # Full snapshot → Discord
philad-cfo monitor         # Investment signals
```

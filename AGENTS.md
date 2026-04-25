# AGENTS.md — philad-cfo Agent Onboarding

Primary reference for AI agents (Claude Code, Codex, Cursor, etc.) working in this repo.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        philad-cfo                               │
│                                                                 │
│  ┌──────────┐   ┌───────────┐   ┌────────────────────────────┐ │
│  │  Plaid   │   │   IBKR    │   │     Manual Config          │ │
│  │  (banks) │   │ (paper    │   │  (income, mortgage, goals) │ │
│  │  credit  │   │  trading) │   │                            │ │
│  └────┬─────┘   └─────┬─────┘   └────────────┬───────────────┘ │
│       │               │                      │                 │
│       └───────────────┴──────────────────────┘                 │
│                               │                                 │
│                        ┌──────▼──────┐                         │
│                        │ Knowledge   │  ~/.philad-cfo/kb/       │
│                        │    Base     │  snapshot.md             │
│                        │  (KB)       │  transactions/           │
│                        └──────┬──────┘  investments/            │
│                               │         mortgage/               │
│              ┌────────────────┼──────────────────────┐         │
│              │                │                      │         │
│       ┌──────▼──────┐  ┌──────▼──────┐    ┌─────────▼───────┐ │
│       │  Monitors   │  │  Markdown   │    │    Discord      │ │
│       │  hourly.py  │  │  Reports    │    │    Webhook      │ │
│       │  daily_     │  │             │    │                 │ │
│       │  report.py  │  └─────────────┘    └─────────────────┘ │
│       └─────────────┘                                          │
│                                                                 │
│       ┌──────────────────────────────────────────────────────┐ │
│       │              Perplexity API (pplx-2)                 │ │
│       │     Mortgage rates · Market intel · Scenarios        │ │
│       └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Context Checklist (Run These First)

```bash
cat ~/.philad-cfo/config.yaml                   # Phil's settings
cat ~/.philad-cfo/kb/snapshot.md                # Latest net worth
cat ~/.philad-cfo/kb/investments/positions.md   # IBKR positions
cat ~/.philad-cfo/kb/mortgage/plan.md           # Mortgage progress
cat ~/.philad-cfo/kb/net_worth/history.md       # Net worth history
```

---

## Skill Activation Triggers

Each skill in `skills/` activates when the user's message matches keywords:

| Skill | File | Activates On |
| ----- | ---- | ------------ |
| Root CFO | `skills/SKILL.md` | financial, CFO, money, budget |
| Personal Finance | `skills/personal-finance/SKILL.md` | budget, savings, ISA, pension, tax |
| Net Worth | `skills/net-worth/SKILL.md` | net worth, balance, assets, wealth |
| Spending | `skills/spending/SKILL.md` | spending, transactions, categories |
| Mortgage | `skills/mortgage-planning/SKILL.md` | mortgage, deposit, LTV, property |
| Investment | `skills/investment-monitor/SKILL.md` | IBKR, IONQ, DWAVE, RSI, signal |
| Research | `skills/research/SKILL.md` | research, rates, market, Perplexity |

Skills use progressive disclosure — load only the relevant SKILL.md.

---

## Data Sources

### Plaid (Banking)
- **What it provides**: account balances, transactions, credit cards, loans
- **Config**: `plaid.client_id`, `plaid.secret`, `plaid.environment`
- **Token**: stored at `~/.philad-cfo/cache/plaid_token.json` after `philad-cfo link`
- **Environments**: `sandbox` (test), `development` (real accounts, limited), `production`

### IBKR Gateway (Investments)
- **What it provides**: portfolio positions, account values, PnL
- **Connection**: `127.0.0.1:4002` (paper trading gateway must be running)
- **Account**: `phidso079` (paper account)
- **Client ID**: `10`
- **Note**: `paper_trading: true` — this is a paper account, no real money

### Perplexity (Research)
- **What it provides**: live web research, mortgage rates, market news
- **Model**: `pplx-2`
- **Config**: `perplexity.api_key`

### Manual Config
- **Income**: `income.monthly_net`, `income.annual_gross`
- **Mortgage goal**: `mortgage.target_price`, `mortgage.current_deposit`, etc.
- **Watchlist**: `investment.watchlist` — IONQ/DWAVE/SNDK/VERT

---

## Config.yaml Field Reference

| Section | Field | Type | Description |
| ------- | ----- | ---- | ----------- |
| `plaid` | `client_id` | str | Plaid API client ID |
| `plaid` | `secret` | str | Plaid API secret |
| `plaid` | `environment` | str | sandbox / development / production |
| `ibkr` | `host` | str | Gateway host (default `127.0.0.1`) |
| `ibkr` | `port` | int | `4002` paper, `4001` live |
| `ibkr` | `client_id` | int | IB client ID (default `10`) |
| `ibkr` | `account_id` | str | IB account number (`phidso079`) |
| `ibkr` | `paper_trading` | bool | Safety flag — must be `true` |
| `perplexity` | `api_key` | str | Perplexity API key |
| `perplexity` | `model` | str | `pplx-2` |
| `discord` | `webhook_url` | str | Discord incoming webhook URL |
| `discord` | `channel_id` | str | `1489761694908678354` |
| `income` | `monthly_net` | float | Take-home pay (GBP) |
| `income` | `annual_gross` | float | Gross salary (GBP) |
| `mortgage` | `target_price` | float | Property price goal |
| `mortgage` | `current_deposit` | float | Deposit saved so far |
| `mortgage` | `monthly_saving` | float | Monthly deposit contribution |
| `mortgage` | `target_ltv` | float | Target LTV (e.g. `0.80`) |
| `mortgage` | `interest_rate` | float | Rate for affordability calc |
| `investment` | `rsi_buy_threshold` | float | RSI < this → BUY signal |
| `investment` | `rsi_sell_threshold` | float | RSI > this → SELL signal |
| `investment` | `paper_only` | bool | Safety: no live execution |
| `investment` | `watchlist` | list | IONQ / DWAVE / SNDK / VERT |

---

## Workflow Examples

### Check Net Worth

```bash
# From cache (fast)
philad-cfo net-worth

# Live from Plaid
philad-cfo net-worth --live

# Or sync first, then read KB
philad-cfo sync plaid
cat ~/.philad-cfo/kb/snapshot.md
```

### Mortgage Readiness Check

```bash
# Run calculator (reads from config.yaml)
philad-cfo mortgage calc

# Check current plan
philad-cfo mortgage status

# Research live mortgage rates
philad-cfo research "best UK 80 LTV 2-year fixed mortgage rates April 2026"
```

### Daily Report (Manual)

```bash
philad-cfo daily-report               # full sync + report + Discord
philad-cfo daily-report --no-discord  # report only, no Discord
```

### Investment Signals

```bash
philad-cfo monitor                    # RSI/SMA/Bollinger on watchlist
philad-cfo monitor --discord          # + send to Discord

# Check specific ticker research
philad-cfo research "IONQ IonQ latest news and analyst ratings"
```

### Full Sync

```bash
philad-cfo sync           # Plaid + IBKR
philad-cfo sync plaid     # banks only
philad-cfo sync ibkr      # portfolio only
```

---

## Investment Strategy Constraints

**CRITICAL — never bypass these rules:**

1. **Paper trading only** — `ibkr.paper_trading: true` and `investment.paper_only: true` must remain set.
2. **Mean-reversion only** — BUY on RSI < 30, SELL on RSI > 70. No momentum, no FOMO trades.
3. **HIGH risk symbols** (DWAVE) — auto-execute is **always overridden to False** in `run_hourly_monitor()`. Always require explicit user confirmation.
4. **No aggressive sizing** — one signal review at a time, not bulk execution.

| Symbol | Risk | Auto-Execute |
| ------ | ---- | ------------ |
| SNDK | LOW | Yes (paper) |
| VERT | LOW | Yes (paper) |
| IONQ | MED | Yes (paper) |
| DWAVE | HIGH | **No — manual always** |

---

## KB Structure

```
~/.philad-cfo/
├── config.yaml                 ← all settings (never commit)
├── kb/
│   ├── snapshot.md             ← latest net worth (overwritten daily)
│   ├── spending_analysis.md    ← latest spending report
│   ├── transactions/
│   │   └── YYYY-MM-DD.md       ← daily transaction log
│   ├── net_worth/
│   │   └── history.md          ← time-series net worth
│   ├── mortgage/
│   │   └── plan.md             ← readiness plan
│   ├── investments/
│   │   ├── positions.md        ← current IBKR positions
│   │   └── signals_latest.md  ← last monitor run
│   ├── goals/
│   │   └── tracking.md
│   ├── snapshots/
│   │   └── daily_YYYY-MM-DD.md ← daily archive
│   └── research/
│       └── YYYY-MM-DD.md       ← Perplexity research log
└── cache/
    └── plaid_token.json        ← Plaid access token (never commit)
```

---

## Discord Output

Reports are sent to webhook `discord.webhook_url`, channel `1489761694908678354`.

The `DiscordReporter` class auto-splits messages exceeding Discord's 2000-char limit.

To send a manual message:
```python
from src.config import load_config
from src.output.discord import DiscordReporter
cfg = load_config()
r = DiscordReporter(cfg.discord)
r.send("**Test message** from philad-cfo")
```

---

## Perplexity Integration

```python
from src.config import load_config
from src.perplexity_client import PerplexityClient

cfg = load_config()
client = PerplexityClient(cfg.perplexity)

# Pre-built helpers
client.mortgage_rate_research(ltv=0.80, term_years=2)
client.investment_thesis_research("IONQ")
client.market_intelligence("UK inflation outlook 2026")
client.scenario_analysis("Bank of England cuts rates by 0.5% in Q3 2026")

# Or arbitrary query
client.query("What is the current Help to Buy ISA bonus rate?")
```

Falls back gracefully if `PERPLEXITY_API_KEY` is not set (raises `ConfigurationError`).

---

## Cron Setup

```bash
# Add to crontab: crontab -e
0 8 * * *    philad-cfo daily-report          # 08:00 daily
0 * * * *    philad-cfo hourly-monitor        # top of every hour
```

---

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

Test files:
- `tests/test_config.py` — config loading, env overrides, defaults
- `tests/test_kb.py` — KB read/write/append, all domain writers
- `tests/test_plaid_client.py` — Plaid client (fully mocked)
- `tests/test_monitors.py` — RSI/Bollinger math, signal generation, daily report

---

## Extending This System

**To add a new data source:**
1. Create `src/<source>_client.py` with a typed client class
2. Add config fields to `src/config.py` and `config/config.yaml.example`
3. Add a sync helper in `src/skills/sync.py`
4. Update `cmd_sync` in `src/cli.py`
5. Add a skill in `skills/<name>/SKILL.md`

**To add a new CLI command:**
1. Write a `cmd_<name>` function in `src/cli.py`
2. Add a subparser in `build_parser()`
3. Set `p_<name>.set_defaults(func=cmd_<name>)`

**To add a new skill:**
1. Create `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`, `allowed-tools`)
2. Add to the routing table in `skills/SKILL.md` and this file

---

## Security Notes

- `~/.philad-cfo/config.yaml` and `cache/plaid_token.json` contain secrets — never commit them.
- `config/config.yaml.example` and `config/.env.example` are safe to commit.
- The `.gitignore` should exclude `*.yaml` in the home directory and `cache/`.

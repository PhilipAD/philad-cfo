# Design Document — philad-cfo

## Overview

philad-cfo is a self-hosted personal CFO system for Philip. It aggregates financial
data from Plaid (banking), IBKR (paper trading), and manual YAML configuration into a
local filesystem knowledge base, and exposes a CLI for reports, signals, and research.

## Goals

- **Single source of truth**: all financial data converges into `~/.philad-cfo/kb/`
- **AI-agent-first**: skills directory and AGENTS.md are the primary interface for AI agents
- **No cloud lock-in**: all data stored locally as markdown; no proprietary database
- **Safe by default**: paper trading only; HIGH-risk symbols always require manual review
- **Composable**: each component (Plaid, IBKR, Perplexity, Discord) is independently usable

## Non-Goals

- Real-money automated trading
- Multi-user support
- Web UI or dashboard
- Tax filing automation

---

## Architecture

### Components

```
CLI (src/cli.py)
    ├── Config loader (src/config.py)          — typed dataclasses from YAML
    ├── Knowledge Base (src/kb.py)             — markdown filesystem store
    ├── Data sources
    │   ├── Plaid client (src/plaid_client.py) — banking data
    │   ├── IBKR client (src/ibkr_client.py)   — portfolio data
    │   └── Perplexity (src/perplexity_client.py) — research
    ├── Monitors
    │   ├── hourly.py                          — RSI/Bollinger signals via yfinance
    │   └── daily_report.py                   — daily snapshot builder
    └── Output
        ├── discord.py                         — webhook delivery
        └── markdown_report.py                — report generation
```

### Data Flow

```
Plaid API ──────────────────┐
                            ▼
IBKR Gateway ──────► Knowledge Base (markdown) ──► Discord Webhook
                            │                  └──► Terminal output
Manual Config ──────────────┘
                            │
Perplexity API ─────────────┘ (research, on-demand)
```

### Knowledge Base Design

The KB is intentionally a flat-file markdown store under `~/.philad-cfo/kb/`.
This makes it human-readable, git-diffable, and trivially parseable by AI agents.

Each domain has its own subdirectory:
- `transactions/YYYY-MM-DD.md` — daily transaction logs
- `net_worth/history.md` — append-only net worth time series
- `investments/positions.md` — overwritten on each IBKR sync
- `mortgage/plan.md` — overwritten on each `mortgage calc` run
- `goals/tracking.md` — savings goal progress
- `snapshots/daily_YYYY-MM-DD.md` — archived daily reports
- `research/YYYY-MM-DD.md` — append-only Perplexity research log

---

## Key Design Decisions

### Why Markdown for the KB?

Alternatives considered: SQLite, JSON, CSV.

Markdown was chosen because:
1. AI agents read and write markdown natively without a query layer
2. Human-readable without tooling
3. Directly embeddable in prompts as context
4. Trivially renderable in Discord and GitHub

### Why argparse instead of Click?

Click provides a better API but adds a dependency and implicit magic.
argparse is stdlib, zero-dependency, and `--help` works identically.
Given the CLI is the integration surface for AI agents running shell commands,
predictability matters more than ergonomics.

### Why ib_insync instead of the native IBKR API?

`ib_insync` wraps the EClient/EWrapper event model in a synchronous, asyncio-compatible
interface. It is the de-facto standard for Python IBKR automation and supports
`readonly=True` for safe read-only connections.

### Why yfinance for signals instead of IBKR market data?

For the mean-reversion monitor, yfinance provides:
- No additional IBKR connection/client-ID required
- No market data subscription fees
- Sufficient data quality for RSI/SMA/Bollinger calculations on daily bars
- Simpler failure mode (HTTP vs. socket connection)

IBKR market data is used only for position mark-to-market in `get_positions()`.

### Signal Execution Safety

Three layers prevent accidental live trade execution:
1. `ibkr.paper_trading: true` — config-level flag
2. `investment.paper_only: true` — investment-level flag  
3. `run_hourly_monitor()` hard-codes `auto_execute = False` for any symbol with `risk == "HIGH"`

This means even a config mistake cannot cause a DWAVE live trade.

---

## Config Schema

Defined as typed Python dataclasses in `src/config.py`. The YAML is loaded with
PyYAML and mapped manually (no Pydantic/Attrs) to keep dependencies minimal.

Environment variables override YAML values via `_apply_env_overrides()`, following
the 12-factor app convention.

---

## Error Handling

- `ConfigurationError` — missing/invalid config, missing API keys
- `requests.HTTPError` — Plaid / Perplexity HTTP failures
- IBKR connection failures — caught and surfaced as `ConfigurationError`
- CLI: all errors print to stderr and exit with code 1; partial sync failures
  are collected and printed as warnings rather than aborting the full sync

---

## Testing Strategy

| Layer | Approach |
| ----- | -------- |
| Config loading | Unit tests with temp YAML files and monkeypatched env vars |
| KB | Unit tests with tmp_path fixture — no mocking needed |
| Plaid client | Fully mocked Plaid SDK (no network calls) |
| IBKR client | Integration test requires running gateway — not in CI |
| Monitors | Unit tests for RSI/Bollinger math; yfinance mocked via patch |
| CLI | Smoke tests via `py_compile` and `--help` invocation |

---

## Future Considerations

These are explicitly out of scope for v0.1 but noted for future reference:

- **Real-time streaming**: IBKR streaming quotes via `ib_insync` subscriptions
- **Portfolio optimisation**: mean-variance / Kelly criterion position sizing
- **Automated remortgage alerts**: when current deal approaches expiry
- **Property price tracking**: Rightmove/Zoopla data integration
- **Tax year summary**: income tax, CGT, ISA utilisation report

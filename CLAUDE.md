# CLAUDE.md — Project Context for philad-cfo

## What This Repo Is

philad-cfo is Philip's self-hosted AI CFO system. It is a Python CLI (`philad-cfo`) that
aggregates financial data from Plaid (banking), IBKR (paper trading), and manual YAML config,
then produces reports, investment signals, and mortgage planning calculations.

**Primary agent onboarding doc**: `AGENTS.md` — read it before doing any work.

## Architecture in 30 Seconds

```
src/config.py          ← AppConfig dataclasses, YAML loader
src/kb.py              ← Filesystem KB (markdown files under ~/.philad-cfo/kb/)
src/plaid_client.py    ← Plaid API: accounts, transactions, balances
src/ibkr_client.py     ← IBKR Gateway: positions via ib_insync
src/perplexity_client.py ← Perplexity API: web research
src/monitors/hourly.py ← Mean-reversion signals (RSI/SMA/Bollinger via yfinance)
src/monitors/daily_report.py ← Daily snapshot builder
src/output/discord.py  ← Discord webhook sender
src/output/markdown_report.py ← Report generators
src/skills/sync.py     ← Plaid+IBKR sync orchestration
src/cli.py             ← argparse CLI entry point
```

## Key Facts

- **IBKR**: `127.0.0.1:4002`, account `phidso079`, client_id `10`
- **Watchlist**: IONQ (MED), DWAVE (HIGH), SNDK (LOW), VERT (LOW)
- **RSI signals**: < 30 = BUY, > 70 = SELL
- **DWAVE is HIGH risk** — auto_execute is always overridden to False
- **Discord channel**: `1489761694908678354`
- **KB root**: `~/.philad-cfo/kb/`
- **Config**: `~/.philad-cfo/config.yaml`
- **No real trading** — `paper_trading: true` always

## Python Standards

- Python 3.10+, type hints on all public functions
- Google-style docstrings
- `ConfigurationError` for missing API keys / config
- No wildcard imports

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Adding Code

- Config changes → `src/config.py` dataclass + `config/config.yaml.example`
- New CLI command → `cmd_<name>` function + subparser in `build_parser()` in `src/cli.py`
- New KB writer → method on `KnowledgeBase` in `src/kb.py`
- New skill → `skills/<name>/SKILL.md` with YAML frontmatter

## What NOT to Do

- Do not set `paper_trading: false` or `paper_only: false`
- Do not auto-execute DWAVE trades
- Do not commit `~/.philad-cfo/config.yaml` or `cache/plaid_token.json`
- Do not add momentum/growth trading strategies — mean-reversion only

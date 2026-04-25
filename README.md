# philad-cfo

AI Personal CFO — Plaid + IBKR + Perplexity financial intelligence in a self-hosted CLI.

## Quick Install

```bash
git clone https://github.com/phildawson/philad-cfo && cd philad-cfo
bash scripts/install.sh          # pip install -e .
philad-cfo init                  # create ~/.philad-cfo/config.yaml
```

## Setup

```bash
# 1. Edit config
nano ~/.philad-cfo/config.yaml

# 2. Link bank accounts
philad-cfo link                  # prints Plaid OAuth URL
philad-cfo link --exchange <public_token>
```

## CLI Commands

| Command | Description |
| ------- | ----------- |
| `philad-cfo init` | Create config directory and example config |
| `philad-cfo link` | Get Plaid Link URL to connect bank accounts |
| `philad-cfo sync` | Pull all accounts from Plaid + IBKR → KB |
| `philad-cfo sync plaid` | Plaid sync only |
| `philad-cfo sync ibkr` | IBKR sync only |
| `philad-cfo net-worth` | Print current net worth from KB |
| `philad-cfo net-worth --live` | Fetch live from Plaid |
| `philad-cfo analyze spending` | Spending by category (last 30 days) |
| `philad-cfo analyze savings` | Savings rate + income breakdown |
| `philad-cfo mortgage status` | Mortgage readiness plan from KB |
| `philad-cfo mortgage calc` | LTV + affordability calculator |
| `philad-cfo positions` | Print IBKR paper portfolio |
| `philad-cfo monitor` | Mean-reversion signals (RSI/SMA/BB) |
| `philad-cfo monitor --discord` | Signals + send to Discord |
| `philad-cfo research <query>` | Perplexity research query |
| `philad-cfo daily-report` | Full snapshot → KB + Discord |
| `philad-cfo hourly-monitor` | Watchlist check → Discord |

## Config Fields (key)

| Field | Description |
| ----- | ----------- |
| `plaid.client_id` / `plaid.secret` | Plaid API credentials |
| `ibkr.port` | `4002` = paper, `4001` = live |
| `ibkr.account_id` | `phidso079` |
| `perplexity.api_key` | pplx-… from perplexity.ai |
| `discord.webhook_url` | Server Settings > Webhooks |
| `income.monthly_net` | Take-home pay (GBP) |
| `mortgage.target_price` | Target property price |
| `investment.paper_only` | `true` — never execute real trades |

## Cron Schedule

```bash
# Daily report at 08:00
0 8 * * * philad-cfo daily-report

# Hourly watchlist monitor
0 * * * * philad-cfo hourly-monitor
```

## For AI Agents

Read `AGENTS.md` for full onboarding. Skills in `skills/` directory.

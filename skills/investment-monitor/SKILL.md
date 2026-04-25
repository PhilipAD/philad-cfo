---
name: investment-monitor
description: >
  Investment monitoring via IBKR and mean-reversion signals. Activates on:
  invest, portfolio, positions, IBKR, IONQ, DWAVE, SNDK, VERT, RSI, signal,
  mean reversion, buy signal, sell signal, stock, equity, shares, watchlist,
  paper trading, trading, market, stock price, technical analysis, Bollinger,
  SMA, momentum, quantum computing, stock alert.
allowed-tools: Read Bash Write
---

# Investment Monitor Skill

## Overview

Monitors Phil's IBKR paper trading portfolio and watchlist for mean-reversion
signals using RSI, SMA, and Bollinger Bands via yfinance.

## Watchlist

| Symbol | Company | Risk | Auto-Execute |
| ------ | ------- | ---- | ------------ |
| IONQ | IonQ (quantum computing) | MED | Yes |
| DWAVE | D-Wave Quantum | HIGH | **No — manual review always** |
| SNDK | SanDisk | LOW | Yes |
| VERT | Vert Capital | LOW | Yes |

**Rule**: HIGH risk (DWAVE) is NEVER auto-executed regardless of config.

## Step-by-Step Instructions

### 1. Check Current Positions

```bash
philad-cfo positions
cat ~/.philad-cfo/kb/investments/positions.md
```

### 2. Run Mean-Reversion Monitor

```bash
philad-cfo monitor
```

Signals generated:
- **BUY**: RSI < 30 (oversold)
- **SELL**: RSI > 70 (overbought)
- **HOLD**: RSI in neutral zone [30, 70]

### 3. Understanding the Signal Table

```
| Symbol | Risk | Action | RSI  | Price | Auto? | Reason          |
| IONQ   | MED  | BUY    | 27.3 | 8.45  | Yes   | RSI below 30    |
| DWAVE  | HIGH | SELL   | 72.1 | 4.20  | No    | RSI above 70    |
```

- **Auto=Yes + LOW/MED risk**: can execute via IBKR paper account
- **Auto=No or HIGH risk**: requires manual review and confirmation

### 4. Run Hourly Monitor (with Discord alerts)

```bash
philad-cfo hourly-monitor
```

Sends signal table to Discord channel 1489761694908678354.

### 5. Research a Symbol

```bash
philad-cfo research "IONQ investment thesis April 2026"
philad-cfo research "DWAVE quantum computing catalyst news"
```

### 6. Portfolio Summary

```bash
philad-cfo sync ibkr    # Refreshes positions.md
```

IBKR connection: `127.0.0.1:4002` (paper gateway), account `phidso079`.

### 7. Strategy Constraints

- **Mean-reversion only** — no momentum or growth chasing.
- **Paper trading only** (`paper_only: true` in config).
- No aggressive position sizing. One signal = one review, not a rush.
- Sync positions after any manual paper trade to keep KB current.

### 8. Report Format

Present signals as:
1. Action table (Symbol / Risk / Action / RSI / Auto)
2. Any HOLD → note it requires no action
3. BUY/SELL → explain the signal and confirm user wants to act
4. For HIGH risk: always ask for explicit confirmation before acting

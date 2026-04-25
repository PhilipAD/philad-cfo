"""Tests for src/monitors/hourly.py and src/monitors/daily_report.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.config import InvestmentConfig, WatchlistItem
from src.monitors.hourly import (
    Signal,
    _compute_bollinger,
    _compute_rsi,
    check_symbol,
    format_signals_table,
    run_hourly_monitor,
)
from src.monitors.daily_report import build_daily_report, run_daily_report
from src.kb import KnowledgeBase


# ─── RSI / Bollinger helpers ────────────────────────────────────────────────


def _make_series(values: list[float]) -> pd.Series:
    return pd.Series(values, dtype=float)


def test_compute_rsi_neutral() -> None:
    prices = _make_series([10.0] * 30)
    rsi = _compute_rsi(prices)
    assert rsi == pytest.approx(50.0)


def test_compute_rsi_rising() -> None:
    prices = _make_series(list(range(1, 31)))
    rsi = _compute_rsi(prices)
    assert rsi > 70


def test_compute_rsi_falling() -> None:
    prices = _make_series(list(range(30, 0, -1)))
    rsi = _compute_rsi(prices)
    assert rsi < 30


def test_compute_rsi_too_short() -> None:
    prices = _make_series([10.0] * 5)
    rsi = _compute_rsi(prices)
    assert rsi == pytest.approx(50.0)


def test_compute_rsi_no_loss_returns_100() -> None:
    prices = _make_series([float(i) for i in range(1, 50)])
    rsi = _compute_rsi(prices)
    assert rsi == pytest.approx(100.0)


def test_compute_bollinger_returns_three_values() -> None:
    prices = _make_series([float(i) for i in range(1, 30)])
    sma, upper, lower = _compute_bollinger(prices)
    assert upper > sma > lower


def test_compute_bollinger_too_short() -> None:
    prices = _make_series([5.0] * 3)
    sma, upper, lower = _compute_bollinger(prices)
    assert sma == upper == lower == pytest.approx(5.0)


# ─── check_symbol ───────────────────────────────────────────────────────────


def _mock_history(rsi_direction: str = "neutral") -> MagicMock:
    """Return a fake yfinance Ticker with history producing a known RSI."""
    if rsi_direction == "oversold":
        closes = list(range(50, 20, -1))  # falling → RSI < 30
    elif rsi_direction == "overbought":
        closes = list(range(1, 50))       # rising → RSI > 70
    else:
        closes = [25.0] * 40              # flat → RSI ≈ 50

    df = pd.DataFrame({"Close": closes})
    ticker = MagicMock()
    ticker.history.return_value = df
    return ticker


def test_check_symbol_buy_signal() -> None:
    item = WatchlistItem(symbol="IONQ", risk="MED", auto_execute=True)
    with patch("src.monitors.hourly.yf.Ticker", return_value=_mock_history("oversold")):
        signal = check_symbol(item, rsi_buy=30.0, rsi_sell=70.0)
    assert signal is not None
    assert signal.action == "BUY"
    assert signal.rsi < 30


def test_check_symbol_sell_signal() -> None:
    item = WatchlistItem(symbol="SNDK", risk="LOW", auto_execute=True)
    with patch("src.monitors.hourly.yf.Ticker", return_value=_mock_history("overbought")):
        signal = check_symbol(item, rsi_buy=30.0, rsi_sell=70.0)
    assert signal is not None
    assert signal.action == "SELL"
    assert signal.rsi > 70


def test_check_symbol_hold() -> None:
    item = WatchlistItem(symbol="VERT", risk="LOW", auto_execute=True)
    with patch("src.monitors.hourly.yf.Ticker", return_value=_mock_history("neutral")):
        signal = check_symbol(item, rsi_buy=30.0, rsi_sell=70.0)
    assert signal is not None
    assert signal.action == "HOLD"


def test_check_symbol_empty_history_returns_none() -> None:
    item = WatchlistItem(symbol="XXX", risk="LOW", auto_execute=False)
    ticker = MagicMock()
    ticker.history.return_value = pd.DataFrame()
    with patch("src.monitors.hourly.yf.Ticker", return_value=ticker):
        signal = check_symbol(item)
    assert signal is None


def test_check_symbol_exception_returns_none() -> None:
    item = WatchlistItem(symbol="ERR", risk="LOW", auto_execute=False)
    with patch("src.monitors.hourly.yf.Ticker", side_effect=Exception("network")):
        signal = check_symbol(item)
    assert signal is None


# ─── run_hourly_monitor ──────────────────────────────────────────────────────


def _cfg_with_watchlist() -> MagicMock:
    cfg = MagicMock()
    cfg.investment.watchlist = [
        WatchlistItem("IONQ", "MED", True),
        WatchlistItem("DWAVE", "HIGH", False),
        WatchlistItem("SNDK", "LOW", True),
        WatchlistItem("VERT", "LOW", True),
    ]
    cfg.investment.rsi_buy_threshold = 30.0
    cfg.investment.rsi_sell_threshold = 70.0
    return cfg


def test_run_hourly_monitor_high_risk_never_auto() -> None:
    cfg = _cfg_with_watchlist()
    oversold = _mock_history("oversold")
    with patch("src.monitors.hourly.yf.Ticker", return_value=oversold):
        signals = run_hourly_monitor(cfg)
    dwave_signal = next((s for s in signals if s.symbol == "DWAVE"), None)
    assert dwave_signal is not None
    assert dwave_signal.auto_execute is False


def test_run_hourly_monitor_returns_all_symbols() -> None:
    cfg = _cfg_with_watchlist()
    with patch("src.monitors.hourly.yf.Ticker", return_value=_mock_history("neutral")):
        signals = run_hourly_monitor(cfg)
    symbols = {s.symbol for s in signals}
    assert symbols == {"IONQ", "DWAVE", "SNDK", "VERT"}


# ─── format_signals_table ────────────────────────────────────────────────────


def test_format_signals_table_empty() -> None:
    result = format_signals_table([])
    assert "_No signals" in result


def test_format_signals_table_with_signals() -> None:
    signals = [
        Signal(
            symbol="IONQ", risk="MED", action="BUY", rsi=25.0,
            price=8.50, sma_20=9.0, bb_upper=10.0, bb_lower=7.0,
            auto_execute=True, reason="RSI below 30",
        )
    ]
    result = format_signals_table(signals)
    assert "IONQ" in result
    assert "BUY" in result
    assert "25.0" in result


# ─── build_daily_report ──────────────────────────────────────────────────────


def test_build_daily_report_contains_sections() -> None:
    report = build_daily_report(
        net_worth=50000.0,
        account_breakdown={"Current": 30000.0, "Savings": 20000.0},
        spending_summary={"Food": 400.0, "Transport": 150.0},
        positions=[{"symbol": "IONQ", "qty": 100, "market_value": 850.0, "pnl": 50.0}],
        signals_md="| IONQ | MED | HOLD | 50.0 |",
    )
    assert "Net Worth" in report
    assert "50,000.00" in report
    assert "Spending" in report
    assert "IONQ" in report
    assert "Investment Signals" in report


def test_build_daily_report_empty_inputs() -> None:
    report = build_daily_report(
        net_worth=0.0,
        account_breakdown={},
        spending_summary={},
        positions=[],
    )
    assert "Daily CFO Report" in report


# ─── run_daily_report ────────────────────────────────────────────────────────


def test_run_daily_report_saves_to_kb(tmp_path: Path) -> None:
    kb = KnowledgeBase(tmp_path / "kb")
    cfg = MagicMock()

    report_md, kb_path = run_daily_report(
        cfg=cfg,
        kb=kb,
        net_worth=75000.0,
        account_breakdown={"Bank": 75000.0},
        spending_summary={"Groceries": 300.0},
        positions=[],
    )
    assert "Daily CFO Report" in report_md
    assert (tmp_path / "kb" / "snapshot.md").exists()
    assert Path(kb_path).exists()

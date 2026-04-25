"""Tests for src/config.py — config loader."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from src.config import (
    AppConfig,
    ConfigurationError,
    _default_watchlist,
    load_config,
)


def _write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data))
    return p


def test_load_minimal_config(tmp_path: Path) -> None:
    p = _write_config(tmp_path, {})
    cfg = load_config(p)
    assert isinstance(cfg, AppConfig)
    assert cfg.ibkr.host == "127.0.0.1"
    assert cfg.ibkr.port == 4002
    assert cfg.ibkr.account_id == "phidso079"


def test_load_full_config(tmp_path: Path) -> None:
    data = {
        "plaid": {"client_id": "abc", "secret": "xyz", "environment": "sandbox"},
        "ibkr": {"host": "127.0.0.1", "port": 4002, "client_id": 10, "account_id": "phidso079"},
        "income": {"monthly_net": 5000.0, "annual_gross": 80000.0, "currency": "GBP"},
        "mortgage": {
            "target_price": 500000,
            "current_deposit": 60000,
            "monthly_saving": 1500,
            "target_ltv": 0.80,
            "interest_rate": 0.045,
            "term_years": 25,
        },
    }
    p = _write_config(tmp_path, data)
    cfg = load_config(p)
    assert cfg.plaid.client_id == "abc"
    assert cfg.income.monthly_net == 5000.0
    assert cfg.mortgage.target_price == 500000.0


def test_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLAID_CLIENT_ID", "env-client")
    monkeypatch.setenv("PLAID_SECRET", "env-secret")
    p = _write_config(tmp_path, {})
    cfg = load_config(p)
    assert cfg.plaid.client_id == "env-client"
    assert cfg.plaid.secret == "env-secret"


def test_default_watchlist() -> None:
    wl = _default_watchlist()
    symbols = {w["symbol"] for w in wl}
    assert symbols == {"IONQ", "DWAVE", "SNDK", "VERT"}


def test_watchlist_risk_levels(tmp_path: Path) -> None:
    p = _write_config(tmp_path, {})
    cfg = load_config(p)
    risk_map = {w.symbol: w.risk for w in cfg.investment.watchlist}
    assert risk_map["DWAVE"] == "HIGH"
    assert risk_map["SNDK"] == "LOW"
    assert risk_map["VERT"] == "LOW"
    assert risk_map["IONQ"] == "MED"


def test_dwave_auto_execute_false(tmp_path: Path) -> None:
    p = _write_config(tmp_path, {})
    cfg = load_config(p)
    dwave = next(w for w in cfg.investment.watchlist if w.symbol == "DWAVE")
    assert dwave.auto_execute is False


def test_missing_config_file_returns_defaults() -> None:
    cfg = load_config(Path("/nonexistent/path/config.yaml"))
    assert cfg.ibkr.port == 4002

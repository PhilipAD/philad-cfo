"""Tests for src/kb.py — knowledge base read/write."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from src.kb import KnowledgeBase


@pytest.fixture
def kb(tmp_path: Path) -> KnowledgeBase:
    return KnowledgeBase(tmp_path / "kb")


def test_write_and_read(kb: KnowledgeBase) -> None:
    kb.write("test.md", "# Hello\n")
    assert kb.read("test.md") == "# Hello\n"


def test_read_missing_returns_none(kb: KnowledgeBase) -> None:
    assert kb.read("nonexistent.md") is None


def test_append(kb: KnowledgeBase) -> None:
    kb.write("log.md", "line1\n")
    kb.append("log.md", "line2\n")
    assert kb.read("log.md") == "line1\nline2\n"


def test_list_files(kb: KnowledgeBase) -> None:
    kb.write("a.md", "")
    kb.write("sub/b.md", "")
    files = kb.list_files()
    names = {f.name for f in files}
    assert "a.md" in names
    assert "b.md" in names


def test_write_snapshot(kb: KnowledgeBase) -> None:
    breakdown = {"Current Account": 5000.0, "Credit Card": -200.0}
    path = kb.write_snapshot(4800.0, breakdown)
    content = path.read_text()
    assert "4,800.00" in content
    assert "Current Account" in content
    assert "Credit Card" in content


def test_write_transaction_log(kb: KnowledgeBase) -> None:
    txns = [
        {"name": "Tesco", "amount": 45.20, "category": "Food", "date": "2026-04-01"},
        {"name": "Netflix", "amount": 15.99, "category": "Entertainment", "date": "2026-04-02"},
    ]
    d = date(2026, 4, 1)
    path = kb.write_transaction_log(txns, log_date=d)
    content = path.read_text()
    assert "Tesco" in content
    assert "Netflix" in content
    assert "2026-04-01" in str(path)


def test_write_empty_transaction_log(kb: KnowledgeBase) -> None:
    path = kb.write_transaction_log([], log_date=date(2026, 4, 1))
    assert "_No transactions._" in path.read_text()


def test_append_net_worth_history_creates_file(kb: KnowledgeBase) -> None:
    path = kb.append_net_worth_history(50000.0)
    content = path.read_text()
    assert "50,000.00" in content
    assert "Net Worth History" in content


def test_append_net_worth_history_appends(kb: KnowledgeBase) -> None:
    kb.append_net_worth_history(50000.0)
    kb.append_net_worth_history(51000.0)
    content = (kb.root / "net_worth" / "history.md").read_text()
    assert "50,000.00" in content
    assert "51,000.00" in content


def test_write_positions(kb: KnowledgeBase) -> None:
    positions = [
        {"symbol": "IONQ", "qty": 100, "avg_cost": 8.00, "market_value": 850.0, "pnl": 50.0},
        {"symbol": "DWAVE", "qty": 200, "avg_cost": 3.50, "market_value": 800.0, "pnl": 100.0},
    ]
    path = kb.write_positions(positions)
    content = path.read_text()
    assert "IONQ" in content
    assert "DWAVE" in content


def test_write_mortgage_plan(kb: KnowledgeBase) -> None:
    data = {
        "target_price": 500000,
        "deposit": 60000,
        "ltv": 0.80,
        "monthly_saving": 1500,
        "months_to_goal": 21,
        "readiness_score": 75,
        "notes": "On track",
    }
    path = kb.write_mortgage_plan(data)
    content = path.read_text()
    assert "500,000" in content
    assert "75/100" in content
    assert "On track" in content


def test_write_goals(kb: KnowledgeBase) -> None:
    goals = [
        {"name": "House Deposit", "target": 100000, "current": 60000, "monthly": 1500, "eta": "2027-01"},
    ]
    path = kb.write_goals(goals)
    content = path.read_text()
    assert "House Deposit" in content
    assert "100,000" in content


def test_json_cache_roundtrip(kb: KnowledgeBase) -> None:
    data = {"access_token": "test-token-123", "item_id": "abc"}
    kb.write_json_cache("plaid_token", data)
    loaded = kb.read_json_cache("plaid_token")
    assert loaded is not None
    assert loaded["access_token"] == "test-token-123"


def test_json_cache_missing_returns_none(kb: KnowledgeBase) -> None:
    assert kb.read_json_cache("nonexistent") is None


def test_write_creates_nested_dirs(kb: KnowledgeBase) -> None:
    kb.write("deep/nested/dir/file.md", "content")
    assert (kb.root / "deep/nested/dir/file.md").exists()

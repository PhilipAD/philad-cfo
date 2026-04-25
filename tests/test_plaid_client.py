"""Tests for src/plaid_client.py — Plaid API client (mocked)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import ConfigurationError, PlaidConfig
from src.plaid_client import PlaidClient


@pytest.fixture
def plaid_cfg() -> PlaidConfig:
    return PlaidConfig(
        client_id="test-client-id",
        secret="test-secret",
        environment="sandbox",
    )


@pytest.fixture
def client(plaid_cfg: PlaidConfig, tmp_path: Path) -> PlaidClient:
    with patch("src.plaid_client.plaid_api.PlaidApi"):
        c = PlaidClient(plaid_cfg, token_path=tmp_path / "token.json")
    return c


def test_missing_client_id_raises() -> None:
    cfg = PlaidConfig(client_id="", secret="secret")
    with pytest.raises(ConfigurationError, match="PLAID_CLIENT_ID"):
        with patch("src.plaid_client.plaid_api.PlaidApi"):
            PlaidClient(cfg)


def test_missing_secret_raises() -> None:
    cfg = PlaidConfig(client_id="id", secret="")
    with pytest.raises(ConfigurationError, match="PLAID_SECRET"):
        with patch("src.plaid_client.plaid_api.PlaidApi"):
            PlaidClient(cfg)


def test_create_link_token(client: PlaidClient) -> None:
    mock_response = {"link_token": "link-sandbox-abc123"}
    client.client.link_token_create = MagicMock(return_value=mock_response)
    token = client.create_link_token()
    assert token == "link-sandbox-abc123"
    client.client.link_token_create.assert_called_once()


def test_exchange_public_token(client: PlaidClient, tmp_path: Path) -> None:
    mock_response = {"access_token": "access-sandbox-xyz", "item_id": "item-123"}
    client.client.item_public_token_exchange = MagicMock(return_value=mock_response)
    token = client.exchange_public_token("public-sandbox-abc")
    assert token == "access-sandbox-xyz"
    assert client._access_token == "access-sandbox-xyz"


def test_exchange_saves_token_file(client: PlaidClient, tmp_path: Path) -> None:
    client.token_path = tmp_path / "plaid_token.json"
    mock_response = {"access_token": "access-sandbox-saved", "item_id": "item-999"}
    client.client.item_public_token_exchange = MagicMock(return_value=mock_response)
    client.exchange_public_token("public-sandbox-x")
    assert client.token_path.exists()
    data = json.loads(client.token_path.read_text())
    assert data["access_token"] == "access-sandbox-saved"


def test_load_token_from_file(plaid_cfg: PlaidConfig, tmp_path: Path) -> None:
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps({"access_token": "access-sandbox-loaded"}))
    with patch("src.plaid_client.plaid_api.PlaidApi"):
        c = PlaidClient(plaid_cfg, token_path=token_path)
    assert c._access_token == "access-sandbox-loaded"


def test_require_token_raises_without_token(client: PlaidClient) -> None:
    client._access_token = None
    with pytest.raises(ConfigurationError, match="philad-cfo link"):
        client._require_token()


def test_get_accounts(client: PlaidClient) -> None:
    client._access_token = "access-sandbox-test"
    mock_accounts = [
        {
            "account_id": "acc1",
            "name": "Current Account",
            "type": "depository",
            "subtype": "checking",
            "balances": {"available": 5000.0, "current": 5200.0, "iso_currency_code": "GBP"},
        },
        {
            "account_id": "acc2",
            "name": "Credit Card",
            "type": "credit",
            "subtype": "credit card",
            "balances": {"available": 1000.0, "current": 200.0, "iso_currency_code": "GBP"},
        },
    ]
    client.client.accounts_get = MagicMock(return_value={"accounts": mock_accounts})
    accounts = client.get_accounts()
    assert len(accounts) == 2
    assert accounts[0]["name"] == "Current Account"
    assert accounts[1]["type"] == "credit"


def test_get_net_worth_negates_credit(client: PlaidClient) -> None:
    client._access_token = "access-sandbox-test"
    mock_accounts = [
        {
            "account_id": "acc1",
            "name": "Savings",
            "type": "depository",
            "subtype": "savings",
            "balances": {"available": 20000.0, "current": 20000.0, "iso_currency_code": "GBP"},
        },
        {
            "account_id": "acc2",
            "name": "Visa Card",
            "type": "credit",
            "subtype": "credit card",
            "balances": {"available": None, "current": 500.0, "iso_currency_code": "GBP"},
        },
    ]
    client.client.accounts_get = MagicMock(return_value={"accounts": mock_accounts})
    net_worth, breakdown = client.get_net_worth()
    assert net_worth == pytest.approx(19500.0)
    assert breakdown["Visa Card"] == pytest.approx(-500.0)


def test_get_transactions(client: PlaidClient) -> None:
    client._access_token = "access-sandbox-test"
    mock_txns = [
        {
            "transaction_id": "txn1",
            "name": "Tesco",
            "amount": 45.20,
            "date": "2026-04-01",
            "category": ["Food and Drink", "Groceries"],
            "merchant_name": "Tesco",
            "pending": False,
        },
    ]
    client.client.transactions_get = MagicMock(
        return_value={"transactions": mock_txns, "total_transactions": 1}
    )
    txns = client.get_transactions()
    assert len(txns) == 1
    assert txns[0]["name"] == "Tesco"
    assert txns[0]["category"] == "Food and Drink"
    assert txns[0]["amount"] == pytest.approx(45.20)


def test_get_spending_summary_skips_pending(client: PlaidClient) -> None:
    client._access_token = "access-sandbox-test"
    mock_txns = [
        {
            "transaction_id": "txn1",
            "name": "Tesco",
            "amount": 50.0,
            "date": "2026-04-01",
            "category": ["Food"],
            "merchant_name": "Tesco",
            "pending": False,
        },
        {
            "transaction_id": "txn2",
            "name": "Pending Shop",
            "amount": 100.0,
            "date": "2026-04-01",
            "category": ["Shopping"],
            "merchant_name": "",
            "pending": True,
        },
    ]
    client.client.transactions_get = MagicMock(
        return_value={"transactions": mock_txns, "total_transactions": 2}
    )
    summary = client.get_spending_summary()
    assert "Food" in summary
    assert "Shopping" not in summary

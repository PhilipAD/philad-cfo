"""Plaid API client — link accounts, fetch transactions, balances, net worth."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.institutions_search_request import InstitutionsSearchRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions

from src.config import ConfigurationError, PlaidConfig


ENVIRONMENTS = {
    "sandbox": plaid.Environment.Sandbox,
    "development": plaid.Environment.Development,
    "production": plaid.Environment.Production,
}


class PlaidClient:
    """Wrapper around Plaid API for account and transaction data.

    Args:
        config: Plaid configuration dataclass.
        token_path: Path to persist/load the access token JSON.
    """

    def __init__(self, config: PlaidConfig, token_path: Optional[Path] = None) -> None:
        if not config.client_id:
            raise ConfigurationError("PLAID_CLIENT_ID is required")
        if not config.secret:
            raise ConfigurationError("PLAID_SECRET is required")

        env = ENVIRONMENTS.get(config.environment, plaid.Environment.Sandbox)
        configuration = plaid.Configuration(
            host=env,
            api_key={
                "clientId": config.client_id,
                "secret": config.secret,
            },
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        self.config = config
        self.token_path = token_path
        self._access_token: Optional[str] = config.access_token

        if not self._access_token and token_path and token_path.exists():
            self._access_token = self._load_token()

    # ------------------------------------------------------------------
    # Link / auth
    # ------------------------------------------------------------------

    def create_link_token(self, user_id: str = "philad-user") -> str:
        """Create a Plaid Link token for initiating OAuth flow.

        Args:
            user_id: Stable identifier for the end user.

        Returns:
            Plaid link_token string.
        """
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
            client_name="philad-cfo",
            products=[Products("transactions"), Products("auth")],
            country_codes=[CountryCode("GB"), CountryCode("US")],
            language="en",
        )
        response = self.client.link_token_create(request)
        return str(response["link_token"])

    def exchange_public_token(self, public_token: str) -> str:
        """Exchange a public token for a persistent access token.

        Args:
            public_token: Public token from Plaid Link callback.

        Returns:
            Access token string.
        """
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        access_token = str(response["access_token"])
        self._access_token = access_token
        if self.token_path:
            self._save_token(access_token)
        return access_token

    def _save_token(self, token: str) -> None:
        if self.token_path is None:
            return
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(
            json.dumps({"access_token": token}), encoding="utf-8"
        )

    def _load_token(self) -> Optional[str]:
        if self.token_path is None or not self.token_path.exists():
            return None
        try:
            data = json.loads(self.token_path.read_text(encoding="utf-8"))
            return str(data.get("access_token", ""))
        except (json.JSONDecodeError, OSError):
            return None

    def _require_token(self) -> str:
        if not self._access_token:
            raise ConfigurationError(
                "No Plaid access token. Run 'philad-cfo link' first."
            )
        return self._access_token

    # ------------------------------------------------------------------
    # Accounts & Balances
    # ------------------------------------------------------------------

    def get_accounts(self) -> list[dict]:
        """Fetch all linked accounts with current balances.

        Returns:
            List of account dicts with keys: account_id, name, type, subtype,
            available, current, currency.
        """
        token = self._require_token()
        request = AccountsGetRequest(access_token=token)
        response = self.client.accounts_get(request)
        accounts = []
        for acct in response["accounts"]:
            balances = acct["balances"]
            accounts.append(
                {
                    "account_id": acct["account_id"],
                    "name": acct["name"],
                    "type": str(acct["type"]),
                    "subtype": str(acct.get("subtype", "")),
                    "available": float(balances.get("available") or 0),
                    "current": float(balances.get("current") or 0),
                    "currency": str(balances.get("iso_currency_code", "GBP")),
                }
            )
        return accounts

    def get_net_worth(self) -> tuple[float, dict[str, float]]:
        """Calculate total net worth from all accounts.

        Returns:
            Tuple of (total_net_worth, breakdown_dict).
            Breakdown maps account name to current balance.
        """
        accounts = self.get_accounts()
        breakdown: dict[str, float] = {}
        total = 0.0
        for acct in accounts:
            value = acct["current"]
            # Credit cards are liabilities — negate
            if acct["type"] in ("credit", "loan"):
                value = -abs(value)
            breakdown[acct["name"]] = value
            total += value
        return total, breakdown

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    def get_transactions(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        count: int = 500,
    ) -> list[dict]:
        """Fetch transactions within a date range.

        Args:
            start_date: Inclusive start date. Defaults to 30 days ago.
            end_date: Inclusive end date. Defaults to today.
            count: Max number of transactions to fetch.

        Returns:
            List of transaction dicts with keys: transaction_id, name, amount,
            date, category, merchant_name, pending.
        """
        token = self._require_token()
        end = end_date or date.today()
        start = start_date or (end - timedelta(days=30))

        request = TransactionsGetRequest(
            access_token=token,
            start_date=start,
            end_date=end,
            options=TransactionsGetRequestOptions(count=count),
        )
        response = self.client.transactions_get(request)
        txns = []
        for t in response["transactions"]:
            categories = t.get("category") or []
            txns.append(
                {
                    "transaction_id": t["transaction_id"],
                    "name": t.get("name", ""),
                    "amount": float(t.get("amount", 0)),
                    "date": str(t.get("date", "")),
                    "category": categories[0] if categories else "Uncategorized",
                    "merchant_name": t.get("merchant_name", ""),
                    "pending": bool(t.get("pending", False)),
                }
            )
        return txns

    def get_spending_summary(
        self, days: int = 30
    ) -> dict[str, float]:
        """Summarise spending by top-level category over the last N days.

        Args:
            days: Number of days to look back.

        Returns:
            Dict mapping category name to total spend (positive = outflow).
        """
        end = date.today()
        start = end - timedelta(days=days)
        transactions = self.get_transactions(start_date=start, end_date=end)
        summary: dict[str, float] = {}
        for t in transactions:
            if t["pending"]:
                continue
            cat = t["category"]
            amount = t["amount"]
            if amount > 0:  # Plaid: positive = debit/spending
                summary[cat] = summary.get(cat, 0.0) + amount
        return dict(sorted(summary.items(), key=lambda x: x[1], reverse=True))

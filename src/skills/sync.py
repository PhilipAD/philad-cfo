"""Sync workflow — Plaid → KB → wiki update orchestration."""

from __future__ import annotations

from typing import Optional

from src.config import AppConfig, ConfigurationError
from src.kb import KnowledgeBase


def sync_plaid(cfg: AppConfig, kb: KnowledgeBase) -> dict:
    """Pull latest data from Plaid and update the KB.

    Args:
        cfg: Application config.
        kb: Knowledge base instance.

    Returns:
        Dict with keys: net_worth, breakdown, transactions, spending_summary.
    """
    from src.plaid_client import PlaidClient

    cache_dir = cfg.cache_dir
    token_path = cache_dir / "plaid_token.json"
    client = PlaidClient(cfg.plaid, token_path=token_path)

    net_worth, breakdown = client.get_net_worth()
    transactions = client.get_transactions()
    spending_summary = client.get_spending_summary()

    kb.write_snapshot(net_worth, breakdown)
    kb.write_transaction_log(transactions)
    kb.append_net_worth_history(net_worth)

    return {
        "net_worth": net_worth,
        "breakdown": breakdown,
        "transactions": transactions,
        "spending_summary": spending_summary,
    }


def sync_ibkr(cfg: AppConfig, kb: KnowledgeBase) -> dict:
    """Pull latest positions from IBKR and update the KB.

    Args:
        cfg: Application config.
        kb: Knowledge base instance.

    Returns:
        Dict with keys: positions, portfolio.
    """
    from src.ibkr_client import IBKRClient

    with IBKRClient(cfg.ibkr) as client:
        positions = client.positions_as_dicts()
        portfolio = client.get_portfolio_summary()

    kb.write_positions(positions)
    return {
        "positions": positions,
        "portfolio": {
            "net_liquidation": portfolio.net_liquidation,
            "total_cash": portfolio.total_cash,
            "unrealized_pnl": portfolio.unrealized_pnl,
        },
    }


def sync_all(cfg: AppConfig, kb: KnowledgeBase) -> dict:
    """Run full sync: Plaid + IBKR.

    Continues if one source fails, collecting errors.

    Args:
        cfg: Application config.
        kb: Knowledge base instance.

    Returns:
        Dict with merged sync results and any errors.
    """
    result: dict = {"errors": []}

    try:
        plaid_data = sync_plaid(cfg, kb)
        result.update(plaid_data)
    except ConfigurationError as e:
        result["errors"].append(f"Plaid: {e}")
    except Exception as e:
        result["errors"].append(f"Plaid unexpected: {e}")

    try:
        ibkr_data = sync_ibkr(cfg, kb)
        result.update(ibkr_data)
    except ConfigurationError as e:
        result["errors"].append(f"IBKR: {e}")
    except Exception as e:
        result["errors"].append(f"IBKR unexpected: {e}")

    return result

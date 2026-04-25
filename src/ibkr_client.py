"""IBKR Gateway client — positions, portfolio, paper trading via ib_insync."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.config import ConfigurationError, IBKRConfig


@dataclass
class Position:
    """Represents a single IBKR portfolio position."""

    symbol: str
    qty: float
    avg_cost: float
    market_price: float
    market_value: float
    pnl: float
    pnl_pct: float


@dataclass
class PortfolioSummary:
    """High-level portfolio summary."""

    account_id: str
    net_liquidation: float
    total_cash: float
    gross_position_value: float
    unrealized_pnl: float
    realized_pnl: float


class IBKRClient:
    """Client for IBKR Gateway via ib_insync.

    Args:
        config: IBKR configuration dataclass.
    """

    def __init__(self, config: IBKRConfig) -> None:
        self.config = config
        self._ib: Optional[object] = None

    def connect(self) -> None:
        """Connect to IBKR Gateway.

        Raises:
            ConfigurationError: If connection fails.
            ImportError: If ib_insync is not installed.
        """
        try:
            from ib_insync import IB  # type: ignore[import]
        except ImportError as exc:
            raise ImportError("ib_insync is required: pip install ib_insync") from exc

        ib = IB()
        try:
            ib.connect(
                self.config.host,
                self.config.port,
                clientId=self.config.client_id,
                readonly=True,
                timeout=10,
            )
        except Exception as exc:
            raise ConfigurationError(
                f"Cannot connect to IBKR Gateway at "
                f"{self.config.host}:{self.config.port} — {exc}"
            ) from exc
        self._ib = ib

    def disconnect(self) -> None:
        """Disconnect from IBKR Gateway."""
        if self._ib is not None:
            self._ib.disconnect()  # type: ignore[union-attr]
            self._ib = None

    def __enter__(self) -> "IBKRClient":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.disconnect()

    def _require_connection(self) -> object:
        if self._ib is None:
            raise ConfigurationError("Not connected to IBKR. Call connect() first.")
        return self._ib

    # ------------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------------

    def get_positions(self) -> list[Position]:
        """Fetch all open positions for the configured account.

        Returns:
            List of Position objects.
        """
        ib = self._require_connection()
        raw_positions = ib.positions(account=self.config.account_id)  # type: ignore[union-attr]
        positions: list[Position] = []
        for pos in raw_positions:
            contract = pos.contract
            symbol = contract.symbol
            qty = float(pos.position)
            avg_cost = float(pos.avgCost)

            # Request market data snapshot
            ticker = ib.reqMktData(contract, "", True, False)  # type: ignore[union-attr]
            ib.sleep(1)  # type: ignore[union-attr]
            market_price = float(ticker.last or ticker.close or avg_cost)
            market_value = qty * market_price
            pnl = market_value - (qty * avg_cost)
            pnl_pct = (pnl / (qty * avg_cost) * 100) if avg_cost else 0.0

            positions.append(
                Position(
                    symbol=symbol,
                    qty=qty,
                    avg_cost=avg_cost,
                    market_price=market_price,
                    market_value=market_value,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                )
            )
        return positions

    def get_portfolio_summary(self) -> PortfolioSummary:
        """Fetch high-level portfolio summary for the configured account.

        Returns:
            PortfolioSummary dataclass.
        """
        ib = self._require_connection()
        account_values = ib.accountValues(account=self.config.account_id)  # type: ignore[union-attr]

        def _get(tag: str) -> float:
            for av in account_values:
                if av.tag == tag and av.currency == "USD":
                    try:
                        return float(av.value)
                    except ValueError:
                        return 0.0
            return 0.0

        return PortfolioSummary(
            account_id=self.config.account_id,
            net_liquidation=_get("NetLiquidation"),
            total_cash=_get("TotalCashValue"),
            gross_position_value=_get("GrossPositionValue"),
            unrealized_pnl=_get("UnrealizedPnL"),
            realized_pnl=_get("RealizedPnL"),
        )

    def positions_as_dicts(self) -> list[dict]:
        """Return positions as plain dicts suitable for KB writing.

        Returns:
            List of dicts with keys: symbol, qty, avg_cost, market_value, pnl.
        """
        return [
            {
                "symbol": p.symbol,
                "qty": p.qty,
                "avg_cost": p.avg_cost,
                "market_value": p.market_value,
                "pnl": p.pnl,
            }
            for p in self.get_positions()
        ]

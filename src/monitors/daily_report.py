"""Daily snapshot report — net worth + spending + IBKR positions."""

from __future__ import annotations

from datetime import date
from typing import Optional

from src.config import AppConfig
from src.kb import KnowledgeBase


def build_daily_report(
    net_worth: float,
    account_breakdown: dict[str, float],
    spending_summary: dict[str, float],
    positions: list[dict],
    signals_md: str = "",
    extra_notes: str = "",
) -> str:
    """Build the daily snapshot report as a markdown string.

    Args:
        net_worth: Current total net worth.
        account_breakdown: Dict mapping account name to balance.
        spending_summary: Dict mapping spending category to total spend.
        positions: List of position dicts from IBKRClient.positions_as_dicts().
        signals_md: Pre-formatted signals markdown table (optional).
        extra_notes: Any additional freetext notes to append.

    Returns:
        Full markdown report string.
    """
    today = date.today().isoformat()
    lines: list[str] = [
        f"# Daily CFO Report — {today}",
        "",
        "## Net Worth",
        "",
        f"**Total: £{net_worth:,.2f}**",
        "",
        "| Account | Balance |",
        "| ------- | ------- |",
    ]
    for name, value in account_breakdown.items():
        lines.append(f"| {name} | £{value:,.2f} |")

    lines += [
        "",
        "## Spending (Last 30 Days)",
        "",
        "| Category | Amount |",
        "| -------- | ------ |",
    ]
    total_spend = 0.0
    for cat, amount in list(spending_summary.items())[:10]:
        lines.append(f"| {cat} | £{amount:,.2f} |")
        total_spend += amount
    lines += [
        f"| **Total** | **£{total_spend:,.2f}** |",
        "",
    ]

    lines += [
        "## Investment Positions",
        "",
        "| Symbol | Qty | Market Value | PnL |",
        "| ------ | --- | ------------ | --- |",
    ]
    for pos in positions:
        lines.append(
            f"| {pos.get('symbol')} | {pos.get('qty')} | "
            f"${float(pos.get('market_value', 0)):,.2f} | "
            f"${float(pos.get('pnl', 0)):+,.2f} |"
        )

    if signals_md:
        lines += ["", "## Investment Signals", "", signals_md]

    if extra_notes:
        lines += ["", "## Notes", "", extra_notes]

    lines.append("")
    return "\n".join(lines)


def run_daily_report(
    cfg: AppConfig,
    kb: KnowledgeBase,
    net_worth: float = 0.0,
    account_breakdown: Optional[dict[str, float]] = None,
    spending_summary: Optional[dict[str, float]] = None,
    positions: Optional[list[dict]] = None,
    signals_md: str = "",
) -> tuple[str, str]:
    """Generate and persist the daily report to the KB.

    Args:
        cfg: Application config.
        kb: Knowledge base instance.
        net_worth: Current net worth figure.
        account_breakdown: Account balance breakdown.
        spending_summary: Spending by category.
        positions: IBKR positions list.
        signals_md: Pre-formatted signals table.

    Returns:
        Tuple of (report_markdown, kb_path_str).
    """
    today = date.today().isoformat()
    report_md = build_daily_report(
        net_worth=net_worth,
        account_breakdown=account_breakdown or {},
        spending_summary=spending_summary or {},
        positions=positions or [],
        signals_md=signals_md,
    )
    kb_path = kb.write(f"snapshots/daily_{today}.md", report_md)
    # Also update the canonical snapshot
    kb.write("snapshot.md", report_md)
    # Record net worth history
    if net_worth:
        kb.append_net_worth_history(net_worth)
    return report_md, str(kb_path)

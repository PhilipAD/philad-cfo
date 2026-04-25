"""Markdown report generator — writes formatted financial reports to files."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional


def mortgage_report(
    target_price: float,
    current_deposit: float,
    monthly_saving: float,
    target_ltv: float = 0.80,
    interest_rate: float = 0.045,
    term_years: int = 25,
) -> str:
    """Generate a mortgage readiness report.

    Args:
        target_price: Target property price.
        current_deposit: Current deposit amount saved.
        monthly_saving: Monthly savings contribution.
        target_ltv: Target loan-to-value ratio (default 80%).
        interest_rate: Annual interest rate (decimal).
        term_years: Mortgage term in years.

    Returns:
        Markdown report string.
    """
    today = date.today().isoformat()
    required_deposit = target_price * (1 - target_ltv)
    deposit_gap = max(0.0, required_deposit - current_deposit)
    months_to_goal = int(deposit_gap / monthly_saving) if monthly_saving > 0 else 9999
    current_ltv = 1 - (current_deposit / target_price) if target_price > 0 else 1.0

    loan_amount = target_price * target_ltv
    monthly_rate = interest_rate / 12
    n_payments = term_years * 12
    if monthly_rate > 0:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** n_payments) / (
            (1 + monthly_rate) ** n_payments - 1
        )
    else:
        monthly_payment = loan_amount / n_payments

    readiness_score = min(100, int((current_deposit / required_deposit) * 100))

    lines = [
        f"# Mortgage Readiness Report — {today}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"| ------ | ----- |",
        f"| Target Price | £{target_price:,.0f} |",
        f"| Required Deposit ({int((1-target_ltv)*100)}%) | £{required_deposit:,.0f} |",
        f"| Current Deposit | £{current_deposit:,.0f} |",
        f"| Deposit Gap | £{deposit_gap:,.0f} |",
        f"| Current LTV | {current_ltv:.1%} |",
        f"| Monthly Saving | £{monthly_saving:,.0f} |",
        f"| Months to Goal | {months_to_goal} |",
        f"| Readiness Score | {readiness_score}/100 |",
        "",
        "## Mortgage Estimate",
        "",
        f"| Metric | Value |",
        f"| ------ | ----- |",
        f"| Loan Amount | £{loan_amount:,.0f} |",
        f"| Interest Rate | {interest_rate:.2%} |",
        f"| Term | {term_years} years |",
        f"| Est. Monthly Payment | £{monthly_payment:,.2f} |",
        "",
    ]
    return "\n".join(lines)


def spending_analysis_report(
    spending_summary: dict[str, float],
    monthly_net_income: float = 0.0,
    days: int = 30,
) -> str:
    """Generate a spending analysis report.

    Args:
        spending_summary: Dict mapping category to total spend.
        monthly_net_income: Monthly take-home pay (for savings rate calculation).
        days: Number of days covered by the spending data.

    Returns:
        Markdown report string.
    """
    today = date.today().isoformat()
    total = sum(spending_summary.values())
    savings_rate = (
        ((monthly_net_income - total) / monthly_net_income * 100)
        if monthly_net_income > 0
        else 0.0
    )

    lines = [
        f"# Spending Analysis — {today}",
        f"_Last {days} days_",
        "",
        f"**Total Spend:** £{total:,.2f}",
        f"**Savings Rate:** {savings_rate:.1f}%",
        "",
        "## By Category",
        "",
        "| Category | Amount | % of Total |",
        "| -------- | ------ | ---------- |",
    ]
    for cat, amount in sorted(spending_summary.items(), key=lambda x: x[1], reverse=True):
        pct = (amount / total * 100) if total > 0 else 0.0
        lines.append(f"| {cat} | £{amount:,.2f} | {pct:.1f}% |")

    lines.append("")
    return "\n".join(lines)


def net_worth_report(
    net_worth: float,
    breakdown: dict[str, float],
    history: Optional[list[tuple[str, float]]] = None,
) -> str:
    """Generate a net worth snapshot report.

    Args:
        net_worth: Total net worth.
        breakdown: Dict mapping account name to balance.
        history: Optional list of (date_str, net_worth) tuples for trend.

    Returns:
        Markdown report string.
    """
    today = date.today().isoformat()
    lines = [
        f"# Net Worth Report — {today}",
        "",
        f"**Total Net Worth: £{net_worth:,.2f}**",
        "",
        "## Account Breakdown",
        "",
        "| Account | Balance |",
        "| ------- | ------- |",
    ]
    assets = {k: v for k, v in breakdown.items() if v >= 0}
    liabilities = {k: v for k, v in breakdown.items() if v < 0}
    for name, val in sorted(assets.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {name} | £{val:,.2f} |")
    for name, val in sorted(liabilities.items(), key=lambda x: x[1]):
        lines.append(f"| {name} (liability) | £{val:,.2f} |")

    if history:
        lines += ["", "## History", "", "| Date | Net Worth |", "| ---- | --------- |"]
        for dt, nw in history[-10:]:
            lines.append(f"| {dt} | £{nw:,.2f} |")

    lines.append("")
    return "\n".join(lines)


def write_report(path: Path, content: str) -> Path:
    """Write a markdown report to a file.

    Args:
        path: Destination path.
        content: Markdown content.

    Returns:
        Path to the written file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path

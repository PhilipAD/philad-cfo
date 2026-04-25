"""Knowledge base — read/write markdown files under ~/.philad-cfo/kb/."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional


class KnowledgeBase:
    """Filesystem-backed knowledge base stored as markdown files.

    Args:
        root: Root directory for the knowledge base. Defaults to ~/.philad-cfo/kb/.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Low-level read / write
    # ------------------------------------------------------------------

    def read(self, relative_path: str) -> Optional[str]:
        """Read a KB file, returning None if it doesn't exist.

        Args:
            relative_path: Path relative to KB root (e.g. 'snapshot.md').

        Returns:
            File contents or None.
        """
        p = self.root / relative_path
        if not p.exists():
            return None
        return p.read_text(encoding="utf-8")

    def write(self, relative_path: str, content: str) -> Path:
        """Write content to a KB file, creating parent dirs as needed.

        Args:
            relative_path: Path relative to KB root.
            content: Markdown content to write.

        Returns:
            Absolute path of the written file.
        """
        p = self.root / relative_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def append(self, relative_path: str, content: str) -> Path:
        """Append content to a KB file.

        Args:
            relative_path: Path relative to KB root.
            content: Content to append.

        Returns:
            Absolute path of the file.
        """
        p = self.root / relative_path
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(content)
        return p

    def list_files(self, subdir: str = "") -> list[Path]:
        """List all markdown files under a subdirectory.

        Args:
            subdir: Subdirectory relative to KB root. Empty string = root.

        Returns:
            List of absolute paths sorted alphabetically.
        """
        base = self.root / subdir if subdir else self.root
        if not base.exists():
            return []
        return sorted(base.glob("**/*.md"))

    # ------------------------------------------------------------------
    # Domain-specific helpers
    # ------------------------------------------------------------------

    def write_snapshot(self, net_worth: float, breakdown: dict[str, float]) -> Path:
        """Overwrite the daily snapshot with current net worth data.

        Args:
            net_worth: Total net worth figure.
            breakdown: Dict mapping account/category name to value.

        Returns:
            Path to snapshot.md.
        """
        today = date.today().isoformat()
        lines = [
            f"# Net Worth Snapshot — {today}",
            "",
            f"**Total Net Worth:** £{net_worth:,.2f}",
            "",
            "## Breakdown",
            "",
            "| Account | Value |",
            "| ------- | ----- |",
        ]
        for account, value in breakdown.items():
            lines.append(f"| {account} | £{value:,.2f} |")
        lines.append("")
        return self.write("snapshot.md", "\n".join(lines))

    def write_transaction_log(
        self, transactions: list[dict], log_date: Optional[date] = None
    ) -> Path:
        """Write daily transaction log.

        Args:
            transactions: List of transaction dicts with keys: name, amount, category, date.
            log_date: Date for the log file name. Defaults to today.

        Returns:
            Path to the transaction log file.
        """
        d = (log_date or date.today()).isoformat()
        lines = [f"# Transactions — {d}", ""]
        if not transactions:
            lines.append("_No transactions._")
        else:
            lines += [
                "| Date | Name | Amount | Category |",
                "| ---- | ---- | ------ | -------- |",
            ]
            for t in transactions:
                lines.append(
                    f"| {t.get('date', d)} | {t.get('name', '?')} "
                    f"| £{float(t.get('amount', 0)):,.2f} | {t.get('category', '?')} |"
                )
        lines.append("")
        return self.write(f"transactions/{d}.md", "\n".join(lines))

    def append_net_worth_history(self, net_worth: float) -> Path:
        """Append a net worth data point to the history log.

        Args:
            net_worth: Net worth figure to record.

        Returns:
            Path to history.md.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        line = f"| {now} | £{net_worth:,.2f} |\n"
        p = self.root / "net_worth" / "history.md"
        if not p.exists():
            header = "# Net Worth History\n\n| Date | Net Worth |\n| ---- | --------- |\n"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(header + line, encoding="utf-8")
        else:
            with open(p, "a", encoding="utf-8") as fh:
                fh.write(line)
        return p

    def write_positions(self, positions: list[dict]) -> Path:
        """Write current IBKR positions to KB.

        Args:
            positions: List of position dicts with keys: symbol, qty, avg_cost, market_value, pnl.

        Returns:
            Path to positions.md.
        """
        today = date.today().isoformat()
        lines = [
            f"# Investment Positions — {today}",
            "",
            "| Symbol | Qty | Avg Cost | Market Value | PnL |",
            "| ------ | --- | -------- | ------------ | --- |",
        ]
        for p in positions:
            lines.append(
                f"| {p.get('symbol')} | {p.get('qty')} | "
                f"${float(p.get('avg_cost', 0)):,.2f} | "
                f"${float(p.get('market_value', 0)):,.2f} | "
                f"${float(p.get('pnl', 0)):+,.2f} |"
            )
        lines.append("")
        return self.write("investments/positions.md", "\n".join(lines))

    def write_mortgage_plan(self, data: dict) -> Path:
        """Write mortgage readiness plan to KB.

        Args:
            data: Dict with keys: target_price, deposit, ltv, monthly_saving,
                  months_to_goal, readiness_score, notes.

        Returns:
            Path to mortgage/plan.md.
        """
        today = date.today().isoformat()
        lines = [
            f"# Mortgage Plan — Updated {today}",
            "",
            f"- **Target Price:** £{float(data.get('target_price', 0)):,.0f}",
            f"- **Current Deposit:** £{float(data.get('deposit', 0)):,.0f}",
            f"- **LTV:** {float(data.get('ltv', 0)) * 100:.1f}%",
            f"- **Monthly Saving:** £{float(data.get('monthly_saving', 0)):,.0f}",
            f"- **Months to Goal:** {data.get('months_to_goal', '?')}",
            f"- **Readiness Score:** {data.get('readiness_score', 0)}/100",
            "",
            "## Notes",
            "",
            data.get("notes", "_None._"),
            "",
        ]
        return self.write("mortgage/plan.md", "\n".join(lines))

    def write_goals(self, goals: list[dict]) -> Path:
        """Write savings goals tracking to KB.

        Args:
            goals: List of goal dicts with keys: name, target, current, monthly, eta.

        Returns:
            Path to goals/tracking.md.
        """
        today = date.today().isoformat()
        lines = [
            f"# Goals Tracking — {today}",
            "",
            "| Goal | Target | Current | Monthly | ETA |",
            "| ---- | ------ | ------- | ------- | --- |",
        ]
        for g in goals:
            lines.append(
                f"| {g.get('name')} | £{float(g.get('target', 0)):,.0f} | "
                f"£{float(g.get('current', 0)):,.0f} | "
                f"£{float(g.get('monthly', 0)):,.0f} | {g.get('eta', '?')} |"
            )
        lines.append("")
        return self.write("goals/tracking.md", "\n".join(lines))

    def read_json_cache(self, key: str) -> Optional[dict]:
        """Read a JSON cache file from the cache directory.

        Args:
            key: Cache key (used as filename without extension).

        Returns:
            Parsed JSON dict or None.
        """
        cache_dir = self.root.parent / "cache"
        p = cache_dir / f"{key}.json"
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def write_json_cache(self, key: str, data: dict) -> Path:
        """Write a JSON cache file.

        Args:
            key: Cache key (used as filename without extension).
            data: Data to serialise.

        Returns:
            Path to the cache file.
        """
        cache_dir = self.root.parent / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        p = cache_dir / f"{key}.json"
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return p

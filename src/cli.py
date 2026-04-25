"""Main CLI entry point — argparse interface for all philad-cfo commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.config import CFO_HOME, AppConfig, ConfigurationError, ensure_dirs, load_config
from src.kb import KnowledgeBase


def _load_cfg_and_kb() -> tuple[AppConfig, KnowledgeBase]:
    """Load config and initialise KB, printing helpful error on failure."""
    try:
        cfg = load_config()
    except FileNotFoundError:
        print("Config not found. Run 'philad-cfo init' first.", file=sys.stderr)
        sys.exit(1)
    ensure_dirs(cfg)
    kb = KnowledgeBase(cfg.kb_root)
    return cfg, kb


# ------------------------------------------------------------------
# Command handlers
# ------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> None:
    """Guided setup wizard — create config directory and example config."""
    cfo_home = CFO_HOME
    cfo_home.mkdir(parents=True, exist_ok=True)
    config_path = cfo_home / "config.yaml"

    if config_path.exists() and not args.force:
        print(f"Config already exists at {config_path}. Use --force to overwrite.")
        return

    example = Path(__file__).parent.parent / "config" / "config.yaml.example"
    if example.exists():
        import shutil
        shutil.copy(example, config_path)
        print(f"Created config at {config_path}")
        print("Edit it to add your API keys, then run 'philad-cfo sync'.")
    else:
        print(f"Creating minimal config at {config_path}")
        config_path.write_text("# philad-cfo config\nplaid:\n  environment: sandbox\n")

    kb_root = cfo_home / "kb"
    kb_root.mkdir(parents=True, exist_ok=True)
    (cfo_home / "cache").mkdir(parents=True, exist_ok=True)
    print("Directories created. Run 'philad-cfo link' to connect Plaid accounts.")


def cmd_link(args: argparse.Namespace) -> None:
    """Get Plaid Link URL for connecting bank accounts."""
    cfg, _ = _load_cfg_and_kb()
    try:
        from src.plaid_client import PlaidClient
        token_path = cfg.cache_dir / "plaid_token.json"
        client = PlaidClient(cfg.plaid, token_path=token_path)
        link_token = client.create_link_token()
        url = f"https://cdn.plaid.com/link/v2/stable/link.html?token={link_token}"
        print(f"Open this URL to link your accounts:\n\n  {url}\n")
        print("After linking, exchange the public token with:")
        print("  philad-cfo link --exchange <public_token>")
    except ConfigurationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_sync(args: argparse.Namespace) -> None:
    """Sync data from Plaid and/or IBKR."""
    cfg, kb = _load_cfg_and_kb()
    from src.skills.sync import sync_all, sync_ibkr, sync_plaid

    target = getattr(args, "target", "all")

    if target == "plaid":
        try:
            data = sync_plaid(cfg, kb)
            print(f"Plaid sync complete. Net worth: £{data['net_worth']:,.2f}")
        except ConfigurationError as e:
            print(f"Plaid error: {e}", file=sys.stderr)
            sys.exit(1)
    elif target == "ibkr":
        try:
            data = sync_ibkr(cfg, kb)
            print(f"IBKR sync complete. {len(data['positions'])} positions updated.")
        except ConfigurationError as e:
            print(f"IBKR error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        result = sync_all(cfg, kb)
        if result.get("errors"):
            for err in result["errors"]:
                print(f"Warning: {err}", file=sys.stderr)
        nw = result.get("net_worth", 0)
        pos = result.get("positions", [])
        print(f"Full sync complete. Net worth: £{nw:,.2f} | Positions: {len(pos)}")


def cmd_net_worth(args: argparse.Namespace) -> None:
    """Print current net worth from KB or live Plaid data."""
    cfg, kb = _load_cfg_and_kb()
    snapshot = kb.read("snapshot.md")
    if snapshot and not getattr(args, "live", False):
        print(snapshot)
        return
    try:
        from src.plaid_client import PlaidClient
        token_path = cfg.cache_dir / "plaid_token.json"
        client = PlaidClient(cfg.plaid, token_path=token_path)
        net_worth, breakdown = client.get_net_worth()
        from src.output.markdown_report import net_worth_report
        print(net_worth_report(net_worth, breakdown))
    except ConfigurationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_analyze(args: argparse.Namespace) -> None:
    """Run spending or savings analysis."""
    cfg, kb = _load_cfg_and_kb()
    mode = args.mode

    if mode == "spending":
        try:
            from src.plaid_client import PlaidClient
            token_path = cfg.cache_dir / "plaid_token.json"
            client = PlaidClient(cfg.plaid, token_path=token_path)
            summary = client.get_spending_summary(days=30)
            from src.output.markdown_report import spending_analysis_report
            report = spending_analysis_report(summary, cfg.income.monthly_net)
            print(report)
            kb.write("spending_analysis.md", report)
        except ConfigurationError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif mode == "savings":
        try:
            from src.plaid_client import PlaidClient
            token_path = cfg.cache_dir / "plaid_token.json"
            client = PlaidClient(cfg.plaid, token_path=token_path)
            summary = client.get_spending_summary(days=30)
            total_spend = sum(summary.values())
            monthly_net = cfg.income.monthly_net
            savings = monthly_net - total_spend
            rate = (savings / monthly_net * 100) if monthly_net > 0 else 0
            print(f"Monthly Net Income:  £{monthly_net:,.2f}")
            print(f"Total Spend (30d):   £{total_spend:,.2f}")
            print(f"Savings:             £{savings:,.2f}")
            print(f"Savings Rate:        {rate:.1f}%")
        except ConfigurationError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown mode: {mode}. Use 'spending' or 'savings'.", file=sys.stderr)
        sys.exit(1)


def cmd_mortgage(args: argparse.Namespace) -> None:
    """Mortgage planning commands."""
    cfg, kb = _load_cfg_and_kb()
    mode = args.mode

    if mode == "status":
        plan = kb.read("mortgage/plan.md")
        if plan:
            print(plan)
        else:
            print("No mortgage plan found. Run 'philad-cfo mortgage calc' first.")

    elif mode == "calc":
        from src.output.markdown_report import mortgage_report
        m = cfg.mortgage
        report = mortgage_report(
            target_price=m.target_price,
            current_deposit=m.current_deposit,
            monthly_saving=m.monthly_saving,
            target_ltv=m.target_ltv,
            interest_rate=m.interest_rate,
            term_years=m.term_years,
        )
        print(report)
        kb.write_mortgage_plan(
            {
                "target_price": m.target_price,
                "deposit": m.current_deposit,
                "ltv": m.target_ltv,
                "monthly_saving": m.monthly_saving,
                "months_to_goal": int(
                    max(0, m.target_price * (1 - m.target_ltv) - m.current_deposit)
                    / max(1, m.monthly_saving)
                ),
                "readiness_score": min(
                    100,
                    int(
                        m.current_deposit
                        / max(1, m.target_price * (1 - m.target_ltv))
                        * 100
                    ),
                ),
            }
        )
    else:
        print(f"Unknown mode: {mode}. Use 'status' or 'calc'.", file=sys.stderr)
        sys.exit(1)


def cmd_positions(args: argparse.Namespace) -> None:
    """Print current IBKR positions."""
    cfg, kb = _load_cfg_and_kb()
    try:
        from src.ibkr_client import IBKRClient
        with IBKRClient(cfg.ibkr) as client:
            positions = client.positions_as_dicts()
        if not positions:
            print("No open positions.")
            return
        print(f"{'Symbol':<8} {'Qty':>6} {'Avg Cost':>10} {'Mkt Value':>12} {'PnL':>10}")
        print("-" * 50)
        for p in positions:
            print(
                f"{p['symbol']:<8} {p['qty']:>6} "
                f"${p['avg_cost']:>9,.2f} "
                f"${p['market_value']:>11,.2f} "
                f"${p['pnl']:>+9,.2f}"
            )
    except ConfigurationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_monitor(args: argparse.Namespace) -> None:
    """Run mean-reversion monitor over watchlist."""
    cfg, kb = _load_cfg_and_kb()
    from src.monitors.hourly import format_signals_table, run_hourly_monitor

    print("Running mean-reversion monitor...")
    signals = run_hourly_monitor(cfg)
    table = format_signals_table(signals)
    print(table)

    # Save to KB
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    kb.write("investments/signals_latest.md", f"# Signals — {now}\n\n{table}")

    if getattr(args, "discord", False):
        try:
            from src.output.discord import DiscordReporter
            reporter = DiscordReporter(cfg.discord)
            reporter.send(f"**Investment Signals — {now}**\n```\n{table}\n```")
            print("Sent to Discord.")
        except ConfigurationError as e:
            print(f"Discord error: {e}", file=sys.stderr)


def cmd_research(args: argparse.Namespace) -> None:
    """Run a Perplexity research query."""
    cfg, kb = _load_cfg_and_kb()
    query = " ".join(args.query)
    if not query:
        print("Usage: philad-cfo research <query>", file=sys.stderr)
        sys.exit(1)
    try:
        from src.perplexity_client import PerplexityClient
        client = PerplexityClient(cfg.perplexity)
        print(f"Researching: {query}\n")
        result = client.market_intelligence(query)
        print(result)
        # Save to KB
        from datetime import date
        today = date.today().isoformat()
        kb.append(f"research/{today}.md", f"\n## Query: {query}\n\n{result}\n")
    except ConfigurationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_daily_report(args: argparse.Namespace) -> None:
    """Generate and optionally send the daily CFO report."""
    cfg, kb = _load_cfg_and_kb()

    # Gather data
    net_worth = 0.0
    breakdown: dict[str, float] = {}
    spending: dict[str, float] = {}
    positions: list[dict] = []
    signals_md = ""

    try:
        from src.plaid_client import PlaidClient
        token_path = cfg.cache_dir / "plaid_token.json"
        plaid = PlaidClient(cfg.plaid, token_path=token_path)
        net_worth, breakdown = plaid.get_net_worth()
        spending = plaid.get_spending_summary()
    except Exception as e:
        print(f"Warning: Plaid unavailable — {e}", file=sys.stderr)

    try:
        from src.ibkr_client import IBKRClient
        with IBKRClient(cfg.ibkr) as ibkr:
            positions = ibkr.positions_as_dicts()
    except Exception as e:
        print(f"Warning: IBKR unavailable — {e}", file=sys.stderr)

    try:
        from src.monitors.hourly import format_signals_table, run_hourly_monitor
        signals = run_hourly_monitor(cfg)
        signals_md = format_signals_table(signals)
    except Exception:
        pass

    from src.monitors.daily_report import run_daily_report
    report_md, kb_path = run_daily_report(
        cfg=cfg,
        kb=kb,
        net_worth=net_worth,
        account_breakdown=breakdown,
        spending_summary=spending,
        positions=positions,
        signals_md=signals_md,
    )
    print(report_md)
    print(f"\nSaved to {kb_path}")

    if not getattr(args, "no_discord", False):
        try:
            from src.output.discord import DiscordReporter
            reporter = DiscordReporter(cfg.discord)
            reporter.send_report(report_md)
            print("Sent to Discord.")
        except ConfigurationError as e:
            print(f"Discord error: {e}", file=sys.stderr)


def cmd_hourly_monitor(args: argparse.Namespace) -> None:
    """Run hourly monitor and send signals to Discord."""
    args.discord = True
    cmd_monitor(args)


# ------------------------------------------------------------------
# Argument parser
# ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="philad-cfo",
        description="AI Personal CFO — financial intelligence from Plaid + IBKR + Perplexity",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # init
    p_init = sub.add_parser("init", help="Guided setup wizard")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing config")
    p_init.set_defaults(func=cmd_init)

    # link
    p_link = sub.add_parser("link", help="Get Plaid Link URL or exchange token")
    p_link.add_argument("--exchange", metavar="PUBLIC_TOKEN", help="Exchange a public token")
    p_link.set_defaults(func=cmd_link)

    # sync
    p_sync = sub.add_parser("sync", help="Sync data from Plaid / IBKR")
    p_sync.add_argument("target", nargs="?", default="all", choices=["all", "plaid", "ibkr"])
    p_sync.set_defaults(func=cmd_sync)

    # net-worth
    p_nw = sub.add_parser("net-worth", help="Print current net worth")
    p_nw.add_argument("--live", action="store_true", help="Fetch live data from Plaid")
    p_nw.set_defaults(func=cmd_net_worth)

    # analyze
    p_analyze = sub.add_parser("analyze", help="Spending or savings analysis")
    p_analyze.add_argument(
        "mode", choices=["spending", "savings"], help="Analysis type"
    )
    p_analyze.set_defaults(func=cmd_analyze)

    # mortgage
    p_mort = sub.add_parser("mortgage", help="Mortgage planning")
    p_mort.add_argument("mode", choices=["status", "calc"], help="Mortgage command")
    p_mort.set_defaults(func=cmd_mortgage)

    # positions
    p_pos = sub.add_parser("positions", help="Print IBKR positions")
    p_pos.set_defaults(func=cmd_positions)

    # monitor
    p_mon = sub.add_parser("monitor", help="Run mean-reversion monitor")
    p_mon.add_argument("--discord", action="store_true", help="Send signals to Discord")
    p_mon.set_defaults(func=cmd_monitor)

    # research
    p_res = sub.add_parser("research", help="Perplexity research query")
    p_res.add_argument("query", nargs="+", help="Research question")
    p_res.set_defaults(func=cmd_research)

    # daily-report
    p_dr = sub.add_parser("daily-report", help="Generate and send daily CFO report")
    p_dr.add_argument("--no-discord", action="store_true", help="Skip Discord send")
    p_dr.set_defaults(func=cmd_daily_report)

    # hourly-monitor
    p_hm = sub.add_parser("hourly-monitor", help="Run hourly watchlist monitor + Discord")
    p_hm.set_defaults(func=cmd_hourly_monitor)

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

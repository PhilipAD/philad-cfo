"""Config loader — reads ~/.philad-cfo/config.yaml into typed dataclasses."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


CFO_HOME = Path(os.environ.get("CFO_HOME", Path.home() / ".philad-cfo"))
CONFIG_PATH = CFO_HOME / "config.yaml"


@dataclass
class PlaidConfig:
    client_id: str
    secret: str
    environment: str = "sandbox"
    access_token: Optional[str] = None


@dataclass
class IBKRConfig:
    host: str = "127.0.0.1"
    port: int = 4002
    client_id: int = 10
    account_id: str = "phidso079"
    paper_trading: bool = True


@dataclass
class PerplexityConfig:
    api_key: str = ""
    model: str = "pplx-2"


@dataclass
class DiscordConfig:
    webhook_url: str = ""
    channel_id: str = "1489761694908678354"


@dataclass
class MortgageConfig:
    target_price: float = 0.0
    current_deposit: float = 0.0
    monthly_saving: float = 0.0
    target_ltv: float = 0.80
    interest_rate: float = 0.045
    term_years: int = 25


@dataclass
class WatchlistItem:
    symbol: str
    risk: str  # LOW, MED, HIGH
    auto_execute: bool = False


@dataclass
class InvestmentConfig:
    watchlist: list[WatchlistItem] = field(default_factory=list)
    rsi_buy_threshold: float = 30.0
    rsi_sell_threshold: float = 70.0
    paper_only: bool = True


@dataclass
class IncomeConfig:
    monthly_net: float = 0.0
    annual_gross: float = 0.0
    currency: str = "GBP"


@dataclass
class AppConfig:
    plaid: PlaidConfig
    ibkr: IBKRConfig
    perplexity: PerplexityConfig
    discord: DiscordConfig
    mortgage: MortgageConfig
    investment: InvestmentConfig
    income: IncomeConfig
    kb_root: Path = field(default_factory=lambda: CFO_HOME / "kb")
    cache_dir: Path = field(default_factory=lambda: CFO_HOME / "cache")


def _load_yaml(path: Path) -> dict:
    """Load YAML file, returning empty dict if not found."""
    if not path.exists():
        return {}
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


def _require(cfg: dict, *keys: str) -> str:
    """Walk nested dict keys, raising ConfigurationError if missing/empty."""
    node: object = cfg
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            raise ConfigurationError(f"Missing required config: {'.'.join(keys)}")
        node = node[k]
    if not node:
        raise ConfigurationError(f"Empty required config: {'.'.join(keys)}")
    return str(node)


def load_config(path: Optional[Path] = None) -> AppConfig:
    """Load and validate configuration from YAML file.

    Args:
        path: Override path to config.yaml. Defaults to ~/.philad-cfo/config.yaml.

    Returns:
        Fully populated AppConfig.

    Raises:
        ConfigurationError: If required fields are missing.
    """
    cfg_path = path or CONFIG_PATH
    raw = _load_yaml(cfg_path)

    # Load .env overrides
    _apply_env_overrides(raw)

    plaid_raw = raw.get("plaid", {})
    plaid = PlaidConfig(
        client_id=plaid_raw.get("client_id", os.environ.get("PLAID_CLIENT_ID", "")),
        secret=plaid_raw.get("secret", os.environ.get("PLAID_SECRET", "")),
        environment=plaid_raw.get("environment", "sandbox"),
        access_token=plaid_raw.get("access_token"),
    )

    ibkr_raw = raw.get("ibkr", {})
    ibkr = IBKRConfig(
        host=ibkr_raw.get("host", "127.0.0.1"),
        port=int(ibkr_raw.get("port", 4002)),
        client_id=int(ibkr_raw.get("client_id", 10)),
        account_id=ibkr_raw.get("account_id", "phidso079"),
        paper_trading=ibkr_raw.get("paper_trading", True),
    )

    perp_raw = raw.get("perplexity", {})
    perplexity = PerplexityConfig(
        api_key=perp_raw.get("api_key", os.environ.get("PERPLEXITY_API_KEY", "")),
        model=perp_raw.get("model", "pplx-2"),
    )

    disc_raw = raw.get("discord", {})
    discord = DiscordConfig(
        webhook_url=disc_raw.get(
            "webhook_url", os.environ.get("DISCORD_WEBHOOK_URL", "")
        ),
        channel_id=disc_raw.get("channel_id", "1489761694908678354"),
    )

    mort_raw = raw.get("mortgage", {})
    mortgage = MortgageConfig(
        target_price=float(mort_raw.get("target_price", 0.0)),
        current_deposit=float(mort_raw.get("current_deposit", 0.0)),
        monthly_saving=float(mort_raw.get("monthly_saving", 0.0)),
        target_ltv=float(mort_raw.get("target_ltv", 0.80)),
        interest_rate=float(mort_raw.get("interest_rate", 0.045)),
        term_years=int(mort_raw.get("term_years", 25)),
    )

    inv_raw = raw.get("investment", {})
    watchlist_raw = inv_raw.get("watchlist", _default_watchlist())
    watchlist = [
        WatchlistItem(
            symbol=w["symbol"],
            risk=w.get("risk", "MED"),
            auto_execute=w.get("auto_execute", False),
        )
        for w in watchlist_raw
    ]
    investment = InvestmentConfig(
        watchlist=watchlist,
        rsi_buy_threshold=float(inv_raw.get("rsi_buy_threshold", 30.0)),
        rsi_sell_threshold=float(inv_raw.get("rsi_sell_threshold", 70.0)),
        paper_only=inv_raw.get("paper_only", True),
    )

    inc_raw = raw.get("income", {})
    income = IncomeConfig(
        monthly_net=float(inc_raw.get("monthly_net", 0.0)),
        annual_gross=float(inc_raw.get("annual_gross", 0.0)),
        currency=inc_raw.get("currency", "GBP"),
    )

    kb_root = Path(raw.get("kb_root", CFO_HOME / "kb"))
    cache_dir = Path(raw.get("cache_dir", CFO_HOME / "cache"))

    return AppConfig(
        plaid=plaid,
        ibkr=ibkr,
        perplexity=perplexity,
        discord=discord,
        mortgage=mortgage,
        investment=investment,
        income=income,
        kb_root=kb_root,
        cache_dir=cache_dir,
    )


def _apply_env_overrides(raw: dict) -> None:
    """Inject environment variable overrides into raw config dict."""
    env_map = {
        ("plaid", "client_id"): "PLAID_CLIENT_ID",
        ("plaid", "secret"): "PLAID_SECRET",
        ("perplexity", "api_key"): "PERPLEXITY_API_KEY",
        ("discord", "webhook_url"): "DISCORD_WEBHOOK_URL",
    }
    for (section, key), env_var in env_map.items():
        val = os.environ.get(env_var)
        if val:
            raw.setdefault(section, {})[key] = val


def _default_watchlist() -> list[dict]:
    return [
        {"symbol": "IONQ", "risk": "MED", "auto_execute": True},
        {"symbol": "DWAVE", "risk": "HIGH", "auto_execute": False},
        {"symbol": "SNDK", "risk": "LOW", "auto_execute": True},
        {"symbol": "VERT", "risk": "LOW", "auto_execute": True},
    ]


def ensure_dirs(cfg: AppConfig) -> None:
    """Create KB and cache directories if they don't exist.

    Args:
        cfg: Loaded application config.
    """
    for subdir in [
        cfg.kb_root,
        cfg.kb_root / "transactions",
        cfg.kb_root / "net_worth",
        cfg.kb_root / "mortgage",
        cfg.kb_root / "investments",
        cfg.kb_root / "goals",
        cfg.cache_dir,
    ]:
        subdir.mkdir(parents=True, exist_ok=True)

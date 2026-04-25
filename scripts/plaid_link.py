#!/usr/bin/env python3
"""One-time Plaid Link initiation — prints the OAuth URL and handles token exchange."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src package is importable when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import CFO_HOME, ConfigurationError, load_config
from src.plaid_client import PlaidClient


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plaid Link helper — get an OAuth URL or exchange a public token"
    )
    parser.add_argument(
        "--exchange",
        metavar="PUBLIC_TOKEN",
        help="Exchange a public_token from Plaid Link for a persistent access_token",
    )
    parser.add_argument(
        "--user-id",
        default="philad-user",
        help="Stable user identifier for Plaid (default: philad-user)",
    )
    args = parser.parse_args()

    try:
        cfg = load_config()
    except ConfigurationError as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)

    token_path = cfg.cache_dir / "plaid_token.json"
    cfg.cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        client = PlaidClient(cfg.plaid, token_path=token_path)

        if args.exchange:
            access_token = client.exchange_public_token(args.exchange)
            print(f"Access token saved to {token_path}")
            print(f"Token: {access_token[:20]}...  (stored, not shown in full)")
            print("\nNext step: run 'philad-cfo sync plaid' to pull your accounts.")
        else:
            link_token = client.create_link_token(user_id=args.user_id)
            url = f"https://cdn.plaid.com/link/v2/stable/link.html?token={link_token}"
            print("Open this URL in a browser to link your bank accounts:\n")
            print(f"  {url}\n")
            print("After completing the flow, you'll receive a public_token.")
            print("Exchange it with:\n")
            print(f"  python scripts/plaid_link.py --exchange <public_token>")

    except ConfigurationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

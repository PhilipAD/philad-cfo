#!/usr/bin/env bash
# Guided setup wizard for philad-cfo
set -euo pipefail

CFO_HOME="${CFO_HOME:-$HOME/.philad-cfo}"
CONFIG="$CFO_HOME/config.yaml"
REPO_DIR="$(dirname "$0")/.."

echo "╔══════════════════════════════════════╗"
echo "║       philad-cfo Setup Wizard        ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Step 1: Install dependencies
echo "Step 1/4: Installing dependencies..."
bash "$REPO_DIR/scripts/install.sh"
echo ""

# Step 2: Create config directory
echo "Step 2/4: Creating config directory at $CFO_HOME..."
mkdir -p "$CFO_HOME/kb/transactions"
mkdir -p "$CFO_HOME/kb/net_worth"
mkdir -p "$CFO_HOME/kb/mortgage"
mkdir -p "$CFO_HOME/kb/investments"
mkdir -p "$CFO_HOME/kb/goals"
mkdir -p "$CFO_HOME/cache"
echo "  Done."
echo ""

# Step 3: Copy example config
if [ -f "$CONFIG" ]; then
    echo "Step 3/4: Config already exists at $CONFIG — skipping."
else
    echo "Step 3/4: Creating config from example..."
    cp "$REPO_DIR/config/config.yaml.example" "$CONFIG"
    echo "  Created $CONFIG"
fi
echo ""

# Step 4: Prompt for key settings
echo "Step 4/4: Configure your settings"
echo "  Edit $CONFIG to fill in:"
echo "    - plaid.client_id + plaid.secret  (from dashboard.plaid.com)"
echo "    - perplexity.api_key              (from perplexity.ai/settings/api)"
echo "    - discord.webhook_url             (from Discord server settings)"
echo "    - income.monthly_net              (your take-home pay)"
echo "    - mortgage.*                      (your property goal)"
echo ""

echo "╔══════════════════════════════════════╗"
echo "║  Setup complete!  Next steps:        ║"
echo "║  1. Edit ~/.philad-cfo/config.yaml   ║"
echo "║  2. philad-cfo link                  ║"
echo "║  3. philad-cfo sync                  ║"
echo "║  4. philad-cfo daily-report          ║"
echo "╚══════════════════════════════════════╝"

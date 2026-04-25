"""Discord webhook sender — formatted financial reports."""

from __future__ import annotations

from typing import Optional

import requests

from src.config import ConfigurationError, DiscordConfig

DISCORD_CHAR_LIMIT = 2000


class DiscordReporter:
    """Send formatted markdown reports to a Discord webhook.

    Args:
        config: Discord configuration dataclass.
    """

    def __init__(self, config: DiscordConfig) -> None:
        if not config.webhook_url:
            raise ConfigurationError(
                "DISCORD_WEBHOOK_URL is required. Set it in config.yaml."
            )
        self.webhook_url = config.webhook_url

    def send(self, content: str, username: str = "philad-cfo") -> bool:
        """Send a message to the Discord webhook.

        Automatically splits messages exceeding Discord's 2000-character limit.

        Args:
            content: Message content (markdown supported in Discord).
            username: Bot display name.

        Returns:
            True if all parts were sent successfully.
        """
        chunks = self._split_message(content)
        success = True
        for chunk in chunks:
            ok = self._post(chunk, username)
            if not ok:
                success = False
        return success

    def send_report(self, report_md: str, title: str = "Daily CFO Report") -> bool:
        """Send a full report with a header embed.

        Args:
            report_md: Full markdown report text.
            title: Report title for the Discord message.

        Returns:
            True on success.
        """
        header = f"**{title}**\n"
        return self.send(header + report_md)

    def send_signal_alert(
        self,
        symbol: str,
        action: str,
        rsi: float,
        price: float,
        risk: str,
        reason: str,
    ) -> bool:
        """Send a trading signal alert.

        Args:
            symbol: Ticker symbol.
            action: BUY, SELL, or HOLD.
            rsi: Current RSI value.
            price: Current price.
            risk: Risk level (LOW, MED, HIGH).
            reason: Signal reason string.

        Returns:
            True on success.
        """
        emoji = {"BUY": "📈", "SELL": "📉", "HOLD": "➡️"}.get(action, "❓")
        msg = (
            f"{emoji} **{action} Signal: {symbol}**\n"
            f"Risk: {risk} | RSI: {rsi:.1f} | Price: ${price:.2f}\n"
            f"Reason: {reason}"
        )
        return self.send(msg)

    def _post(self, content: str, username: str) -> bool:
        """Post a single message chunk to Discord.

        Args:
            content: Message content (max 2000 chars).
            username: Display name.

        Returns:
            True on HTTP 204.
        """
        try:
            resp = requests.post(
                self.webhook_url,
                json={"content": content, "username": username},
                timeout=10,
            )
            return resp.status_code in (200, 204)
        except requests.RequestException:
            return False

    @staticmethod
    def _split_message(content: str) -> list[str]:
        """Split long messages into chunks within Discord's character limit.

        Args:
            content: Full message string.

        Returns:
            List of message chunks.
        """
        if len(content) <= DISCORD_CHAR_LIMIT:
            return [content]
        chunks: list[str] = []
        lines = content.split("\n")
        current = ""
        for line in lines:
            candidate = current + line + "\n"
            if len(candidate) > DISCORD_CHAR_LIMIT:
                if current:
                    chunks.append(current.rstrip())
                current = line + "\n"
            else:
                current = candidate
        if current.strip():
            chunks.append(current.rstrip())
        return chunks

"""Perplexity API client — financial research queries via pplx-2 model."""

from __future__ import annotations

import json
from typing import Optional

import requests

from src.config import ConfigurationError, PerplexityConfig


PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

SYSTEM_PROMPT = (
    "You are a financial research assistant with expertise in UK personal finance, "
    "mortgage markets, investment analysis, and macroeconomics. "
    "Provide concise, factual, up-to-date answers with specific figures and sources. "
    "Always note when data may be time-sensitive."
)


class PerplexityClient:
    """Client for Perplexity API research queries.

    Args:
        config: Perplexity configuration dataclass.
    """

    def __init__(self, config: PerplexityConfig) -> None:
        if not config.api_key:
            raise ConfigurationError(
                "PERPLEXITY_API_KEY is required for research queries. "
                "Set it in config.yaml or as an environment variable."
            )
        self.config = config

    def query(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> str:
        """Send a research query to Perplexity and return the answer.

        Args:
            question: The research question or prompt.
            system_prompt: Override the default financial system prompt.
            max_tokens: Maximum tokens in the response.

        Returns:
            Response text from Perplexity.

        Raises:
            ConfigurationError: If API key is invalid.
            requests.HTTPError: On non-2xx responses.
        """
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            "max_tokens": max_tokens,
        }
        response = requests.post(
            PERPLEXITY_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30,
        )
        if response.status_code == 401:
            raise ConfigurationError("Invalid PERPLEXITY_API_KEY.")
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"])

    def mortgage_rate_research(self, ltv: float = 0.80, term_years: int = 2) -> str:
        """Research current UK mortgage rates for a given LTV and term.

        Args:
            ltv: Loan-to-value ratio (e.g. 0.80 = 80%).
            term_years: Fixed-rate term in years.

        Returns:
            Research summary as a string.
        """
        q = (
            f"What are the best UK residential mortgage rates available right now "
            f"for a {int(ltv * 100)}% LTV property with a {term_years}-year fixed term? "
            f"Include rates from major lenders (HSBC, Barclays, Halifax, NatWest, Nationwide). "
            f"What is the current Bank of England base rate and market expectation?"
        )
        return self.query(q)

    def investment_thesis_research(self, symbol: str) -> str:
        """Research investment thesis and recent news for a given ticker.

        Args:
            symbol: Stock ticker symbol (e.g. IONQ, DWAVE).

        Returns:
            Research summary including fundamentals, news, and analyst views.
        """
        q = (
            f"Provide a concise investment analysis for {symbol}: "
            f"recent price action, key catalysts, analyst consensus, and risk factors. "
            f"Focus on developments in the last 30 days."
        )
        return self.query(q)

    def market_intelligence(self, topic: str) -> str:
        """Research a broad market or macroeconomic topic.

        Args:
            topic: Research topic (e.g. 'UK property market Q1 2026').

        Returns:
            Research summary.
        """
        return self.query(topic)

    def scenario_analysis(self, scenario: str) -> str:
        """Run a 'what if' financial scenario analysis.

        Args:
            scenario: Scenario description (e.g. 'interest rates drop 1% in 2026').

        Returns:
            Analysis of likely financial impacts.
        """
        q = (
            f"Analyse this financial scenario and its likely impact on a UK household: "
            f"{scenario}. Consider effects on mortgage affordability, savings rates, "
            f"and investment portfolio performance."
        )
        return self.query(q)

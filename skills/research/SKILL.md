---
name: research
description: >
  Financial research via Perplexity API — market intelligence, mortgage rates,
  investment thesis, economic scenarios. Activates on: research, look up,
  find out, what are current rates, market news, what's happening with,
  UK property market, Bank of England, inflation, interest rates, lender rates,
  analyst view, economic outlook, what if scenario, scenario analysis,
  Perplexity, web search, latest news, current data, 2026, market intelligence.
allowed-tools: Read Bash Write
---

# Research Skill

## Overview

Uses Perplexity API (model: pplx-2) to retrieve real-time financial
intelligence. Falls back to noting the query if API key is not configured.

## Step-by-Step Instructions

### 1. Run a Research Query

```bash
philad-cfo research "<your question>"
```

Results are printed and saved to `~/.philad-cfo/kb/research/YYYY-MM-DD.md`.

### 2. Specialist Research Helpers

**Mortgage rates:**
```bash
philad-cfo research "current UK mortgage rates 80 LTV 2-year fixed May 2026"
```

**Investment thesis:**
```bash
philad-cfo research "IONQ IonQ quantum computing investment case 2026"
philad-cfo research "DWAVE D-Wave recent news and analyst ratings"
```

**Market scenarios:**
```bash
philad-cfo research "impact of Bank of England rate cut on UK mortgages 2026"
philad-cfo research "UK property price forecast 2026 2027"
```

### 3. Compose Effective Research Queries

Good query structure:
- Be specific about geography: "UK", "England", "London"
- Include the date context: "2026", "Q1 2026", "current"
- Ask for specific data: "rates", "figures", "percentages"
- Request sources where relevant

### 4. Interpret Results

Perplexity returns synthesised answers with citations. Always note:
- Whether data is real-time or from a recent snapshot
- Any uncertainty or conflicting figures in the response
- Source quality (official bodies, reputable news vs. opinion)

### 5. Save Research to KB

Research results are auto-saved:
```bash
cat ~/.philad-cfo/kb/research/$(date +%Y-%m-%d).md
```

### 6. Perplexity Not Configured?

If `PERPLEXITY_API_KEY` is not set:
1. Tell the user what query would have been run
2. Offer to frame the answer using general financial knowledge
3. Note that live data requires the API key

### 7. Report Format

After a research query:
1. Present the Perplexity answer in full
2. Highlight 2–3 **key takeaways** in bold
3. Note any **action item** for Phil (e.g. "check if your lender offers X")
4. Mention when to refresh this research (rates change weekly)

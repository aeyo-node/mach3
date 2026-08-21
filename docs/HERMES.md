# Hermes System Context Formatter

Hermes translates raw quantitative indicators, order books, and news events into token-optimized Markdown formatting designed for LLM prompts.

---

## 1. Output Format
See `swaram/agents/hermes.py` for context formatting. An example context block:

```markdown
# SWRAM MARKET INTELLIGENCE STATE
Timestamp: 2026-08-21T16:10:26Z
Target Instrument: CRYPTO:BTC/USD

## 1. REAL-TIME MARKET TICK SNAPSHOT
- Last Price: 65000.0
- Bid / Ask: 64998.0 / 65002.0 (Spread: 4.0)

## 2. TECHNICAL INDICATORS (1m Timeframe)
- RSI (14): 32.5 (Oversold)
- Moving Averages: EMA9=65100.0, EMA21=65200.0
- Bollinger Bands: Upper=66000.0, Lower=64800.0

...
```

---

## 2. Dynamic Retrieval Endpoints
- **REST**: `/agent/context/{symbol}`
- **WebSocket Stream**: `/ws/agent/{symbol}`

from typing import Any, Dict, Optional
from swaram.core.time import iso_ist, iso_utc, now_utc


class HermesContextBuilder:
    """Hermes System Context Formatter — Converts full multi-market quantitative state into token-optimized LLM context."""

    def build_system_context(
        self,
        symbol: str,
        canonical_symbol: str,
        snapshot: Optional[Dict[str, Any]],
        indicators: Optional[Dict[str, Any]],
        market_structure: Optional[Dict[str, Any]],
        macro_risk: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        now = now_utc()

        # Build clean markdown system context block
        lines = [
            f"# SWRAM MARKET INTELLIGENCE STATE",
            f"Timestamp: {iso_utc(now)} UTC ({iso_ist(now)} IST)",
            f"Target Instrument: {canonical_symbol} ({symbol})",
            "",
            "## 1. REAL-TIME MARKET TICK SNAPSHOT",
        ]

        if snapshot:
            lines.extend([
                f"- Last Price: {snapshot.get('last')}",
                f"- Bid / Ask: {snapshot.get('bid')} / {snapshot.get('ask')} (Spread: {snapshot.get('spread')})",
                f"- Timestamp: {snapshot.get('timestamp')}",
            ])
        else:
            lines.append("- Snapshot: Unavailable / Data Stream Initializing")

        lines.extend([
            "",
            "## 2. TECHNICAL INDICATORS (1m Timeframe)",
        ])

        if indicators:
            lines.extend([
                f"- RSI (14): {indicators.get('rsi')}",
                f"- MACD: {indicators.get('macd')} (Signal: {indicators.get('macd_signal')}, Hist: {indicators.get('macd_hist')})",
                f"- ATR (14): {indicators.get('atr')}",
                f"- Moving Averages: EMA9={indicators.get('ema_9')}, EMA21={indicators.get('ema_21')}, EMA50={indicators.get('ema_50')}, EMA200={indicators.get('ema_200')}",
                f"- Bollinger Bands: Upper={indicators.get('bollinger_upper')}, Mid={indicators.get('bollinger_mid')}, Lower={indicators.get('bollinger_lower')}",
                f"- 24h Realized Volatility: {indicators.get('realized_vol_24h')}",
            ])
        else:
            lines.append("- Indicators: Insufficient bars available")

        lines.extend([
            "",
            "## 3. INSTITUTIONAL MARKET STRUCTURE",
        ])

        if market_structure:
            lines.extend([
                f"- Trend Regime: {market_structure.get('trend', 'NEUTRAL')}",
                f"- Active FVGs (Fair Value Gaps): {market_structure.get('active_fvgs_count', 0)} unmitigated",
                f"- Active Order Blocks: {market_structure.get('active_order_blocks_count', 0)} zones",
                f"- Latest Structure Event: {market_structure.get('latest_event')}",
            ])
        else:
            lines.append("- Market Structure: Analyzing...")

        lines.extend([
            "",
            "## 4. MACROECONOMIC EVENT RISK WATCHDOG",
        ])

        if macro_risk:
            is_risk = macro_risk.get("is_high_risk_window", False)
            lines.append(f"- Active News Risk Window: {'⚠️ HIGH RISK WINDOW ACTIVE' if is_risk else '✅ SAFE (No Tier-1 news within 15 mins)'}")
            active_evts = macro_risk.get("active_risk_events", [])
            if active_evts:
                lines.append(f"- Active Tier-1 Releases: {active_evts}")
        else:
            lines.append("- Macro Watchdog: Clear")

        context_prompt_text = "\n".join(lines)

        return {
            "canonical_symbol": canonical_symbol,
            "symbol": symbol,
            "timestamp_utc": iso_utc(now),
            "timestamp_ist": iso_ist(now),
            "prompt_context_text": context_prompt_text,
            "structured_payload": {
                "snapshot": snapshot,
                "indicators": indicators,
                "market_structure": market_structure,
                "macro_risk": macro_risk,
            },
        }

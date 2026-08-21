from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import re

# Fallback default dictionary if symbols.yaml is not loaded yet
DEFAULT_SYMBOL_MAP: Dict[str, Dict[str, str]] = {
    "CRYPTO:BTC/USD": {
        "asset_class": "crypto",
        "base": "BTC",
        "quote": "USD",
        "delta": "BTCUSD",
        "bybit": "BTCUSDT",
        "deribit": "BTC-PERPETUAL",
    },
    "CRYPTO:ETH/USD": {
        "asset_class": "crypto",
        "base": "ETH",
        "quote": "USD",
        "delta": "ETHUSD",
        "bybit": "ETHUSDT",
        "deribit": "ETH-PERPETUAL",
    },
    "FX:EUR/USD": {
        "asset_class": "fx",
        "base": "EUR",
        "quote": "USD",
        "ctrader": "EURUSD",
    },
    "FX:GBP/USD": {
        "asset_class": "fx",
        "base": "GBP",
        "quote": "USD",
        "ctrader": "GBPUSD",
    },
    "FX:USD/JPY": {
        "asset_class": "fx",
        "base": "USD",
        "quote": "JPY",
        "ctrader": "USDJPY",
    },
    "METAL:XAU/USD": {
        "asset_class": "metal",
        "base": "XAU",
        "quote": "USD",
        "ctrader": "XAUUSD",
    },
    "METAL:XAG/USD": {
        "asset_class": "metal",
        "base": "XAG",
        "quote": "USD",
        "ctrader": "XAGUSD",
    },
}

# Reverse index: (provider, provider_symbol) -> canonical
PROVIDER_TO_CANONICAL: Dict[Tuple[str, str], str] = {}
for canonical, meta in DEFAULT_SYMBOL_MAP.items():
    for k, v in meta.items():
        if k not in ("asset_class", "base", "quote"):
            PROVIDER_TO_CANONICAL[(k.lower(), v.upper())] = canonical


@dataclass(frozen=True)
class CanonicalSymbol:
    asset_class: str
    base: str
    quote: str

    @property
    def value(self) -> str:
        return f"{self.asset_class.upper()}:{self.base.upper()}/{self.quote.upper()}"

    def __str__(self) -> str:
        return self.value


def parse_canonical(canonical: str) -> CanonicalSymbol:
    """Parse a canonical symbol string like 'CRYPTO:BTC/USD' into CanonicalSymbol."""
    canonical = canonical.strip().upper()
    match = re.match(r"^([A-Z]+):([A-Z0-9_\-]+)/([A-Z0-9_\-]+)$", canonical)
    if not match:
        raise ValueError(f"Invalid canonical symbol format: '{canonical}'. Expected 'CLASS:BASE/QUOTE'")
    return CanonicalSymbol(
        asset_class=match.group(1).lower(),
        base=match.group(2),
        quote=match.group(3),
    )


def to_canonical(provider: str, symbol: str) -> str:
    """Map a provider-specific symbol to its canonical form."""
    key = (provider.strip().lower(), symbol.strip().upper())
    if key in PROVIDER_TO_CANONICAL:
        return PROVIDER_TO_CANONICAL[key]

    # Heuristic resolution
    sym = symbol.strip().upper().replace("/", "").replace("-", "").replace("_", "")
    if sym in ("BTCUSD", "BTCUSDT", "XBTUSD"):
        return "CRYPTO:BTC/USD"
    elif sym in ("ETHUSD", "ETHUSDT"):
        return "CRYPTO:ETH/USD"
    elif sym in ("EURUSD",):
        return "FX:EUR/USD"
    elif sym in ("GBPUSD",):
        return "FX:GBP/USD"
    elif sym in ("USDJPY",):
        return "FX:USD/JPY"
    elif sym in ("XAUUSD", "GOLD"):
        return "METAL:XAU/USD"
    elif sym in ("XAGUSD", "SILVER"):
        return "METAL:XAG/USD"

    # Default fallback
    return f"UNKNOWN:{symbol.upper()}"


def resolve_canonical(input_str: str) -> str:
    """Resolve any input (e.g. BTCUSD, BTC/USD, CRYPTO:BTC/USD) into canonical format."""
    input_str = input_str.strip().upper()
    if ":" in input_str and "/" in input_str:
        return input_str
    
    # Common short names
    clean = input_str.replace("/", "").replace("-", "").replace("_", "")
    if clean in ("BTC", "BTCUSD", "BTCUSDT"):
        return "CRYPTO:BTC/USD"
    if clean in ("ETH", "ETHUSD", "ETHUSDT"):
        return "CRYPTO:ETH/USD"
    if clean == "EURUSD":
        return "FX:EUR/USD"
    if clean == "GBPUSD":
        return "FX:GBP/USD"
    if clean == "USDJPY":
        return "FX:USD/JPY"
    if clean in ("XAUUSD", "GOLD"):
        return "METAL:XAU/USD"
    if clean in ("XAGUSD", "SILVER"):
        return "METAL:XAG/USD"

    # Guess format
    if "/" in input_str:
        parts = input_str.split("/")
        return f"CRYPTO:{parts[0]}/{parts[1]}"

    return f"UNKNOWN:{input_str}"


def to_provider_symbol(canonical: str, provider: str) -> str:
    """Retrieve provider-specific symbol for a given canonical symbol."""
    canonical_upper = canonical.strip().upper()
    meta = DEFAULT_SYMBOL_MAP.get(canonical_upper)
    if meta and provider.lower() in meta:
        return meta[provider.lower()]
    
    # Fallback to base+quote
    parsed = parse_canonical(canonical_upper)
    return f"{parsed.base}{parsed.quote}"

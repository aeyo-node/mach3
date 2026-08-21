from typing import Dict, Optional, Tuple, Union
import numpy as np


def calculate_sma(values: np.ndarray, period: int) -> np.ndarray:
    """Calculate Simple Moving Average (SMA)."""
    if len(values) < period:
        return np.full_like(values, np.nan, dtype=float)
    
    weights = np.ones(period) / period
    sma = np.convolve(values, weights, mode='valid')
    # Pad beginning with NaN to maintain original array length
    pad = np.full(period - 1, np.nan)
    return np.concatenate((pad, sma))


def calculate_ema(values: np.ndarray, period: int) -> np.ndarray:
    """Calculate Exponential Moving Average (EMA)."""
    if len(values) == 0:
        return np.array([], dtype=float)
    if len(values) < period:
        return np.full_like(values, np.nan, dtype=float)

    ema = np.empty_like(values, dtype=float)
    ema[:period - 1] = np.nan
    # Seed first valid EMA with SMA
    ema[period - 1] = np.mean(values[:period])

    multiplier = 2.0 / (period + 1)
    for i in range(period, len(values)):
        ema[i] = (values[i] - ema[i - 1]) * multiplier + ema[i - 1]

    return ema


def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Relative Strength Index (RSI)."""
    if len(prices) <= period:
        return np.full_like(prices, np.nan, dtype=float)

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    rsi = np.empty_like(prices, dtype=float)
    rsi[:period] = np.nan

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    if avg_loss == 0:
        rsi[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi[period] = 100.0 - (100.0 / (1.0 + rs))

    for i in range(period + 1, len(prices)):
        gain = gains[i - 1]
        loss = losses[i - 1]

        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))

    return rsi


def calculate_macd(
    prices: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate MACD line, Signal line, and MACD Histogram."""
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)
    macd_line = fast_ema - slow_ema

    # Filter out NaNs for signal calculation
    valid_macd_idx = np.where(~np.isnan(macd_line))[0]
    signal_line = np.full_like(prices, np.nan, dtype=float)
    macd_hist = np.full_like(prices, np.nan, dtype=float)

    if len(valid_macd_idx) >= signal_period:
        valid_macd = macd_line[valid_macd_idx]
        sig = calculate_ema(valid_macd, signal_period)
        signal_line[valid_macd_idx] = sig
        macd_hist = macd_line - signal_line

    return macd_line, signal_line, macd_hist


def calculate_atr(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 14,
) -> np.ndarray:
    """Calculate Average True Range (ATR)."""
    if len(closes) < 2:
        return np.full_like(closes, np.nan, dtype=float)

    tr0 = highs - lows
    tr1 = np.abs(highs[1:] - closes[:-1])
    tr2 = np.abs(lows[1:] - closes[:-1])

    tr = np.empty(len(closes), dtype=float)
    tr[0] = tr0[0]
    tr[1:] = np.maximum(tr0[1:], np.maximum(tr1, tr2))

    return calculate_ema(tr, period)


def calculate_bollinger_bands(
    prices: np.ndarray,
    period: int = 20,
    num_std: float = 2.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Bollinger Bands (Upper, Middle/SMA, Lower)."""
    sma = calculate_sma(prices, period)
    upper = np.full_like(prices, np.nan, dtype=float)
    lower = np.full_like(prices, np.nan, dtype=float)

    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1 : i + 1]
        std = np.std(window)
        upper[i] = sma[i] + (num_std * std)
        lower[i] = sma[i] - (num_std * std)

    return upper, sma, lower


def calculate_realized_volatility(closes: np.ndarray, window: int = 24) -> float:
    """Calculate rolling annualized realized volatility from close prices."""
    if len(closes) < 2:
        return 0.0

    recent = closes[-window:] if len(closes) >= window else closes
    log_returns = np.diff(np.log(recent))
    if len(log_returns) == 0:
        return 0.0

    # Annualize assuming 365 days / 24h per day
    std_dev = np.std(log_returns)
    annualized_vol = std_dev * np.sqrt(365 * 24)
    return float(annualized_vol)

import numpy as np
import pytest
from swaram.analytics.indicators import (
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_realized_volatility,
    calculate_rsi,
    calculate_sma,
)


def test_calculate_sma():
    prices = np.array([10.0, 11.0, 12.0, 13.0, 14.0], dtype=float)
    sma = calculate_sma(prices, 3)
    assert np.isnan(sma[0])
    assert np.isnan(sma[1])
    assert pytest.approx(sma[2], 0.01) == 11.0
    assert pytest.approx(sma[4], 0.01) == 13.0


def test_calculate_ema():
    prices = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0], dtype=float)
    ema = calculate_ema(prices, 3)
    assert np.isnan(ema[0])
    assert np.isnan(ema[1])
    assert pytest.approx(ema[2], 0.01) == 11.0
    assert ema[5] > ema[2]


def test_calculate_rsi():
    # Uptrend
    prices = np.array([100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 108.0, 110.0, 112.0, 111.0, 115.0, 118.0, 120.0, 122.0, 125.0], dtype=float)
    rsi = calculate_rsi(prices, 14)
    assert not np.isnan(rsi[-1])
    assert rsi[-1] > 50.0  # Strong uptrend RSI > 50


def test_calculate_macd():
    prices = np.linspace(100.0, 200.0, 50)
    macd, signal, hist = calculate_macd(prices, 12, 26, 9)
    assert not np.isnan(macd[-1])
    assert not np.isnan(signal[-1])
    assert not np.isnan(hist[-1])


def test_calculate_bollinger_bands():
    prices = np.linspace(100.0, 150.0, 30)
    upper, mid, lower = calculate_bollinger_bands(prices, 20, 2.0)
    assert upper[-1] > mid[-1] > lower[-1]


def test_calculate_realized_volatility():
    prices = np.array([100.0, 105.0, 98.0, 103.0, 97.0, 102.0], dtype=float)
    vol = calculate_realized_volatility(prices)
    assert vol > 0.0

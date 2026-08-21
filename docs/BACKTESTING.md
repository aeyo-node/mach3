# Historical Backtesting Engine

Swaram includes an event-driven backtesting engine to evaluate strategies over historical candle sequences.

---

## 1. Metric Calculations
- **Sharpe Ratio**: Annualized return divided by annualized standard deviation of daily returns.
- **Max Drawdown**: Peak-to-trough decline of the simulated equity curve.
- **Profit Factor**: Sum of gross profits divided by the sum of gross losses.

---

## 2. API Usage
To run a backtest over a historical window:
```bash
curl -X POST http://localhost:8000/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSD", "start_time": "2026-08-21T00:00:00Z", "end_time": "2026-08-21T18:00:00Z", "initial_capital": 10000.0}'
```

Returns performance stats and the historical equity curve sequence.

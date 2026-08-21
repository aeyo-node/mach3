# Machine Learning Interface

This document specifies the Swaram Machine Learning forecasting model integration hooks.

---

## 1. Feature Representation
Features are continuously generated and exposed via:
- `/market/{symbol}/indicators`
- `/market/{symbol}/structure`
- `/market/{symbol}/orderflow`

## 2. In-Process Estimation (Placeholder Hooks)
ML pipelines subscribe to Redis streams or scrape `/metrics` to train:
- **Directional Skew Estimator**: Binary classification predicting \(T+15m\) price changes.
- **Volatility Regimes**: Predicts volatility spikes to adjust Kelly Sizing ratios.

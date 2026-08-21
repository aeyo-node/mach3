# Risk Management Engine Documentation

The Risk Engine serves as a safety filter guarding all executed orders.

---

## 1. Safety Checks
Before passing any order to execution, Swaram performs these checks:
1. **Drawdown Halt**: Prevents trading if overall account drawdown exceeds the limit (default: 10%).
2. **Exposure Limits**: Caps max capital exposure on any single instrument (default: 20%).
3. **Per-Trade Loss Limit**: Recommends scaling down sizes if the trade's raw dollar risk is excessive.

---

## 2. API Reference
- `POST /risk/check` — Submits order details to check eligibility. Returns `ALLOW` or `BLOCK`.
- `POST /risk/position-size` — Sizing calculations.
- `GET /risk/state` — Retrieves the active drawdown status and exposure metrics.

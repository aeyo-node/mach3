"""
Swaram Risk Management Engine.
Pre-trade risk gate + portfolio-level safety guards.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskState:
    current_capital: float
    initial_capital: float
    position_size: float
    entry_price: float
    current_price: float
    max_drawdown_pct: float          # Alert threshold e.g. 10%
    max_position_pct: float          # Max % of capital in one position e.g. 20%
    max_loss_per_trade_pct: float    # Max loss per trade e.g. 2%


@dataclass
class RiskCheckResult:
    allowed: bool
    reason: str
    suggested_quantity: float
    current_drawdown_pct: float
    current_exposure_pct: float


class RiskEngine:
    """
    Production-grade pre-trade and portfolio risk engine.
    Methods:
      - check_trade: Pre-trade gate → returns ALLOW / BLOCK with reason
      - kelly_size: Kelly Criterion position sizing
      - fixed_fractional_size: Fixed-fraction position sizing
    """

    def check_trade(self, state: RiskState, requested_qty: float) -> RiskCheckResult:
        """Pre-trade risk gate. Blocks if drawdown, exposure, or margin limits are breached."""
        current_drawdown_pct = self._drawdown_pct(state)
        trade_value = requested_qty * state.current_price
        current_exposure_pct = (state.position_size * state.current_price / state.initial_capital) * 100.0
        proposed_exposure_pct = ((state.position_size + requested_qty) * state.current_price / state.initial_capital) * 100.0

        # Guard 1: Max drawdown halt
        if current_drawdown_pct >= state.max_drawdown_pct:
            return RiskCheckResult(
                allowed=False,
                reason=f"Max drawdown guard: drawdown {current_drawdown_pct:.2f}% >= limit {state.max_drawdown_pct}%",
                suggested_quantity=0.0,
                current_drawdown_pct=current_drawdown_pct,
                current_exposure_pct=current_exposure_pct,
            )

        # Guard 2: Max position exposure
        if proposed_exposure_pct > state.max_position_pct:
            return RiskCheckResult(
                allowed=False,
                reason=f"Position limit: proposed exposure {proposed_exposure_pct:.2f}% > limit {state.max_position_pct}%",
                suggested_quantity=0.0,
                current_drawdown_pct=current_drawdown_pct,
                current_exposure_pct=current_exposure_pct,
            )

        # Guard 3: Max loss per trade
        max_loss_dollars = state.initial_capital * (state.max_loss_per_trade_pct / 100.0)
        if trade_value > max_loss_dollars:
            suggested = max_loss_dollars / state.current_price
            return RiskCheckResult(
                allowed=False,
                reason=f"Per-trade loss limit: trade value ${trade_value:.2f} > ${max_loss_dollars:.2f} limit",
                suggested_quantity=round(suggested, 4),
                current_drawdown_pct=current_drawdown_pct,
                current_exposure_pct=current_exposure_pct,
            )

        return RiskCheckResult(
            allowed=True,
            reason="All risk checks passed",
            suggested_quantity=requested_qty,
            current_drawdown_pct=current_drawdown_pct,
            current_exposure_pct=current_exposure_pct,
        )

    def kelly_size(
        self,
        win_rate: float,          # e.g. 0.55 for 55%
        avg_win: float,           # average profit on wins
        avg_loss: float,          # average loss on losses
        capital: float,
        current_price: float,
        fraction: float = 0.25,   # fractional Kelly (safer)
    ) -> float:
        """Kelly Criterion position sizing (fractional)."""
        if avg_loss == 0 or current_price == 0:
            return 0.0
        odds = avg_win / avg_loss
        kelly_fraction = win_rate - ((1.0 - win_rate) / odds)
        safe_fraction = kelly_fraction * fraction
        safe_fraction = max(0.0, min(safe_fraction, 0.20))  # Cap at 20% of capital
        return round((capital * safe_fraction) / current_price, 4)

    def fixed_fractional_size(
        self,
        capital: float,
        current_price: float,
        risk_pct: float = 2.0,    # Risk 2% of capital per trade
    ) -> float:
        """Fixed-fractional position sizing."""
        if current_price == 0:
            return 0.0
        return round((capital * risk_pct / 100.0) / current_price, 4)

    def _drawdown_pct(self, state: RiskState) -> float:
        if state.initial_capital == 0:
            return 0.0
        return max(0.0, (state.initial_capital - state.current_capital) / state.initial_capital * 100.0)

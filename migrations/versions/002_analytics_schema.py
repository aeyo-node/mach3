"""analytics schema

Revision ID: 002_analytics_schema
Revises: 001_initial_schema
Create Date: 2026-08-21 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_analytics_schema"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. market_structure_events table
    op.create_table(
        "market_structure_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("price_level", sa.Float(), nullable=False),
        sa.Column("boundary_high", sa.Float(), nullable=True),
        sa.Column("boundary_low", sa.Float(), nullable=True),
        sa.Column("is_mitigated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("mitigated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_structure_events_timestamp", "market_structure_events", ["timestamp"])
    op.create_index("ix_market_structure_events_instrument_id", "market_structure_events", ["instrument_id"])
    op.create_index("ix_market_structure_events_timeframe", "market_structure_events", ["timeframe"])
    op.create_index("ix_market_structure_events_event_type", "market_structure_events", ["event_type"])
    op.create_index("ix_market_structure_events_direction", "market_structure_events", ["direction"])
    op.create_index("ix_market_structure_events_is_mitigated", "market_structure_events", ["is_mitigated"])

    # 2. indicator_snapshots table
    op.create_table(
        "indicator_snapshots",
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("provider", sa.String(length=32), server_default="engine", nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("rsi", sa.Float(), nullable=True),
        sa.Column("macd", sa.Float(), nullable=True),
        sa.Column("macd_signal", sa.Float(), nullable=True),
        sa.Column("macd_hist", sa.Float(), nullable=True),
        sa.Column("atr", sa.Float(), nullable=True),
        sa.Column("ema_9", sa.Float(), nullable=True),
        sa.Column("ema_21", sa.Float(), nullable=True),
        sa.Column("ema_50", sa.Float(), nullable=True),
        sa.Column("ema_200", sa.Float(), nullable=True),
        sa.Column("bollinger_upper", sa.Float(), nullable=True),
        sa.Column("bollinger_mid", sa.Float(), nullable=True),
        sa.Column("bollinger_lower", sa.Float(), nullable=True),
        sa.Column("vwap", sa.Float(), nullable=True),
        sa.Column("cvd", sa.Float(), nullable=True),
        sa.Column("realized_vol_24h", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("timestamp", "instrument_id", "timeframe", "provider"),
    )


def downgrade() -> None:
    op.drop_table("indicator_snapshots")
    op.drop_table("market_structure_events")

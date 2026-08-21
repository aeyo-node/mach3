"""orderflow schema

Revision ID: 004_orderflow_schema
Revises: 003_macro_schema
Create Date: 2026-08-21 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_orderflow_schema"
down_revision: Union[str, None] = "003_macro_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. orderflow_snapshots table
    op.create_table(
        "orderflow_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("best_bid", sa.Float(), nullable=False),
        sa.Column("best_ask", sa.Float(), nullable=False),
        sa.Column("mid_price", sa.Float(), nullable=False),
        sa.Column("microprice", sa.Float(), nullable=False),
        sa.Column("spread", sa.Float(), nullable=False),
        sa.Column("spread_bps", sa.Float(), nullable=False),
        sa.Column("bid_depth_top20", sa.Float(), nullable=False),
        sa.Column("ask_depth_top20", sa.Float(), nullable=False),
        sa.Column("depth_imbalance", sa.Float(), nullable=False),
        sa.Column("liquidity_walls", sa.JSON(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orderflow_snapshots_timestamp", "orderflow_snapshots", ["timestamp"])
    op.create_index("ix_orderflow_snapshots_instrument_id", "orderflow_snapshots", ["instrument_id"])

    # 2. positioning_records table
    op.create_table(
        "positioning_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("funding_rate", sa.Float(), nullable=True),
        sa.Column("annualized_funding_yield", sa.Float(), nullable=True),
        sa.Column("open_interest", sa.Float(), nullable=True),
        sa.Column("open_interest_delta_24h", sa.Float(), nullable=True),
        sa.Column("positioning_regime", sa.String(length=32), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_positioning_records_timestamp", "positioning_records", ["timestamp"])
    op.create_index("ix_positioning_records_instrument_id", "positioning_records", ["instrument_id"])


def downgrade() -> None:
    op.drop_table("positioning_records")
    op.drop_table("orderflow_snapshots")

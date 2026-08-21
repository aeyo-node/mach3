"""execution schema

Revision ID: 006_execution_schema
Revises: 005_anomaly_schema
Create Date: 2026-08-21 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "006_execution_schema"
down_revision: Union[str, None] = "005_anomaly_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. account_balances table
    op.create_table(
        "account_balances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("asset", sa.String(length=16), nullable=False),
        sa.Column("balance", sa.Float(), nullable=False),
        sa.Column("equity", sa.Float(), nullable=False),
        sa.Column("available_margin", sa.Float(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_account_balances_timestamp", "account_balances", ["timestamp"])

    # 2. live_orders table
    op.create_table(
        "live_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("order_id", sa.String(length=64), nullable=False),
        sa.Column("client_order_id", sa.String(length=64), nullable=True),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column("order_type", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("filled_quantity", sa.Float(), nullable=False),
        sa.Column("avg_fill_price", sa.Float(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_live_orders_timestamp", "live_orders", ["timestamp"])
    op.create_index("ix_live_orders_order_id", "live_orders", ["order_id"], unique=True)
    op.create_index("ix_live_orders_status", "live_orders", ["status"])
    op.create_index("ix_live_orders_instrument_id", "live_orders", ["instrument_id"])


def downgrade() -> None:
    op.drop_table("live_orders")
    op.drop_table("account_balances")

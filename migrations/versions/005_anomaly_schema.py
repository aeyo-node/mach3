"""anomaly schema

Revision ID: 005_anomaly_schema
Revises: 004_orderflow_schema
Create Date: 2026-08-21 19:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005_anomaly_schema"
down_revision: Union[str, None] = "004_orderflow_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_anomaly_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("anomaly_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("trigger_value", sa.Float(), nullable=False),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_anomaly_records_timestamp", "market_anomaly_records", ["timestamp"])
    op.create_index("ix_market_anomaly_records_anomaly_type", "market_anomaly_records", ["anomaly_type"])
    op.create_index("ix_market_anomaly_records_instrument_id", "market_anomaly_records", ["instrument_id"])


def downgrade() -> None:
    op.drop_table("market_anomaly_records")

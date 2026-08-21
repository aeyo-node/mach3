"""macro schema

Revision ID: 003_macro_schema
Revises: 002_analytics_schema
Create Date: 2026-08-21 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_macro_schema"
down_revision: Union[str, None] = "002_analytics_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "macro_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("country", sa.String(length=16), nullable=False),
        sa.Column("event_name", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("impact_level", sa.String(length=16), nullable=False),
        sa.Column("actual", sa.Float(), nullable=True),
        sa.Column("forecast", sa.Float(), nullable=True),
        sa.Column("previous", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=16), nullable=True),
        sa.Column("source", sa.String(length=64), server_default="calendar_feed", nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_macro_events_timestamp", "macro_events", ["timestamp"])
    op.create_index("ix_macro_events_country", "macro_events", ["country"])
    op.create_index("ix_macro_events_event_name", "macro_events", ["event_name"])
    op.create_index("ix_macro_events_category", "macro_events", ["category"])
    op.create_index("ix_macro_events_impact_level", "macro_events", ["impact_level"])


def downgrade() -> None:
    op.drop_table("macro_events")

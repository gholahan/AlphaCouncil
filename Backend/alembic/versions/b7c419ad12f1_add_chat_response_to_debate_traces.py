"""Add a dedicated chat response column to debate traces.

Revision ID: b7c419ad12f1
Revises: 40ae6784efee
Create Date: 2026-11-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c419ad12f1"
down_revision: Union[str, None] = "40ae6784efee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "debate_traces",
        sa.Column("chat_response", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("debate_traces", "chat_response")

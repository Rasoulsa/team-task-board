"""add notification deduplication key

Revision ID: a1268901a74f
Revises: 753f2ecaa444
Create Date: 2026-07-16 13:04:23.329680

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1268901a74f"
down_revision: str | Sequence[str] | None = "753f2ecaa444"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "notifications",
        sa.Column(
            "deduplication_key",
            sa.String(length=200),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_notifications_deduplication_key"),
        "notifications",
        ["deduplication_key"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_notifications_deduplication_key"),
        table_name="notifications",
    )
    op.drop_column("notifications", "deduplication_key")

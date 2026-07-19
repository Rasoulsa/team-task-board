"""add unique card assignee constraint

Revision ID: 4b5eea0a6b38
Revises: a1268901a74f
Create Date: 2026-07-17 10:15:21.592753

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4b5eea0a6b38"
down_revision: str | Sequence[str] | None = "a1268901a74f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add uniqueness for card assignments."""
    op.create_unique_constraint(
        "uq_card_assignees_card_id_user_id",
        "card_assignees",
        ["card_id", "user_id"],
    )


def downgrade() -> None:
    """Remove uniqueness for card assignments."""
    op.drop_constraint(
        "uq_card_assignees_card_id_user_id",
        "card_assignees",
        type_="unique",
    )

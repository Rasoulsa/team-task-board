"""reporting and caching indexes

Revision ID: a23966086a1c
Revises: ba0cdc7f2fa7
Create Date: 2026-07-20 16:25:46.188230

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a23966086a1c"
down_revision: str | Sequence[str] | None = "ba0cdc7f2fa7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Cursor pagination over the activity feed:
    # ORDER BY created_at DESC, id DESC  scoped to a board.
    op.create_index(
        "ix_activity_logs_board_created_id",
        "activity_logs",
        ["board_id", "created_at", "id"],
        unique=False,
    )

    # Overdue stats: open cards whose due_date has passed.
    # Partial index keeps it small (only cards that actually have a due_date).
    op.create_index(
        "ix_cards_due_date_active",
        "cards",
        ["due_date"],
        unique=False,
        postgresql_where="due_date IS NOT NULL AND is_deleted = false",
    )

    # Stats join path: assignees -> user, filtered by card.
    # (card_id, user_id) already unique; add user_id lookup for per-member grouping.
    op.create_index(
        "ix_card_assignees_user_card",
        "card_assignees",
        ["user_id", "card_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_card_assignees_user_card", table_name="card_assignees")
    op.drop_index("ix_cards_due_date_active", table_name="cards")
    op.drop_index("ix_activity_logs_board_created_id", table_name="activity_logs")

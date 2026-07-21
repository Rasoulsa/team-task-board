"""reporting caching activity

Revision ID: 872aaa41e10e
Revises: a23966086a1c
Create Date: 2026-07-20 17:26:09.794348

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "872aaa41e10e"
down_revision: str | Sequence[str] | None = "a23966086a1c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Explicit "done" flag on columns (Option C) ---
    op.execute(
        """
        ALTER TABLE board_columns
        ADD COLUMN IF NOT EXISTS is_done_column BOOLEAN NOT NULL DEFAULT false
        """
    )

    # Backfill: the highest-position column on each board becomes the done column.
    op.execute(
        """
        UPDATE board_columns AS bc
        SET is_done_column = true
        FROM (
            SELECT DISTINCT ON (board_id) id
            FROM board_columns
            ORDER BY board_id, position DESC, created_at DESC
        ) AS last_col
        WHERE bc.id = last_col.id
        """
    )

    # --- Indexes (idempotent; the activity index already exists) ---
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_activity_logs_board_created_id
        ON activity_logs (board_id, created_at DESC, id DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_card_assignees_user_card
        ON card_assignees (user_id, card_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_cards_due_date_active
        ON cards (due_date)
        WHERE due_date IS NOT NULL AND is_deleted = false
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_cards_column_is_deleted
        ON cards (column_id, is_deleted)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_cards_column_is_deleted")
    op.execute("DROP INDEX IF EXISTS ix_cards_due_date_active")
    op.execute("DROP INDEX IF EXISTS ix_card_assignees_user_card")
    op.execute("DROP INDEX IF EXISTS ix_activity_logs_board_created_id")
    op.execute("ALTER TABLE board_columns DROP COLUMN IF EXISTS is_done_column")

"""add guest role and invitation notification type

Revision ID: ba0cdc7f2fa7
Revises: 4b5eea0a6b38
Create Date: 2026-07-19

"""

from alembic import op

revision = "ba0cdc7f2fa7"
down_revision = "4b5eea0a6b38"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("COMMIT")
    op.execute("ALTER TYPE organization_role ADD VALUE IF NOT EXISTS 'GUEST'")
    op.execute("ALTER TYPE invitation_role ADD VALUE IF NOT EXISTS 'GUEST'")
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'ORGANIZATION_INVITATION'")


def downgrade() -> None:
    pass

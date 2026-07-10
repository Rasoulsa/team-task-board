"""create authentication tables

Revision ID: cbd098bbfc02
Revises:
Create Date: 2026-07-10 11:26:25.302399
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cbd098bbfc02"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "invitations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("inviter_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "OWNER",
                "ADMIN",
                "MEMBER",
                "VIEWER",
                name="invitation_role",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "ACCEPTED",
                "EXPIRED",
                "REVOKED",
                name="invitation_status",
            ),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["inviter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_invitations_email"),
        "invitations",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_invitations_inviter_id"),
        "invitations",
        ["inviter_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_invitations_organization_id"),
        "invitations",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_invitations_token"),
        "invitations",
        ["token"],
        unique=True,
    )

    op.create_table(
        "org_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "OWNER",
                "ADMIN",
                "MEMBER",
                "VIEWER",
                name="organization_role",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_org_member_user",
        ),
    )

    op.create_index(
        op.f("ix_org_members_organization_id"),
        "org_members",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_org_members_user_id"),
        "org_members",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_org_members_user_id"), table_name="org_members")
    op.drop_index(
        op.f("ix_org_members_organization_id"),
        table_name="org_members",
    )
    op.drop_table("org_members")

    op.drop_index(op.f("ix_invitations_token"), table_name="invitations")
    op.drop_index(
        op.f("ix_invitations_organization_id"),
        table_name="invitations",
    )
    op.drop_index(op.f("ix_invitations_inviter_id"), table_name="invitations")
    op.drop_index(op.f("ix_invitations_email"), table_name="invitations")
    op.drop_table("invitations")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_table("organizations")

    op.execute("DROP TYPE IF EXISTS invitation_status")
    op.execute("DROP TYPE IF EXISTS invitation_role")
    op.execute("DROP TYPE IF EXISTS organization_role")

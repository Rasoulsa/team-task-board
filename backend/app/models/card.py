from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.board_column import BoardColumn
    from app.models.comment import Comment


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    column_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("board_columns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )

    rank: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    labels: Mapped[list[CardLabel]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )

    assignees: Mapped[list[CardAssignee]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )

    checklist_items: Mapped[list[ChecklistItem]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )

    comments: Mapped[list[Comment]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )

    column: Mapped["BoardColumn"] = relationship(
        "BoardColumn",
        back_populates="cards",
    )

    labels: Mapped[list[CardLabel]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )

    assignees: Mapped[list[CardAssignee]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )

    checklist_items: Mapped[list[ChecklistItem]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )

    comments: Mapped[list[Comment]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )

class CardLabel(Base):
    __tablename__ = "card_labels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="gray")

    card: Mapped[Card] = relationship(back_populates="labels")


class CardAssignee(Base):
    __tablename__ = "card_assignees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    card: Mapped[Card] = relationship(back_populates="assignees")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(String(255), nullable=False)
    is_done: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    card: Mapped[Card] = relationship(back_populates="checklist_items")

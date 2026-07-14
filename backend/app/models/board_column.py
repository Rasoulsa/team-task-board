import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.board import Board
    from app.models.card import Card


class BoardColumn(Base):
    __tablename__ = "board_columns"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    board_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    board: Mapped["Board"] = relationship(
        "Board",
        back_populates="columns",
    )

    cards: Mapped[list["Card"]] = relationship(
        "Card",
        back_populates="column",
        cascade="all, delete-orphan",
        order_by="Card.rank",
    )
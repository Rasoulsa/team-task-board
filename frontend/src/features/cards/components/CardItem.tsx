import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { CSSProperties, KeyboardEvent } from "react";

import type { Card, CardPriority } from "../domain/types";

interface CardItemProps {
  card: Card;
  onOpen: (card: Card) => void;
  onDelete: (card: Card) => void;
}

interface CardPreviewProps {
  card: Card;
  isDragging?: boolean;
}

const priorityColor: Record<CardPriority, string> = {
  low: "#94a3b8",
  medium: "#3b82f6",
  high: "#f59e0b",
  urgent: "#ef4444",
};

export function CardPreview({
  card,
  isDragging = false,
}: CardPreviewProps) {
  return (
    <div
      className={`kanban-card${
        isDragging ? " kanban-card--overlay" : ""
      }`}
    >
      <div
        className="kanban-card__priority"
        style={{
          backgroundColor: priorityColor[card.priority],
        }}
      />

      <p className="kanban-card__title">{card.title}</p>

      {card.due_date ? (
        <p className="kanban-card__due">
          Due {card.due_date.slice(0, 10)}
        </p>
      ) : null}

      {card.assignees.length > 0 ? (
        <div className="kanban-card__assignees">
          {card.assignees.map((assignee) => (
            <span key={assignee.id} title={assignee.user_id}>
              {assignee.user_id.charAt(0).toUpperCase()}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function CardItem({ card, onOpen, onDelete }: CardItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: card.id,
    data: {
      type: "card",
      card,
    },
  });

  const style: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.35 : 1,
  };

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onOpen(card);
    }
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      role="button"
      tabIndex={0}
      onClick={() => onOpen(card)}
      onKeyDown={handleKeyDown}
      data-testid={`card-${card.id}`}
      className="kanban-card-wrapper"
    >
      <button
        type="button"
        className="kanban-card__delete"
        aria-label={`Delete ${card.title}`}
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => {
          event.stopPropagation();
          onDelete(card);
        }}
      >
        ×
      </button>

      <CardPreview card={card} />
    </div>
  );
}
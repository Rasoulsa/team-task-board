import { useDroppable } from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useState, type FormEvent } from "react";

import type { Card, Column } from "../domain/types";
import { CardItem } from "./CardItem";

interface ColumnLaneProps {
  column: Column;
  onOpenCard: (card: Card) => void;
  onAddCard: (columnId: string, title: string) => Promise<void>;
  onDeleteCard: (card: Card) => void;
  isAddingCard?: boolean;
}

export function ColumnLane({
  column,
  onOpenCard,
  onAddCard,
  onDeleteCard,
  isAddingCard = false,
}: ColumnLaneProps) {
  const [title, setTitle] = useState("");

  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
    data: {
      type: "column",
      column,
    },
  });

  async function submit() {
    if (isAddingCard) {
      return;
    }

    const normalizedTitle = title.trim();

    if (!normalizedTitle) {
      return;
    }

    try {
      await onAddCard(column.id, normalizedTitle);
      setTitle("");
    } catch {
      // The mutation error is displayed by KanbanBoard.
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submit();
  }

  const sortedCards = [...column.cards].sort((left, right) =>
    left.rank.localeCompare(right.rank),
  );

  return (
    <section
      className={`kanban-column${isOver ? " kanban-column--over" : ""}`}
      data-testid="board-column"
      data-column-id={column.id}
      aria-label={column.name}
    >
      <header className="kanban-column__header">
        <h3>{column.name}</h3>

        <span aria-label={`${sortedCards.length} cards`}>
          {sortedCards.length}
        </span>
      </header>

      <div
        ref={setNodeRef}
        className="kanban-column__body"
        data-testid="column-body"
        data-column-id={column.id}
      >
        <SortableContext
          items={sortedCards.map((card) => card.id)}
          strategy={verticalListSortingStrategy}
        >
          {sortedCards.map((card) => (
            <CardItem
              key={card.id}
              card={card}
              onOpen={onOpenCard}
              onDelete={onDeleteCard}
            />
          ))}
        </SortableContext>

        {sortedCards.length === 0 ? (
          <p className="kanban-column__empty">Drop cards here</p>
        ) : null}
      </div>

      <form className="kanban-column__footer" onSubmit={handleSubmit}>
        <input
          type="text"
          value={title}
          data-testid="add-card-input"
          aria-label={`Add a card to ${column.name}`}
          placeholder="Add a card"
          autoComplete="off"
          disabled={isAddingCard}
          onChange={(event) => setTitle(event.target.value)}
        />

        <button
          type="submit"
          data-testid="add-card-submit"
          disabled={isAddingCard || !title.trim()}
        >
          {isAddingCard ? "Adding…" : "Add"}
        </button>
      </form>
    </section>
  );
}
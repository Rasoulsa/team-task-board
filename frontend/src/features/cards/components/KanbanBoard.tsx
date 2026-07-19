import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useBoardSocket } from "../../realtime/useBoardSocket";
import type { Card } from "../domain/types";
import { useBoard } from "../hooks/useBoard";
import { useCreateCard } from "../hooks/useCreateCard";
import { useDeleteCard } from "../hooks/useDeleteCard";
import { useMoveCard } from "../hooks/useMoveCard";
import { CardPreview } from "./CardItem";
import { CardModal } from "./CardModal";
import { ColumnLane } from "./ColumnLane";

interface KanbanBoardProps {
  boardId: string;
  readOnlyExceptDescription?: boolean;
}

export function KanbanBoard({
  boardId,
  readOnlyExceptDescription = false,
}: KanbanBoardProps) {
  useBoardSocket(boardId);

  const {
    data: board,
    isLoading,
    isError,
    error: boardError,
  } = useBoard(boardId);

  const createCard = useCreateCard(boardId);
  const moveCard = useMoveCard();
  const deleteCard = useDeleteCard();

  const [searchParams, setSearchParams] =
    useSearchParams();

  const requestedCardId =
    searchParams.get("card");

  const [activeCard, setActiveCard] =
    useState<Card | null>(null);

  const [openCardId, setOpenCardId] =
    useState<string | null>(requestedCardId);

  const [previousRequestedCardId, setPreviousRequestedCardId] =
    useState<string | null>(requestedCardId);

  if (requestedCardId !== previousRequestedCardId) {
    setPreviousRequestedCardId(requestedCardId);
    setOpenCardId(requestedCardId);
  }

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 6,
      },
    }),
  );

  const mutationError =
    createCard.isError ||
    moveCard.isError ||
    deleteCard.isError
      ? "The card operation failed. Please try again."
      : null;

  const isMutating =
    createCard.isPending ||
    moveCard.isPending ||
    deleteCard.isPending;

  const mutationStatus = createCard.isPending
    ? "Creating card…"
    : moveCard.isPending
      ? "Moving card…"
      : deleteCard.isPending
        ? "Deleting card…"
        : "";

  function handleDragStart(event: DragStartEvent) {
    if (moveCard.isPending) {
      return;
    }

    const activeData = event.active.data.current;

    if (activeData?.type !== "card") {
      return;
    }

    setActiveCard(activeData.card as Card);
  }

  function handleDragCancel() {
    setActiveCard(null);
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveCard(null);

    if (moveCard.isPending) {
      return;
    }

    const { active, over } = event;

    if (!over) {
      return;
    }

    const activeData = active.data.current;

    if (activeData?.type !== "card") {
      return;
    }

    const draggedCard = activeData.card as Card;
    const overData = over.data.current;

    const targetColumnId =
      overData?.type === "column"
        ? String(over.id)
        : overData?.type === "card"
          ? (overData.card as Card).column_id
          : null;

    if (!targetColumnId || !board) {
      return;
    }

    const sourceColumn = board.columns.find(
      (column) => column.id === draggedCard.column_id,
    );

    const targetColumn = board.columns.find(
      (column) => column.id === targetColumnId,
    );

    if (!targetColumn) {
      return;
    }

    const targetSiblings = targetColumn.cards
      .filter((card) => card.id !== draggedCard.id)
      .sort((left, right) =>
        left.rank.localeCompare(right.rank),
      );

    let targetIndex = targetSiblings.length;

    if (overData?.type === "card") {
      const overCard = overData.card as Card;

      const overIndex = targetSiblings.findIndex(
        (card) => card.id === overCard.id,
      );

      if (overIndex >= 0) {
        targetIndex = overIndex;
      }
    }

    const previousCardId =
      targetSiblings[targetIndex - 1]?.id ?? null;

    const nextCardId =
      targetSiblings[targetIndex]?.id ?? null;

    if (
      sourceColumn &&
      draggedCard.column_id === targetColumnId
    ) {
      const sourceCards = [...sourceColumn.cards].sort(
        (left, right) =>
          left.rank.localeCompare(right.rank),
      );

      const currentIndex = sourceCards.findIndex(
        (card) => card.id === draggedCard.id,
      );

      if (currentIndex >= 0) {
        const currentPreviousCardId =
          sourceCards[currentIndex - 1]?.id ?? null;

        const currentNextCardId =
          sourceCards[currentIndex + 1]?.id ?? null;

        if (
          currentPreviousCardId === previousCardId &&
          currentNextCardId === nextCardId
        ) {
          return;
        }
      }
    }

    moveCard.reset();

    moveCard.mutate({
      cardId: draggedCard.id,
      boardId,
      payload: {
        target_column_id: targetColumnId,
        previous_card_id: previousCardId,
        next_card_id: nextCardId,
      },
    });
  }

  async function handleAddCard(
    columnId: string,
    title: string,
  ): Promise<void> {
    if (createCard.isPending) {
      return;
    }

    const normalizedTitle = title.trim();

    if (!normalizedTitle) {
      return;
    }

    createCard.reset();

    await createCard.mutateAsync({
      columnId,
      input: {
        title: normalizedTitle,
      },
    });
  }

  function handleOpenCard(cardId: string) {
    const next = new URLSearchParams(searchParams);
    next.set("card", cardId);
    setSearchParams(next, { replace: true });
  }

  function closeCard() {
    const next = new URLSearchParams(searchParams);
    next.delete("card");
    setSearchParams(next, { replace: true });
  }

  function handleDeleteCard(card: Card) {
    if (deleteCard.isPending) {
      return;
    }

    const confirmed = window.confirm(
      `Delete "${card.title}"?`,
    );

    if (!confirmed) {
      return;
    }

    if (openCardId === card.id) {
      closeCard();
    }

    deleteCard.reset();

    deleteCard.mutate({
      cardId: card.id,
      boardId,
    });
  }

  if (isLoading) {
    return (
      <p className="text-sm text-slate-400">
        Loading board…
      </p>
    );
  }

  if (isError) {
    console.error(
      "Unable to load the board:",
      boardError,
    );

    return (
      <p
        role="alert"
        className="rounded-lg border border-red-900 bg-red-950/40 p-3 text-sm text-red-300"
      >
        Unable to load the board.
      </p>
    );
  }

  if (!board) {
    return (
      <p
        role="alert"
        className="rounded-lg border border-amber-900 bg-amber-950/40 p-3 text-sm text-amber-300"
      >
        Board not found.
      </p>
    );
  }

  if (!Array.isArray(board.columns)) {
    console.error(
      "Invalid board response: expected board.columns to be an array.",
      board,
    );

    return (
      <p
        role="alert"
        className="rounded-lg border border-red-900 bg-red-950/40 p-3 text-sm text-red-300"
      >
        The board response is invalid: its columns were not included.
      </p>
    );
  }

  const columns = board.columns;

  const openCard =
    openCardId === null
      ? null
      : columns
          .flatMap((column) => column.cards)
          .find((card) => card.id === openCardId) ?? null;

  return (
    <>
      {mutationError ? (
        <div
          role="alert"
          className="fixed bottom-4 left-1/2 z-[100] max-w-[calc(100vw-2rem)] -translate-x-1/2 rounded-lg border border-red-800 bg-red-950 px-4 py-3 text-sm font-medium text-red-200 shadow-xl"
        >
          {mutationError}
        </div>
      ) : null}

      {isMutating ? (
        <div
          aria-live="polite"
          aria-atomic="true"
          className="pointer-events-none fixed bottom-4 right-4 z-[99] rounded-lg border border-slate-600 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-200 shadow-xl"
        >
          {mutationStatus}
        </div>
      ) : null}

      {columns.length === 0 ? (
        <div className="mb-4 rounded-lg border border-dashed border-slate-700 p-6 text-center">
          <p className="text-sm text-slate-300">
            This board does not have any columns yet.
          </p>
        </div>
      ) : null}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragCancel={handleDragCancel}
        onDragEnd={handleDragEnd}
      >
        <div className="kanban-board" aria-busy={isMutating}>
          {columns.map((column) => (
            <ColumnLane
              key={column.id}
              column={column}
              onOpenCard={(card) => handleOpenCard(card.id)}
              onAddCard={handleAddCard}
              onDeleteCard={handleDeleteCard}
              isAddingCard={createCard.isPending}
            />
          ))}
        </div>

        <DragOverlay dropAnimation={null}>
          {activeCard ? <CardPreview card={activeCard} /> : null}
        </DragOverlay>
      </DndContext>

      {openCard ? (
        <CardModal
          key={openCard.id}
          boardId={boardId}
          card={openCard}
          onClose={closeCard}
          onDelete={handleDeleteCard}
          readOnlyExceptDescription={
            readOnlyExceptDescription
          }
        />
      ) : null}
    </>
  );
}
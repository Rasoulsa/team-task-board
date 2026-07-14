import type {
  BoardDetail,
  Card,
  MoveCardInput,
} from "../domain/types";

export function applyMove(
  board: BoardDetail,
  cardId: string,
  payload: MoveCardInput,
): BoardDetail {
  let cardToMove: Card | undefined;

  for (const column of board.columns) {
    const card = column.cards.find(
      (candidate) => candidate.id === cardId,
    );

    if (card) {
      cardToMove = card;
      break;
    }
  }

  if (!cardToMove) {
    return board;
  }

  const targetColumnExists = board.columns.some(
    (column) =>
      column.id === payload.target_column_id,
  );

  if (!targetColumnExists) {
    return board;
  }

  return {
    ...board,

    columns: board.columns.map((column) => {
      const cardsWithoutMoved =
        column.cards.filter(
          (card) => card.id !== cardId,
        );

      if (
        column.id !== payload.target_column_id
      ) {
        return {
          ...column,
          cards: cardsWithoutMoved,
        };
      }

      const insertionIndex =
        resolveInsertionIndex(
          cardsWithoutMoved,
          payload,
        );

      /*
       * The optimistic rank is temporary. The server returns the
       * authoritative rank after completing the move.
       */
      const previousRank =
        cardsWithoutMoved[insertionIndex - 1]
          ?.rank ?? null;

      const nextRank =
        cardsWithoutMoved[insertionIndex]?.rank ??
        null;

      const optimisticRank = midpointRank(
        previousRank,
        nextRank,
      );

      const movedCard: Card = {
        ...cardToMove,
        column_id: payload.target_column_id,
        rank: optimisticRank,
      };

      const nextCards = [
        ...cardsWithoutMoved.slice(
          0,
          insertionIndex,
        ),
        movedCard,
        ...cardsWithoutMoved.slice(
          insertionIndex,
        ),
      ];

      return {
        ...column,
        cards: nextCards,
      };
    }),
  };
}

function resolveInsertionIndex(
  cards: Card[],
  payload: MoveCardInput,
): number {
  if (payload.previous_card_id) {
    const previousIndex = cards.findIndex(
      (card) =>
        card.id === payload.previous_card_id,
    );

    if (previousIndex >= 0) {
      return previousIndex + 1;
    }
  }

  if (payload.next_card_id) {
    const nextIndex = cards.findIndex(
      (card) =>
        card.id === payload.next_card_id,
    );

    if (nextIndex >= 0) {
      return nextIndex;
    }
  }

  return cards.length;
}

/**
 * Produces a temporary optimistic rank.
 *
 * The server-generated rank remains authoritative and replaces this
 * value when the move request succeeds.
 */
function midpointRank(
  previous: string | null,
  next: string | null,
): string {
  if (previous && next) {
    if (previous < next) {
      return `${previous}m`;
    }

    return previous;
  }

  if (previous && !next) {
    return `${previous}z`;
  }

  if (!previous && next) {
    return next.slice(0, -1);
  }

  return "m";
}
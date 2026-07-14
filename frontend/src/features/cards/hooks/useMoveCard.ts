import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import { applyMove } from "../application/applyMove";
import type {
  BoardDetail,
  Card,
  MoveCardInput,
  MoveCardResult,
} from "../domain/types";
import { cardQueryKeys } from "./queryKeys";

interface MoveCardVariables {
  cardId: string;
  boardId: string;
  payload: MoveCardInput;
}

interface MoveCardContext {
  previousBoard: BoardDetail | undefined;
}

export function useMoveCard() {
  const queryClient = useQueryClient();

  return useMutation<
    MoveCardResult,
    Error,
    MoveCardVariables,
    MoveCardContext
  >({
    mutationFn: ({ cardId, payload }) =>
      container.cardService.moveCard(
        cardId,
        payload,
      ),

    onMutate: async (
      variables,
    ): Promise<MoveCardContext> => {
      const queryKey = cardQueryKeys.board(
        variables.boardId,
      );

      await queryClient.cancelQueries({
        queryKey,
      });

      const previousBoard =
        queryClient.getQueryData<BoardDetail>(
          queryKey,
        );

      if (previousBoard) {
        const optimisticBoard = applyMove(
          previousBoard,
          variables.cardId,
          variables.payload,
        );

        queryClient.setQueryData<BoardDetail>(
          queryKey,
          optimisticBoard,
        );
      }

      return { previousBoard };
    },

    onSuccess: (moveResult, variables) => {
      const queryKey = cardQueryKeys.board(
        variables.boardId,
      );

      const currentBoard =
        queryClient.getQueryData<BoardDetail>(
          queryKey,
        );

      if (!currentBoard) {
        return;
      }

      /*
       * After the optimistic update, the complete card should already
       * be in the target column. Use that card as the base and merge
       * authoritative fields returned by the server.
       */
      const cachedCard = currentBoard.columns
        .flatMap((column) => column.cards)
        .find(
          (card) =>
            card.id === variables.cardId,
        );

      if (!cachedCard) {
        /*
         * The optimistic card is unexpectedly absent. Refetching is
         * safer than inserting an incomplete move result.
         */
        void queryClient.invalidateQueries({
          queryKey,
        });

        return;
      }

      const completeMovedCard: Card = {
        ...cachedCard,
        ...moveResult,

        id: moveResult.id,
        column_id: moveResult.column_id,
        rank: moveResult.rank,

        /*
         * If the move response omitted a relationship, preserve the
         * relationship already held by the cached complete card.
         */
        labels: Array.isArray(moveResult.labels)
          ? moveResult.labels
          : cachedCard.labels,

        assignees: Array.isArray(
          moveResult.assignees,
        )
          ? moveResult.assignees
          : cachedCard.assignees,

        checklist: Array.isArray(
          moveResult.checklist,
        )
          ? moveResult.checklist
          : cachedCard.checklist,
      };

      const targetColumnExists =
        currentBoard.columns.some(
          (column) =>
            column.id ===
            completeMovedCard.column_id,
        );

      if (!targetColumnExists) {
        void queryClient.invalidateQueries({
          queryKey,
        });

        return;
      }

      const reconciledBoard: BoardDetail = {
        ...currentBoard,

        columns: currentBoard.columns.map(
          (column) => {
            /*
             * Remove the card from every column first. This prevents
             * duplicate cards after an optimistic move.
             */
            const withoutMoved =
              column.cards.filter(
                (card) =>
                  card.id !== variables.cardId,
              );

            if (
              column.id !==
              completeMovedCard.column_id
            ) {
              return {
                ...column,
                cards: withoutMoved,
              };
            }

            /*
             * Insert exactly one reconciled card into the server's
             * authoritative target column and sort by server rank.
             */
            const nextCards = [
              ...withoutMoved,
              completeMovedCard,
            ].sort((left, right) =>
              left.rank.localeCompare(right.rank),
            );

            return {
              ...column,
              cards: nextCards,
            };
          },
        ),
      };

      queryClient.setQueryData<BoardDetail>(
        queryKey,
        reconciledBoard,
      );
    },

    onError: (_error, variables, context) => {
      if (!context?.previousBoard) {
        return;
      }

      queryClient.setQueryData<BoardDetail>(
        cardQueryKeys.board(
          variables.boardId,
        ),
        context.previousBoard,
      );
    },
  });
}
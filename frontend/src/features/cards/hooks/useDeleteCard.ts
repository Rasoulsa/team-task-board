import { useMutation, useQueryClient } from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import type { BoardDetail } from "../domain/types";
import { cardQueryKeys } from "./queryKeys";

interface DeleteCardVariables {
  cardId: string;
  boardId: string;
}

interface DeleteCardContext {
  previousBoard: BoardDetail | undefined;
}

export function useDeleteCard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ cardId }: DeleteCardVariables) =>
      container.cardService.deleteCard(cardId),

    onMutate: async (
      variables: DeleteCardVariables,
    ): Promise<DeleteCardContext> => {
      const queryKey = cardQueryKeys.board(variables.boardId);

      await queryClient.cancelQueries({ queryKey });

      const previousBoard =
        queryClient.getQueryData<BoardDetail>(queryKey);

      if (previousBoard) {
        const optimisticBoard: BoardDetail = {
          ...previousBoard,
          columns: previousBoard.columns.map((column) => ({
            ...column,
            cards: column.cards.filter(
              (card) => card.id !== variables.cardId,
            ),
          })),
        };

        queryClient.setQueryData<BoardDetail>(
          queryKey,
          optimisticBoard,
        );
      }

      return { previousBoard };
    },

    onError: (_error, variables, context) => {
      if (!context?.previousBoard) {
        return;
      }

      queryClient.setQueryData<BoardDetail>(
        cardQueryKeys.board(variables.boardId),
        context.previousBoard,
      );
    },

    onSettled: async (_data, _error, variables) => {
      await queryClient.invalidateQueries({
        queryKey: cardQueryKeys.board(variables.boardId),
      });
    },
  });
}
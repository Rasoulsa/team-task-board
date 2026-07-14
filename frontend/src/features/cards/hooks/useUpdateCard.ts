import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import type { UpdateCardInput } from "../domain/types";
import { cardQueryKeys } from "./queryKeys";

interface UpdateCardVariables {
  cardId: string;
  payload: UpdateCardInput;
}

export function useUpdateCard(boardId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      cardId,
      payload,
    }: UpdateCardVariables) =>
      container.cardService.updateCard(
        cardId,
        payload,
      ),

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: cardQueryKeys.board(boardId),
      });
    },
  });
}
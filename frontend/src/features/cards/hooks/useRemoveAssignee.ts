import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import { cardQueryKeys } from "./queryKeys";

interface RemoveAssigneeVariables {
  cardId: string;
  userId: string;
}

export function useRemoveAssignee(
  boardId: string,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      cardId,
      userId,
    }: RemoveAssigneeVariables) =>
      container.cardService.removeAssignee(
        cardId,
        userId,
      ),

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: cardQueryKeys.board(boardId),
      });
    },
  });
}
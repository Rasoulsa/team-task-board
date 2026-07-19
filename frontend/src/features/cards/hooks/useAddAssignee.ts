import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import { cardQueryKeys } from "./queryKeys";

interface AddAssigneeVariables {
  cardId: string;
  userId: string;
}

export function useAddAssignee(boardId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      cardId,
      userId,
    }: AddAssigneeVariables) =>
      container.cardService.addAssignee(
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
import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import type { CreateCardInput } from "../domain/types";
import { cardQueryKeys } from "./queryKeys";

interface CreateCardVariables {
  columnId: string;
  input: CreateCardInput;
}

export function useCreateCard(boardId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      columnId,
      input,
    }: CreateCardVariables) =>
      container.cardService.createCard(
        columnId,
        input,
      ),

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: cardQueryKeys.board(boardId),
      });
    },
  });
}
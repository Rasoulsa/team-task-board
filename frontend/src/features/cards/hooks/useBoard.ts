import { useQuery } from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import { cardQueryKeys } from "./queryKeys";

export function useBoard(boardId: string) {
  return useQuery({
    queryKey: cardQueryKeys.board(boardId),
    queryFn: () =>
      container.cardService.getBoard(boardId),
    enabled: Boolean(boardId),
  });
}
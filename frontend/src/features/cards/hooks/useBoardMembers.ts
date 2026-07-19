import { useQuery } from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import { cardQueryKeys } from "./queryKeys";

export function useBoardMembers(boardId: string) {
  return useQuery({
    queryKey: cardQueryKeys.boardMembers(boardId),
    queryFn: () =>
      container.boardService.listMembers(boardId),
    enabled: Boolean(boardId),
  });
}
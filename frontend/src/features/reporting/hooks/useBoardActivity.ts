import { useInfiniteQuery } from "@tanstack/react-query";
import { HttpActivityRepository } from "../data/HttpActivityRepository";
import { ActivityService } from "../application/ActivityService";

const activityService = new ActivityService(new HttpActivityRepository());

export function useBoardActivity(boardId: string, limit = 20) {
  return useInfiniteQuery({
    queryKey: ["board-activity", boardId, limit],
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      activityService.getBoardActivity(boardId, {
        cursor: pageParam,
        limit,
      }),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: Boolean(boardId),
  });
}
import { useQuery } from "@tanstack/react-query";
import { HttpStatsRepository } from "../data/HttpStatsRepository";
import { StatsService } from "../application/StatsService";

const statsService = new StatsService(new HttpStatsRepository());

export function useBoardStats(boardId: string) {
  return useQuery({
    queryKey: ["board-stats", boardId],
    queryFn: () => statsService.getBoardStats(boardId),
    enabled: Boolean(boardId),
  });
}
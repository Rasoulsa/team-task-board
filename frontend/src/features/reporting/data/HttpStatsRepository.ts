import { apiClient } from "../../../core/http/client";
import type { StatsRepository } from "../domain/StatsRepository";
import type { BoardStats } from "../domain/types";

export class HttpStatsRepository implements StatsRepository {
  async getBoardStats(boardId: string): Promise<BoardStats> {
    const response = await apiClient.get<BoardStats>(
      `/boards/${boardId}/stats`,
    );
    return response.data;
  }
}
import type { BoardStats } from "./types";

export interface StatsRepository {
  getBoardStats(boardId: string): Promise<BoardStats>;
}
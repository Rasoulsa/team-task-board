import type { StatsRepository } from "../domain/StatsRepository";
import type { BoardStats } from "../domain/types";

export class StatsService {
  private readonly statsRepository: StatsRepository;

  constructor(statsRepository: StatsRepository) {
    this.statsRepository = statsRepository;
  }

  getBoardStats(boardId: string): Promise<BoardStats> {
    return this.statsRepository.getBoardStats(boardId);
  }
}
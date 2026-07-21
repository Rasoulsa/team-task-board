import { describe, expect, it, vi } from "vitest";
import { StatsService } from "./StatsService";
import type { StatsRepository } from "../domain/StatsRepository";
import type { BoardStats } from "../domain/types";

describe("StatsService", () => {
  it("delegates getBoardStats to the repository", async () => {
    const stats: BoardStats = {
      board_id: "b1",
      totals: { open_count: 3, closed_count: 1, overdue_count: 0, total_count: 4 },
      per_member: [],
    };
    const repo: StatsRepository = {
      getBoardStats: vi.fn().mockResolvedValue(stats),
    };
    const service = new StatsService(repo);

    const result = await service.getBoardStats("b1");

    expect(repo.getBoardStats).toHaveBeenCalledWith("b1");
    expect(result).toEqual(stats);
  });
});
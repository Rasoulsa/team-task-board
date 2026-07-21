import type { ActivityPage } from "./types";

export interface ActivityRepository {
  getBoardActivity(
    boardId: string,
    params: { cursor?: string; limit?: number },
  ): Promise<ActivityPage>;
}
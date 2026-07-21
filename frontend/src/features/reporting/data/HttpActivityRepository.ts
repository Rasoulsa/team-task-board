import { apiClient } from "../../../core/http/client";
import type { ActivityRepository } from "../domain/ActivityRepository";
import type { ActivityPage } from "../domain/types";

export class HttpActivityRepository implements ActivityRepository {
  async getBoardActivity(
    boardId: string,
    params: { cursor?: string; limit?: number },
  ): Promise<ActivityPage> {
    const response = await apiClient.get<ActivityPage>(
      `/boards/${boardId}/activity`,
      { params },
    );
    return response.data;
  }
}
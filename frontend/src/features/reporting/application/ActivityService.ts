import type { ActivityRepository } from "../domain/ActivityRepository";
import type { ActivityPage } from "../domain/types";

export class ActivityService {
  private readonly activityRepository: ActivityRepository;

  constructor(activityRepository: ActivityRepository) {
    this.activityRepository = activityRepository;
  }

  getBoardActivity(
    boardId: string,
    params: { cursor?: string; limit?: number } = {},
  ): Promise<ActivityPage> {
    return this.activityRepository.getBoardActivity(boardId, params);
  }
}
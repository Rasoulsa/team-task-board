import { axiosClient } from "../../../core/http/axiosClient";
import type { NotificationRepository } from "../domain/NotificationRepository";
import type { AppNotification } from "../domain/types";
import type { NotificationDto, UnreadCountDto } from "./notificationApiTypes";
import { mapNotificationList } from "./notificationResponseMapper";

export class HttpNotificationRepository implements NotificationRepository {
  async list(limit = 20, offset = 0): Promise<AppNotification[]> {
    const { data } = await axiosClient.get<NotificationDto[]>(
      "/notifications",
      { params: { limit, offset } },
    );
    return mapNotificationList(data);
  }

  async unreadCount(): Promise<number> {
    const { data } = await axiosClient.get<UnreadCountDto>(
      "/notifications/unread-count",
    );
    return data.unread_count;
  }

  async markRead(id: string): Promise<void> {
    await axiosClient.post(`/notifications/${id}/read`);
  }

  async markAllRead(): Promise<void> {
    await axiosClient.post("/notifications/read-all");
  }
}
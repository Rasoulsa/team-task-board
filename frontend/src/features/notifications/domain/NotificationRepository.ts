import type { AppNotification } from "./types";

export interface NotificationRepository {
  list(limit?: number, offset?: number): Promise<AppNotification[]>;
  unreadCount(): Promise<number>;
  markRead(id: string): Promise<void>;
  markAllRead(): Promise<void>;
}
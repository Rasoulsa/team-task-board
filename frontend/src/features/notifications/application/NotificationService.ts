import type { NotificationRepository } from "../domain/NotificationRepository";
import type { AppNotification } from "../domain/types";

export class NotificationService {
  private readonly repository: NotificationRepository;

  constructor(repository: NotificationRepository) {
    this.repository = repository;
  }

  async list(limit = 20, offset = 0): Promise<AppNotification[]> {
    return this.repository.list(limit, offset);
  }

  async unreadCount(): Promise<number> {
    return this.repository.unreadCount();
  }

  async markRead(id: string): Promise<void> {
    return this.repository.markRead(id);
  }

  async markAllRead(): Promise<void> {
    return this.repository.markAllRead();
  }
}
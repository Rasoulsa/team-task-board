import { describe, expect, it, vi } from "vitest";

import type { NotificationRepository } from "../domain/NotificationRepository";
import type { AppNotification } from "../domain/types";
import { NotificationService } from "./NotificationService";

function createMockRepository(): NotificationRepository {
  return {
    list: vi.fn(),
    unreadCount: vi.fn(),
    markRead: vi.fn(),
    markAllRead: vi.fn(),
  };
}

describe("NotificationService", () => {
  it("delegates list() to the repository with given params", async () => {
    const repo = createMockRepository();
    const notif: AppNotification = {
      id: "n1",
      type: "card_assigned",
      title: "t",
      body: "b",
      boardId: null,
      cardId: null,
      isRead: false,
      createdAt: "2026-07-16T10:00:00Z",
    };
    vi.mocked(repo.list).mockResolvedValueOnce([notif]);

    const service = new NotificationService(repo);
    const result = await service.list(10, 5);

    expect(repo.list).toHaveBeenCalledWith(10, 5);
    expect(result).toEqual([notif]);
  });

  it("delegates unreadCount() to the repository", async () => {
    const repo = createMockRepository();
    vi.mocked(repo.unreadCount).mockResolvedValueOnce(3);

    const service = new NotificationService(repo);
    expect(await service.unreadCount()).toBe(3);
  });

  it("delegates markRead(id) to the repository", async () => {
    const repo = createMockRepository();
    const service = new NotificationService(repo);

    await service.markRead("n1");
    expect(repo.markRead).toHaveBeenCalledWith("n1");
  });

  it("delegates markAllRead() to the repository", async () => {
    const repo = createMockRepository();
    const service = new NotificationService(repo);

    await service.markAllRead();
    expect(repo.markAllRead).toHaveBeenCalledTimes(1);
  });
});
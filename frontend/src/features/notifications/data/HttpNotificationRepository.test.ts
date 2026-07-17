import { beforeEach, describe, expect, it, vi } from "vitest";

import { axiosClient } from "../../../core/http/axiosClient";
import { HttpNotificationRepository } from "./HttpNotificationRepository";

vi.mock("../../../core/http/axiosClient", () => ({
  axiosClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("HttpNotificationRepository", () => {
  const repo = new HttpNotificationRepository();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("maps list() response to domain notifications", async () => {
    vi.mocked(axiosClient.get).mockResolvedValueOnce({
      data: [
        {
          id: "n1",
          type: "card_assigned",
          title: "Assigned",
          body: "body",
          board_id: "b1",
          card_id: "c1",
          is_read: false,
          created_at: "2026-07-16T10:00:00Z",
        },
      ],
    });

    const result = await repo.list();

    expect(axiosClient.get).toHaveBeenCalledWith("/notifications", {
      params: {
        limit: 20,
        offset: 0,
      },
    });

    expect(result).toEqual([
      {
        id: "n1",
        type: "card_assigned",
        title: "Assigned",
        body: "body",
        boardId: "b1",
        cardId: "c1",
        isRead: false,
        createdAt: "2026-07-16T10:00:00Z",
      },
    ]);
  });

  it("returns unread_count as a number", async () => {
    vi.mocked(axiosClient.get).mockResolvedValueOnce({
      data: { unread_count: 5 },
    });

    expect(await repo.unreadCount()).toBe(5);

    expect(axiosClient.get).toHaveBeenCalledWith(
      "/notifications/unread-count",
    );
  });

  it("posts to /read for markRead", async () => {
    vi.mocked(axiosClient.post).mockResolvedValueOnce({
      data: undefined,
    });

    await repo.markRead("n1");

    expect(axiosClient.post).toHaveBeenCalledWith(
      "/notifications/n1/read",
    );
  });

  it("posts to /read-all for markAllRead", async () => {
    vi.mocked(axiosClient.post).mockResolvedValueOnce({
      data: undefined,
    });

    await repo.markAllRead();

    expect(axiosClient.post).toHaveBeenCalledWith(
      "/notifications/read-all",
    );
  });
});
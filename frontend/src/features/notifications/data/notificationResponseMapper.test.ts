import { describe, expect, it } from "vitest";

import type { NotificationDto } from "./notificationApiTypes";
import { mapNotificationDto } from "./notificationResponseMapper";

describe("mapNotificationDto", () => {
  it("maps snake_case API fields to camelCase domain fields", () => {
    const dto: NotificationDto = {
      id: "n1",
      type: "card_assigned",
      title: "You were assigned",
      body: "Card X was assigned to you",
      board_id: "b1",
      card_id: "c1",
      is_read: false,
      created_at: "2026-07-16T10:00:00Z",
    };

    expect(mapNotificationDto(dto)).toEqual({
      id: "n1",
      type: "card_assigned",
      title: "You were assigned",
      body: "Card X was assigned to you",
      boardId: "b1",
      cardId: "c1",
      isRead: false,
      createdAt: "2026-07-16T10:00:00Z",
    });
  });
});
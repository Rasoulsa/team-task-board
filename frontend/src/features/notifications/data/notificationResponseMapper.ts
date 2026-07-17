import type { AppNotification } from "../domain/types";
import type { NotificationDto } from "./notificationApiTypes";

export function mapNotificationDto(dto: NotificationDto): AppNotification {
  return {
    id: dto.id,
    type: dto.type,
    title: dto.title,
    body: dto.body,
    boardId: dto.board_id,
    cardId: dto.card_id,
    isRead: dto.is_read,
    createdAt: dto.created_at,
  };
}

export function mapNotificationList(
  dtos: NotificationDto[],
): AppNotification[] {
  return dtos.map(mapNotificationDto);
}
export type NotificationTypeDto =
  | "card_assigned"
  | "card_mentioned"
  | "due_date_reminder";

export interface NotificationDto {
  id: string;
  type: NotificationTypeDto;
  title: string;
  body: string;
  board_id: string | null;
  card_id: string | null;
  is_read: boolean;
  created_at: string;
}

export interface UnreadCountDto {
  unread_count: number;
}
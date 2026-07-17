export type NotificationType =
  | "card_assigned"
  | "card_mentioned"
  | "due_date_reminder";

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  boardId: string | null;
  cardId: string | null;
  isRead: boolean;
  createdAt: string;
}
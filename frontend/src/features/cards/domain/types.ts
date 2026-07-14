export type CardPriority =
  | "low"
  | "medium"
  | "high"
  | "urgent";

export interface CardLabel {
  id: string;
  name: string;
  color: string;
}

export interface CardAssignee {
  id: string;
  user_id: string;
}

export interface ChecklistItem {
  id: string;
  content: string;
  is_done: boolean;
  position?: number;
}

export interface Card {
  id: string;
  column_id: string;
  title: string;
  description: string | null;
  priority: CardPriority;
  due_date: string | null;
  rank: string;
  labels: CardLabel[];
  assignees: CardAssignee[];
  checklist: ChecklistItem[];
  is_deleted: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * Domain-level result of moving a card.
 *
 * The backend must return the authoritative id, column and rank,
 * but it may omit other card properties.
 *
 * This domain type uses `checklist`, never `checklist_items`.
 */
export type MoveCardResult = Pick<
  Card,
  "id" | "column_id" | "rank"
> &
  Partial<
    Omit<Card, "id" | "column_id" | "rank">
  >;

export interface Column {
  id: string;
  board_id: string;
  name: string;
  position: number;
  cards: Card[];
  created_at?: string;
  updated_at?: string;
}

export interface BoardDetail {
  id: string;
  name: string;
  description?: string | null;
  project_id?: string;
  columns: Column[];
  created_at?: string;
  updated_at?: string;
}

// Matches backend CardCreate (server assigns rank).
export interface CreateCardInput {
  title: string;
  description?: string | null;
  priority?: CardPriority;
  due_date?: string | null;
}

export interface UpdateCardInput {
  title?: string;
  description?: string | null;
  priority?: CardPriority;
  due_date?: string | null;
}

// Matches backend CardMove (server computes rank from neighbors).
export interface MoveCardInput {
  target_column_id: string;
  previous_card_id?: string | null;
  next_card_id?: string | null;
}
export interface MemberCardStats {
  user_id: string;
  full_name: string;
  email: string;
  open_count: number;
  closed_count: number;
  overdue_count: number;
}

export interface BoardTotals {
  open_count: number;
  closed_count: number;
  overdue_count: number;
  total_count: number;
}

export interface BoardStats {
  board_id: string;
  totals: BoardTotals;
  per_member: MemberCardStats[];
}

export interface ActivityItem {
  id: string;
  board_id: string;
  actor_id: string | null;
  actor_name: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  meta: Record<string, unknown>;
  created_at: string;
}

export interface ActivityPage {
  items: ActivityItem[];
  next_cursor: string | null;
}
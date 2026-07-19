export type Board = {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type BoardMemberRole =
  | "owner"
  | "admin"
  | "member"
  | "viewer";

export type BoardMember = {
  id: string;
  user_id: string;
  organization_id: string;
  full_name: string;
  email: string;
  role: BoardMemberRole;
  created_at: string;
};

export type BoardColumn = {
  id: string;
  board_id: string;
  name: string;
  position: number;
  created_at: string;
  updated_at: string;
};

export type CreateBoardInput = {
  name: string;
  description?: string | null;
};

export type UpdateBoardInput = {
  name?: string;
  description?: string | null;
};

export type CreateColumnInput = {
  name: string;
  position?: number | null;
};
import type {
  BoardDetail,
  Card,
  Column,
} from "../domain/types";

/**
 * Raw card returned by endpoints that return a complete card.
 *
 * The backend currently uses `checklist_items`; the frontend domain
 * uses `checklist`.
 *
 * Relationship arrays are optional because some backend endpoints
 * may omit them.
 */
export type CardApiResponse = Omit<
  Card,
  "labels" | "assignees" | "checklist"
> & {
  labels?: Card["labels"] | null;
  assignees?: Card["assignees"] | null;
  checklist?: Card["checklist"] | null;
  checklist_items?: Card["checklist"] | null;
};

/**
 * Raw response returned by the move endpoint.
 *
 * A move response must contain the authoritative location and rank,
 * but it may omit the rest of the card fields.
 */
export type MoveCardApiResponse = Pick<
  Card,
  "id" | "column_id" | "rank"
> &
  Partial<
    Omit<
      Card,
      | "id"
      | "column_id"
      | "rank"
      | "labels"
      | "assignees"
      | "checklist"
    >
  > & {
    labels?: Card["labels"] | null;
    assignees?: Card["assignees"] | null;
    checklist?: Card["checklist"] | null;
    checklist_items?: Card["checklist"] | null;
  };

/**
 * Raw column contained in the board Kanban response.
 */
export type ColumnApiResponse = Omit<Column, "cards"> & {
  cards?: CardApiResponse[] | null;
};

/**
 * Raw board Kanban response.
 */
export type BoardDetailApiResponse = Omit<
  BoardDetail,
  "columns"
> & {
  columns?: ColumnApiResponse[] | null;
};
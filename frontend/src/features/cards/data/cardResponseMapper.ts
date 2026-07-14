import type {
  BoardDetail,
  Card,
  Column,
  MoveCardResult,
} from "../domain/types";
import type {
  BoardDetailApiResponse,
  CardApiResponse,
  ColumnApiResponse,
  MoveCardApiResponse,
} from "./cardApiTypes";

/**
 * Converts a complete backend card response into the canonical
 * frontend Card domain object.
 *
 * The raw `checklist_items` property is intentionally removed.
 */
export function mapCardResponse(
  response: CardApiResponse,
): Card {
  const {
    checklist_items,
    checklist,
    labels,
    assignees,
    ...card
  } = response;

  return {
    ...card,

    labels: Array.isArray(labels)
      ? labels
      : [],

    assignees: Array.isArray(assignees)
      ? assignees
      : [],

    checklist: Array.isArray(checklist)
      ? checklist
      : Array.isArray(checklist_items)
        ? checklist_items
        : [],
  };
}

/**
 * Converts an optional array of raw cards into domain Cards.
 */
export function mapCardResponses(
  responses: CardApiResponse[] | null | undefined,
): Card[] {
  if (!Array.isArray(responses)) {
    return [];
  }

  return responses.map(mapCardResponse);
}

/**
 * Converts a potentially partial move response into a domain-level
 * move result.
 *
 * Unlike mapCardResponse, omitted relationships remain omitted here.
 * This allows the move hook to preserve relationship data already
 * present on the optimistic cached card.
 */
export function mapMoveCardResponse(
  response: MoveCardApiResponse,
): MoveCardResult {
  const result: MoveCardResult = {
    id: response.id,
    column_id: response.column_id,
    rank: response.rank,
  };

  if (response.title !== undefined) {
    result.title = response.title;
  }

  if (response.description !== undefined) {
    result.description = response.description;
  }

  if (response.priority !== undefined) {
    result.priority = response.priority;
  }

  if (response.due_date !== undefined) {
    result.due_date = response.due_date;
  }

  if (response.is_deleted !== undefined) {
    result.is_deleted = response.is_deleted;
  }

  if (response.created_at !== undefined) {
    result.created_at = response.created_at;
  }

  if (response.updated_at !== undefined) {
    result.updated_at = response.updated_at;
  }

  if (
    Object.prototype.hasOwnProperty.call(
      response,
      "labels",
    )
  ) {
    result.labels = Array.isArray(response.labels)
      ? response.labels
      : [];
  }

  if (
    Object.prototype.hasOwnProperty.call(
      response,
      "assignees",
    )
  ) {
    result.assignees = Array.isArray(
      response.assignees,
    )
      ? response.assignees
      : [];
  }

  const hasChecklist =
    Object.prototype.hasOwnProperty.call(
      response,
      "checklist",
    );

  const hasChecklistItems =
    Object.prototype.hasOwnProperty.call(
      response,
      "checklist_items",
    );

  if (hasChecklist || hasChecklistItems) {
    result.checklist = Array.isArray(
      response.checklist,
    )
      ? response.checklist
      : Array.isArray(response.checklist_items)
        ? response.checklist_items
        : [];
  }

  return result;
}

function mapColumnResponse(
  response: ColumnApiResponse,
): Column {
  return {
    id: response.id,
    board_id: response.board_id,
    name: response.name,
    position: response.position,
    cards: mapCardResponses(response.cards),
    created_at: response.created_at,
    updated_at: response.updated_at,
  };
}

/**
 * Converts the complete board/Kanban response and normalizes every
 * nested card before the result reaches React Query.
 */
export function mapBoardDetailResponse(
  response: BoardDetailApiResponse,
): BoardDetail {
  return {
    id: response.id,
    name: response.name,
    description: response.description ?? null,
    project_id: response.project_id,

    columns: Array.isArray(response.columns)
      ? response.columns.map(mapColumnResponse)
      : [],

    created_at: response.created_at,
    updated_at: response.updated_at,
  };
}
import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  CardApiResponse,
  MoveCardApiResponse,
} from "./cardApiTypes";
import {
  mapBoardDetailResponse,
  mapCardResponse,
  mapMoveCardResponse,
} from "./cardResponseMapper";

function makeCardResponse(
  overrides: Partial<CardApiResponse> = {},
): CardApiResponse {
  return {
    id: "card-1",
    column_id: "column-1",
    title: "Test card",
    description: null,
    priority: "medium",
    due_date: null,
    rank: "m",
    labels: [],
    assignees: [],
    checklist_items: [],
    is_deleted: false,
    created_at: "2026-07-14T00:00:00Z",
    updated_at: "2026-07-14T00:00:00Z",
    ...overrides,
  };
}

describe("cardResponseMapper", () => {
  it("maps checklist_items to checklist", () => {
    const result = mapCardResponse(
      makeCardResponse({
        checklist_items: [
          {
            id: "item-1",
            content: "Write tests",
            is_done: false,
            position: 0,
          },
        ],
      }),
    );

    expect(result.checklist).toEqual([
      {
        id: "item-1",
        content: "Write tests",
        is_done: false,
        position: 0,
      },
    ]);

    expect(result).not.toHaveProperty(
      "checklist_items",
    );
  });

  it("normalizes omitted relationships", () => {
    const result = mapCardResponse(
      makeCardResponse({
        labels: undefined,
        assignees: undefined,
        checklist: undefined,
        checklist_items: undefined,
      }),
    );

    expect(result.labels).toEqual([]);
    expect(result.assignees).toEqual([]);
    expect(result.checklist).toEqual([]);
  });

  it("prefers checklist over checklist_items", () => {
    const result = mapCardResponse(
      makeCardResponse({
        checklist: [
          {
            id: "canonical-item",
            content: "Canonical",
            is_done: true,
          },
        ],
        checklist_items: [
          {
            id: "backend-item",
            content: "Backend",
            is_done: false,
          },
        ],
      }),
    );

    expect(result.checklist[0]?.id).toBe(
      "canonical-item",
    );
  });

  it("keeps omitted move relationships omitted", () => {
    const response: MoveCardApiResponse = {
      id: "card-1",
      column_id: "column-2",
      rank: "n",
    };

    const result =
      mapMoveCardResponse(response);

    expect(result).toEqual({
      id: "card-1",
      column_id: "column-2",
      rank: "n",
    });

    expect(result.labels).toBeUndefined();
    expect(result.assignees).toBeUndefined();
    expect(result.checklist).toBeUndefined();
  });

  it("normalizes checklist_items in a move response", () => {
    const result = mapMoveCardResponse({
      id: "card-1",
      column_id: "column-2",
      rank: "n",
      checklist_items: [
        {
          id: "item-1",
          content: "Move test",
          is_done: false,
        },
      ],
    });

    expect(result.checklist).toEqual([
      {
        id: "item-1",
        content: "Move test",
        is_done: false,
      },
    ]);

    expect(result).not.toHaveProperty(
      "checklist_items",
    );
  });

  it("normalizes cards nested inside a board", () => {
    const board = mapBoardDetailResponse({
      id: "board-1",
      name: "Board",
      columns: [
        {
          id: "column-1",
          board_id: "board-1",
          name: "To do",
          position: 0,
          cards: [
            makeCardResponse({
              checklist_items: [],
            }),
          ],
        },
      ],
    });

    expect(board.columns).toHaveLength(1);
    expect(board.columns[0]?.cards).toHaveLength(
      1,
    );
    expect(
      board.columns[0]?.cards[0]?.checklist,
    ).toEqual([]);

    expect(
      board.columns[0]?.cards[0],
    ).not.toHaveProperty("checklist_items");
  });
});
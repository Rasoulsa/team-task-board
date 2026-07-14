import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  BoardDetail,
  Card,
} from "../domain/types";
import { applyMove } from "./applyMove";

function makeCard(
  id: string,
  columnId: string,
  rank: string,
): Card {
  return {
    id,
    column_id: columnId,
    title: id,
    description: null,
    priority: "medium",
    due_date: null,
    rank,
    labels: [],
    assignees: [],
    checklist: [],
    is_deleted: false,
  };
}

function makeBoard(): BoardDetail {
  return {
    id: "board-1",
    name: "Test board",
    columns: [
      {
        id: "column-1",
        board_id: "board-1",
        name: "To do",
        position: 0,
        cards: [
          makeCard(
            "card-1",
            "column-1",
            "a",
          ),
        ],
      },
      {
        id: "column-2",
        board_id: "board-1",
        name: "Done",
        position: 1,
        cards: [
          makeCard(
            "card-2",
            "column-2",
            "b",
          ),
        ],
      },
    ],
  };
}

describe("applyMove", () => {
  it("moves a card across columns without duplicating it", () => {
    const result = applyMove(
      makeBoard(),
      "card-1",
      {
        target_column_id: "column-2",
        next_card_id: "card-2",
      },
    );

    const allOccurrences = result.columns
      .flatMap((column) => column.cards)
      .filter(
        (card) => card.id === "card-1",
      );

    expect(allOccurrences).toHaveLength(1);

    expect(
      result.columns[0]?.cards.some(
        (card) => card.id === "card-1",
      ),
    ).toBe(false);

    expect(
      result.columns[1]?.cards[0]?.id,
    ).toBe("card-1");

    expect(
      result.columns[1]?.cards[0]?.column_id,
    ).toBe("column-2");
  });

  it("does not mutate the original board", () => {
    const original = makeBoard();

    applyMove(original, "card-1", {
      target_column_id: "column-2",
    });

    expect(
      original.columns[0]?.cards[0]?.id,
    ).toBe("card-1");

    expect(
      original.columns[1]?.cards,
    ).toHaveLength(1);
  });

  it("returns the same board when the card does not exist", () => {
    const board = makeBoard();

    const result = applyMove(
      board,
      "missing-card",
      {
        target_column_id: "column-2",
      },
    );

    expect(result).toBe(board);
  });

  it("returns the same board when the target column does not exist", () => {
    const board = makeBoard();

    const result = applyMove(
      board,
      "card-1",
      {
        target_column_id: "missing-column",
      },
    );

    expect(result).toBe(board);
  });
});
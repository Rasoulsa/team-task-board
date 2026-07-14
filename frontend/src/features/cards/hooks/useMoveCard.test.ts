import { describe, expect, it } from "vitest";

import type { BoardDetail, Card } from "../domain/types";
import { applyMove } from "../application/applyMove";

function makeCard(id: string, columnId: string, rank: string): Card {
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

const board: BoardDetail = {
  id: "b1",
  name: "Board",
  columns: [
    {
      id: "todo",
      board_id: "b1",
      name: "Todo",
      position: 0,
      cards: [makeCard("c1", "todo", "a"), makeCard("c2", "todo", "b")],
    },
    {
      id: "done",
      board_id: "b1",
      name: "Done",
      position: 1,
      cards: [],
    },
  ],
};

describe("applyMove", () => {
  it("moves a card to another column", () => {
    const next = applyMove(board, "c1", {
      target_column_id: "done",
      previous_card_id: null,
      next_card_id: null,
    });

    const todo = next.columns.find((column) => column.id === "todo");
    const done = next.columns.find((column) => column.id === "done");

    expect(todo).toBeDefined();
    expect(done).toBeDefined();

    expect(todo?.cards.map((card) => card.id)).toEqual(["c2"]);
    expect(done?.cards.map((card) => card.id)).toEqual(["c1"]);
    expect(done?.cards[0]?.column_id).toBe("done");
  });

  it("inserts a card before the next card when next_card_id is given", () => {
    const next = applyMove(board, "c2", {
      target_column_id: "todo",
      previous_card_id: null,
      next_card_id: "c1",
    });

    const todo = next.columns.find((column) => column.id === "todo");

    expect(todo?.cards.map((card) => card.id)).toEqual(["c2", "c1"]);
  });

  it("inserts a card after the previous card when previous_card_id is given", () => {
    const next = applyMove(board, "c1", {
      target_column_id: "todo",
      previous_card_id: "c2",
      next_card_id: null,
    });

    const todo = next.columns.find((column) => column.id === "todo");

    expect(todo?.cards.map((card) => card.id)).toEqual(["c2", "c1"]);
  });

  it("appends to the end when no neighbors are provided", () => {
    const next = applyMove(board, "c1", {
      target_column_id: "todo",
      previous_card_id: null,
      next_card_id: null,
    });

    const todo = next.columns.find((column) => column.id === "todo");

    expect(todo?.cards.map((card) => card.id)).toEqual(["c2", "c1"]);
  });

  it("does not mutate the original board", () => {
    applyMove(board, "c1", {
      target_column_id: "done",
      previous_card_id: null,
      next_card_id: null,
    });

    expect(board.columns[0]?.cards.map((card) => card.id)).toEqual([
      "c1",
      "c2",
    ]);

    expect(board.columns[1]?.cards).toEqual([]);
  });

  it("returns the same board when the card does not exist", () => {
    const next = applyMove(board, "missing", {
      target_column_id: "done",
      previous_card_id: null,
      next_card_id: null,
    });

    expect(next).toBe(board);
  });

  it("returns the same board when the target column does not exist", () => {
    const next = applyMove(board, "c1", {
      target_column_id: "missing",
      previous_card_id: null,
      next_card_id: null,
    });

    expect(next).toBe(board);
  });
});
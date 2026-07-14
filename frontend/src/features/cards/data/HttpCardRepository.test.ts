import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import { axiosClient } from "../../../core/http/axiosClient";
import { HttpCardRepository } from "./HttpCardRepository";

vi.mock("../../../core/http/axiosClient", () => ({
  axiosClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockedAxiosClient = vi.mocked(axiosClient);

describe("HttpCardRepository", () => {
  const repository = new HttpCardRepository();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("normalizes nested cards returned by getBoard", async () => {
    mockedAxiosClient.get.mockResolvedValue({
      data: {
        id: "board-1",
        name: "Demo board",
        columns: [
          {
            id: "column-1",
            board_id: "board-1",
            name: "To do",
            position: 0,
            cards: [
              {
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
              },
            ],
          },
        ],
      },
    });

    const result = await repository.getBoard(
      "board-1",
    );

    const card =
      result.columns[0]?.cards[0];

    expect(card?.checklist).toEqual([]);
    expect(card).not.toHaveProperty(
      "checklist_items",
    );

    expect(mockedAxiosClient.get).toHaveBeenCalledWith(
      "/boards/board-1/kanban",
    );
  });

  it("normalizes a created card", async () => {
    mockedAxiosClient.post.mockResolvedValue({
      data: {
        id: "card-1",
        column_id: "column-1",
        title: "Created card",
        description: null,
        priority: "medium",
        due_date: null,
        rank: "m",
        labels: [],
        assignees: [],
        checklist_items: [],
        is_deleted: false,
      },
    });

    const result = await repository.createCard(
      "column-1",
      {
        title: "Created card",
      },
    );

    expect(result.checklist).toEqual([]);
    expect(result).not.toHaveProperty(
      "checklist_items",
    );
  });

  it("normalizes an updated card", async () => {
    mockedAxiosClient.patch.mockResolvedValue({
      data: {
        id: "card-1",
        column_id: "column-1",
        title: "Updated card",
        description: "New description",
        priority: "high",
        due_date: null,
        rank: "m",
        labels: [],
        assignees: [],
        checklist_items: [
          {
            id: "item-1",
            content: "Test item",
            is_done: false,
          },
        ],
        is_deleted: false,
      },
    });

    const result = await repository.updateCard(
      "card-1",
      {
        title: "Updated card",
      },
    );

    expect(result.checklist).toEqual([
      {
        id: "item-1",
        content: "Test item",
        is_done: false,
      },
    ]);

    expect(result).not.toHaveProperty(
      "checklist_items",
    );
  });

  it("normalizes a partial move response", async () => {
    mockedAxiosClient.post.mockResolvedValue({
      data: {
        id: "card-1",
        column_id: "column-2",
        rank: "n",
        checklist_items: [],
      },
    });

    const result = await repository.moveCard(
      "card-1",
      {
        target_column_id: "column-2",
      },
    );

    expect(result).toEqual({
      id: "card-1",
      column_id: "column-2",
      rank: "n",
      checklist: [],
    });

    expect(result).not.toHaveProperty(
      "checklist_items",
    );
  });

  it("deletes a card", async () => {
    mockedAxiosClient.delete.mockResolvedValue({
      data: undefined,
    });

    await repository.deleteCard("card-1");

    expect(
      mockedAxiosClient.delete,
    ).toHaveBeenCalledWith("/cards/card-1");
  });
});
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DndContext } from "@dnd-kit/core";
import { ColumnLane } from "./ColumnLane";
import type { Column } from "../domain/types";

const column: Column = {
  id: "todo",
  board_id: "board-1",
  name: "To Do",
  position: 0,
  cards: [],
};

function renderLane(
  onAddCard = vi.fn().mockResolvedValue(undefined),
) {
  render(
    <DndContext>
      <ColumnLane
        column={column}
        onOpenCard={vi.fn()}
        onAddCard={onAddCard}
        onDeleteCard={vi.fn()}
      />
    </DndContext>,
  );
  return { onAddCard };
}

describe("ColumnLane", () => {
  it("renders the column name", () => {
    renderLane();
    expect(screen.getByText("To Do")).toBeInTheDocument();
  });

  it("calls onAddCard when a title is submitted", async () => {
    const { onAddCard } = renderLane();
    const user = userEvent.setup();

    await user.type(screen.getByPlaceholderText("Add a card"), "New task");
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(onAddCard).toHaveBeenCalledWith("todo", "New task");
  });
});
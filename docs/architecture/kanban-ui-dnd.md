# Kanban UI & Drag-and-Drop Architecture

## Goal

Turn the static board-columns view into a fully interactive Kanban board:
draggable cards and columns, instant (optimistic) visual feedback on
reorder/move, and a card detail modal for editing all card fields.

## Component structure

```text
KanbanBoard
├── DndContext (@dnd-kit/core)
│   ├── ColumnLane (per column, sortable container)
│   │   └── CardItem (per card, useSortable)
│   └── DragOverlay (visual clone of the dragged card)
└── CardModal (opened on card click)
```

- **KanbanBoard** owns the DndContext, the column list, and wires up onDragEnd to the move/reorder mutation.
- **ColumnLane** renders a droppable/sortable list of cards using SortableContext from @dnd-kit/sortable.
- **CardItem** uses useSortable for drag handles, transform, and transition; applies opacity: 0.5 while the item being dragged is the active one, so the source position stays visible as a placeholder.
- **CardModal** is a controlled dialog for viewing/editing a single card: title, description, priority, due date, checklist, labels, assignees.

## Drag-and-drop flow
1. `onDragStart` records the active card id and its source column.
2. `onDragOver` is used only for visual column-switch feedback while dragging; it does not persist anything.
3. `onDragEnd` computes:
    - the destination column,
    - the destination index among that column’s cards,
    - a new LexoRank rank string, based on the ranks of the two neighboring cards at the drop position (see `frontend/src/core/lexorank/lexorank.ts`).
4. The local cache is updated optimistically (card moved to the new column at the new rank) via TanStack Query’s `setQueryData`, so the UI reflects the move immediately with zero perceived latency.
5. `useMoveCard` (a TanStack Query mutation) sends the move to the backend (`PATCH` on the card, or a dedicated move endpoint) with the target column id and computed rank.
6. On success, the mutation’s response is treated as the source of truth; on error, the optimistic update is rolled back and the previous board state is restored via the mutation’s `onError` cache rollback.

## Why client-side LexoRank

Computing the rank on the client (rather than waiting on a backend-computed
rank) is what makes the optimistic update possible: the UI needs a final
rank value immediately to render the correct order, before the network
round-trip completes. The backend independently validates/recomputes the
rank server-side as the authoritative value, so client and server
implementations of the algorithm must stay identical (see
`README.md#shared-utilities`).

## State and caching
- All card data for a board is fetched and cached under a single board-scoped query key (`cardQueryKeys.board(boardId)`).
- Mutations (`useCreateCard`, `useMoveCard`, `useUpdateCard`, `useDeleteCard`, `useRestoreCard`, label/assignee/checklist hooks) all read and write that same cache entry, so the board view, card modal, and any other card-aware component stay in sync from one source of truth.
- `CardRepository` normalizes raw backend card responses (e.g. mapping `checklist_items` to `checklist`) into a single consistent frontend `Card` shape before anything else touches the data, so components never need to special-case backend field naming.

## Known simplifications
- Drag-and-drop reordering within a column and moving across columns share the same mutation path; there is no separate “reorder-only” endpoint.
- Error feedback for failed create/move mutations is minimal (no toast/inline banner yet) — this was later revisited alongside Day 6 real-time work.
- No card deletion entry point in the UI yet at the end of Day 5 (soft delete/restore exists on the backend; frontend wiring for delete came later).
## Phase: Kanban UI and Drag & Drop (Frontend)

### Scope
- Kanban board, columns, and card components using @dnd-kit
- Optimistic reordering with client-side LexoRank
- Persistence of moves through CardService
- Card modal exposing title, description, priority, due date, checklist, labels, and assignees
- TanStack Query for board caching and invalidation

### Design decisions
- Optimistic updates apply moves locally before the server responds, then reconcile
  through query invalidation in onSettled.
- LexoRank is computed on the client using the same algorithm as the backend so that
  the optimistic order matches persisted order.
- @dnd-kit was chosen over react-beautiful-dnd for active maintenance, accessibility,
  and better TypeScript support.
- The board is fetched as a single aggregate (columns with nested cards) to avoid
  N+1 client fetches; TanStack Query caches it under a board-scoped key.

### Testing
- Unit test for the optimistic move reducer (applyMove).
- Unit test for the LexoRank between-helper.
- Component test for column rendering and card creation.

### Follow-ups
- Wire checklist, label, and assignee mutations in the card modal.
- Replace REST refetch-on-settle with real-time WebSocket updates in the next phase.

Create `docs/architecture.md` frontend section if not present, describing:

- Presentation: React components
- Service: `CardService`
- Repository: `HttpCardRepository`
- Data access: axios `http` client
- State/caching: TanStack Query + optimistic mutations
- Shared LexoRank utility with backend
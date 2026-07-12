# Cards, Ordering, Comments

This phase adds the core task-management domain on top of Projects and Boards.

## Domain model

```text
organizations
└── projects
└── boards
├── activity_logs
└── board_columns
└── cards
├── card_labels
├── card_assignees
├── checklist_items
└── comments
└── comment_mentions
```

## Ordering strategy: LexoRank

Cards are ordered using a string rank rather than an integer position.

Reasons:

- Reordering a card only updates that single card's `rank`.
- No renumbering of siblings is required.
- Works well with optimistic drag & drop on the frontend.

A new rank is generated between two neighbors:

- `rank_between(None, None)` returns a middle default rank.
- `rank_between(prev, None)` returns a rank after `prev`.
- `rank_between(None, next)` returns a rank before `next`.
- `rank_between(prev, next)` returns a rank strictly between them.

The same algorithm exists on both stacks:

- Backend: `app/utils/lexorank.py`
- Frontend: `src/core/lexorank/lexorank.ts`

The backend is the source of truth. The frontend copy is only used for
optimistic UI updates before the server response.

## Soft delete and restore

Cards are soft-deleted:

- `is_deleted = true`
- `deleted_at` timestamp set

Listing cards excludes soft-deleted rows by default. Restore clears the flag.
The `activity_logs` table is preserved so history survives deletion.

## Comments and mentions

Comment bodies are scanned for `@handle` mentions. The handle is matched
against the user's email local-part. Each match creates a
`comment_mentions` row. This will drive notifications in a later phase.

## Activity log

Every meaningful action records an entry in `activity_logs`:

- card.created, card.updated, card.moved, card.deleted, card.restored
- comment.created

Activity is keyed by board so it can power the board activity feed and,
later, the reporting dashboard.

## RBAC

- Viewer: read cards, comments, activity.
- Member and above: create/update/move/delete cards, add comments.

Access is resolved by mapping a card or column back to its board and then to
the owning organization, then applying the Phase 3 role check.
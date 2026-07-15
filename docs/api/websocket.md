# WebSocket API

## Connection

```text
GET /api/v1/ws/boards/{board_id}?token={access_token}
```

- `token` is a valid JWT access token, passed as a query parameter because browser WebSocket clients cannot set custom headers.
- The server validates the token and board membership before accepting the connection. Invalid token or insufficient access results in the connection being closed immediately with a policy-violation close code.

## Message envelope
Every message sent from server to client has the shape:

```json
{
  "type": "string",
  "board_id": "uuid",
  "actor_id": "uuid",
  "payload": { }
}
```

## Event types

```text
| Event | Payload | Description |
|---|---|---|
| `card.created` | `{ card }` | A new card was created on the board. |
| `card.updated` | `{ card }` | Card fields changed (title, description, priority, due date, etc.). |
| `card.moved` | `{ card_id, from_column_id, to_column_id, rank }` | Card moved within or across columns. |
| `card.deleted` | `{ card_id }` | Card soft-deleted. |
| `card.restored` | `{ card }` | Card restored from soft delete. |
| `comment.created` | `{ comment }` | New comment added to a card. |
| `presence.joined` | `{ user_id }` | A member connected to the board. |
| `presence.left` | `{ user_id }` | A member disconnected from the board. |
```

## Client responsibilities
- Ignore messages where `actor_id` matches the current user — the client already reflects its own mutation via optimistic update / mutation response.
- Ignore `presence.*` events for data invalidation purposes; they are for presence UI only.
On any other event type, treat it as “board data may have changed” and invalidate/refetch card queries for that board.

## Heartbeat
Clients are expected to remain connected; the server does not currently
require client-sent pings. Presence TTL is refreshed server-side while the
connection is open.
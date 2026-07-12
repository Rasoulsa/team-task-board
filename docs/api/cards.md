# Cards API

Base path: `/api/v1`

## Cards

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| GET | `/columns/{column_id}/cards` | Viewer | List active cards in a column |
| POST | `/columns/{column_id}/cards` | Member | Create a card (appended by rank) |
| GET | `/cards/{card_id}` | Viewer | Get a single card |
| PATCH | `/cards/{card_id}` | Member | Update card fields |
| POST | `/cards/{card_id}/move` | Member | Move/reorder using LexoRank |
| DELETE | `/cards/{card_id}` | Member | Soft delete |
| POST | `/cards/{card_id}/restore` | Member | Restore soft-deleted card |

## Card details

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| POST | `/cards/{card_id}/labels` | Member | Add a label |
| POST | `/cards/{card_id}/assignees` | Member | Add an assignee |
| POST | `/cards/{card_id}/checklist` | Member | Add checklist item |
| PATCH | `/checklist/{item_id}` | Member | Update checklist item |

## Comments

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| GET | `/cards/{card_id}/comments` | Viewer | List comments |
| POST | `/cards/{card_id}/comments` | Member | Add comment (parses @mentions) |

## Activity

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| GET | `/boards/{board_id}/activity` | Viewer | Recent board activity |

## Move request body

```json
{
  "target_column_id": "uuid",
  "previous_card_id": "uuid or null",
  "next_card_id": "uuid or null"
}
# API Endpoints

Base URL:

```text
/api/v1
```

## Organizations

### List current user’s organizations

```http
GET /organizations
```

Requires authentication.

Response:

```json
[
  {
    "id": "uuid",
    "name": "Demo Team",
    "created_at": "2026-07-11T00:00:00Z",
    "updated_at": "2026-07-11T00:00:00Z"
  }
]
```

## Projects

### List projects
```http
GET /projects?organization_id={organization_id}
```

Minimum role: `VIEWER`

### Create project
```http
POST /projects
```

Minimum role: `MEMBER`

Payload:

```json
{
  "organization_id": "uuid",
  "name": "Demo Project",
  "description": "Optional description"
}
```

### Get project
```http
GET /projects/{project_id}
```

Minimum role: `VIEWER`

### Update project
```http
PATCH /projects/{project_id}
```

Minimum role: `MEMBER`

Payload:

```json
{
  "name": "Updated Project",
  "description": "Updated description"
}
```

### Delete project
```http
DELETE /projects/{project_id}
```

Minimum role: `ADMIN`

## Boards

### List boards
```http
GET /projects/{project_id}/boards
```

Minimum role: `VIEWER`

### Create board
```http
POST /projects/{project_id}/boards
```

Minimum role: `MEMBER`

Payload:

```json
{
  "name": "Engineering Board",
  "description": "Sprint work"
}
```

### Get board
```http
GET /boards/{board_id}
```

Minimum role: `VIEWER`

### Update board
```http
PATCH /boards/{board_id}
```

Minimum role: `MEMBER`

### Delete board
```http
DELETE /boards/{board_id}
```

Minimum role: `ADMIN`

## Columns

### List columns
```http
GET /boards/{board_id}/columns
```
Minimum role: `VIEWER`

### Create column
```http
POST /boards/{board_id}/columns
```

Minimum role: `MEMBER`

Payload:

```json
{
  "name": "Todo",
  "position": 0
}
```

### Update column
```http
PATCH /columns/{column_id}
```

Minimum role: `MEMBER`

### Delete column
```http
DELETE /columns/{column_id}
```

Minimum role: `MEMBER`

## Invitations

### List invitations
```http
GET /organizations/{organization_id}/invitations
```

Minimum role: `ADMIN`

### Create invitation
```http
POST /organizations/{organization_id}/invitations
```

Minimum role: `ADMIN`

Payload:

```json
{
  "email": "member@example.com",
  "role": "MEMBER"
}
```

### Revoke invitation
```http
POST /invitations/{invitation_id}/revoke
```

Minimum role: `ADMIN`
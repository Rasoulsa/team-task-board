# Backend Architecture — RBAC, Projects, Boards, Columns

## Scope

This phase introduces the backend foundation for organization-scoped project management.

Implemented capabilities:

- Role-Based Access Control for organization members
- Project CRUD
- Board CRUD
- Column CRUD
- Basic invitation management
- Repository and service layers for new resources

## RBAC Model

The system supports four organization roles:

```text
| Role   | Level | Purpose |
| ------ | ----- | ------- |
| OWNER  | 40    | Full organization control |
| ADMIN  | 30    | Manage organization resources and invitations |
| MEMBER | 20    | Create and update workspace resources |
| VIEWER | 10    | Read-only access |
```

RBAC is implemented in:

```text
backend/app/api/rbac.py
```

The core functions are:
- `role_allows(actual, required)`
- `get_membership(...)`
- `require_org_role(...)`


### Permission policy

```text
| Action | Minimum role |
|---|---|
| List projects | VIEWER |
| View project | VIEWER |
| Create project | MEMBER |
| Update project | MEMBER |
| Delete project | ADMIN |
| List boards | VIEWER |
| Create board | MEMBER |
| Update board | MEMBER |
| Delete board | ADMIN |
| List columns | VIEWER |
| Create column | MEMBER |
| Update column | MEMBER |
| Delete column | MEMBER |
| Create invitation | ADMIN |
| List invitations | ADMIN |
| Revoke invitation | ADMIN |
```

### Data model

```text
organizations
  └── projects
        └── boards
              └── board_columns
```

### Layered design

Each resource follows the same structure:
```text
API route -> Service -> Repository -> SQLAlchemy model
```

Example for projects:

```text
app/api/v1/routes/projects.py
app/services/projects.py
app/repositories/projects.py
app/models/project.py
app/schemas/project.py
```

### Notes
- Columns use integer ordering for now.
- LexoRank ordering is planned for the cards phase.
- Invitation accept flow can be extended in the team management phase.
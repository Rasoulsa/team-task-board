# Implementation Log

## Title

RBAC, Projects/Boards Backend, and Frontend App Shell

## Summary

This phase expands the authenticated product foundation into an organization-scoped task management structure.

## Backend work completed

- Added RBAC helper module
- Added project model, schema, repository, service, and API routes
- Added board model, schema, repository, service, and API routes
- Added board column model, schema, repository, service, and API routes
- Added organization listing endpoint for current user
- Added basic invitation list/create/revoke endpoints
- Added Alembic migration for projects, boards, and columns
- Added RBAC unit tests

## Frontend work completed

- Added authenticated app shell
- Added sidebar navigation
- Added topbar with notification bell placeholder
- Added project repository/service/page
- Added board repository/service/page
- Added board columns preview and create form
- Added frontend unit tests for project and board services

## Design decisions

### Integer column ordering for now

Columns use simple integer positions in this phase. Card ordering will use LexoRank in the next backend card phase.

### RBAC in service layer

Route handlers remain thin. Permission checks are executed in service methods close to business logic.

### Frontend repository/service pattern

The frontend continues using repository interfaces and service classes to keep UI pages independent from HTTP implementation details.

## Next phase

The next phase will add cards, card ordering, comments, mentions, soft delete, restore, and activity log foundations.
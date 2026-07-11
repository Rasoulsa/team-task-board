# Frontend Architecture — App Shell and Project/Board Pages

## Scope

This phase adds the authenticated application shell and the first organization/project/board UI pages.

Implemented capabilities:

- Authenticated app layout
- Sidebar navigation
- Topbar
- Notification bell placeholder
- Projects page
- Boards page
- Board columns preview
- Project and board repository/service abstractions

## Layout

The app shell is implemented in:

```text
frontend/src/features/app-shell/components/AppLayout.tsx
```

Protected routes are nested inside the app shell:

```text
/dashboard
/projects
/projects/:projectId/boards
```

### Feature structure

Projects:

```text
features/projects/domain
features/projects/data
features/projects/application
features/projects/pages
```

Boards:

```text
features/boards/domain
features/boards/data
features/boards/application
features/boards/pages
```

### Dependency inversion

Frontend services depend on repository interfaces.

Example:

```text
ProjectService -> ProjectRepository
HttpProjectRepository -> API client
```

The DI container wires concrete implementations:

```text
frontend/src/core/di/container.ts
```

### Real-time readiness

The topbar includes a notification bell placeholder. This will be connected to WebSocket notifications in the real-time and notification phases.
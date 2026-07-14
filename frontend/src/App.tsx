import { Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from './features/app-shell/components/AppLayout';
import { ProtectedRoute } from './features/auth/components/ProtectedRoute';
import { LoginPage } from './features/auth/pages/LoginPage';
import { RegisterPage } from './features/auth/pages/RegisterPage';
import { BoardPage } from './features/boards/pages/BoardPage';
import { BoardsPage } from './features/boards/pages/BoardsPage';
import { DashboardPage } from './features/dashboard/pages/DashboardPage';
import { ProjectsPage } from './features/projects/pages/ProjectsPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/projects" element={<ProjectsPage />} />

        <Route
          path="/projects/:projectId/boards"
          element={<BoardsPage />}
        />

        <Route
          path="/projects/:projectId/boards/:boardId"
          element={<BoardPage />}
        />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
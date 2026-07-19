import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { isGuestRole } from '../domain/roles';

export function GuestGuard({ children }: { children: React.ReactNode }) {
  const role = useAuthStore((s) => s.user?.role);
  if (isGuestRole(role)) return <Navigate to="/assigned-cards" replace />;
  return <>{children}</>;
}
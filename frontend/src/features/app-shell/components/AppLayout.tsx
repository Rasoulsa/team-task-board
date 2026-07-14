import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';

import { container } from '../../../core/di/container';
import { useAuthStore } from '../../auth/store/authStore';

export function AppLayout() {
  const navigate = useNavigate();

  const user = useAuthStore((state) => state.user);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const clearSession = useAuthStore((state) => state.clearSession);

  async function handleLogout() {
    try {
      if (refreshToken) {
        await container.authService.logout(refreshToken);
      }
    } finally {
      clearSession();
      navigate('/login', { replace: true });
    }
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-white">
      <aside className="hidden w-64 border-r border-slate-800 bg-slate-900/80 p-4 md:block">
        <Link to="/dashboard" className="block">
          <h1 className="text-xl font-bold">Team Task Board</h1>
          <p className="mt-1 text-xs text-slate-400">
            Collaborative task management
          </p>
        </Link>

        <nav className="mt-8 space-y-2">
          <NavItem to="/dashboard" label="Dashboard" />
          <NavItem to="/projects" label="Projects" />
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-950 px-6">
          <div>
            <p className="text-sm text-slate-400">Workspace</p>
            <p className="font-medium">Kanban task management</p>
          </div>

          <div className="flex items-center gap-4">
            <button
              type="button"
              className="relative rounded-full border border-slate-700 px-3 py-2 text-sm hover:bg-slate-900"
            >
              🔔 <span className="ml-1 text-slate-400">0</span>
            </button>

            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium">{user?.full_name}</p>
              <p className="text-xs text-slate-400">{user?.email}</p>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700"
            >
              Logout
            </button>
          </div>
        </header>

        <main className="min-w-0 flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

type NavItemProps = {
  to: string;
  label: string;
};

function NavItem({ to, label }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          'block rounded-lg px-3 py-2 text-sm transition',
          isActive
            ? 'bg-blue-600 text-white'
            : 'text-slate-300 hover:bg-slate-800 hover:text-white',
        ].join(' ')
      }
    >
      {label}
    </NavLink>
  );
}
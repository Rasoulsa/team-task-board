import { Link } from 'react-router-dom';

import { useAuthStore } from '../../auth/store/authStore';

export function DashboardPage() {
  const user = useAuthStore((state) => state.user);

  return (
    <div>
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">
          Welcome back to Team Task Board FIXED2.
        </p>
      </div>

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">Signed in as</p>
          <p className="mt-2 font-medium">{user?.email}</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">Current phase</p>
          <p className="mt-2 font-medium">RBAC + Projects/Boards</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">Notifications</p>
          <p className="mt-2 font-medium">0 unread</p>
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-lg font-semibold">Quick actions</h2>

        <div className="mt-4 flex flex-wrap gap-3">
          <Link
            to="/projects"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-500"
          >
            Open Projects
          </Link>
        </div>
      </section>
    </div>
  );
}
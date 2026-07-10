import { container } from '../../../core/di/container';
import { useAuthStore } from '../store/authStore';

export function DashboardPage() {
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
      window.location.href = '/login';
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <header className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
        <div>
          <h1 className="text-xl font-bold">Team Task Board</h1>
          <p className="text-sm text-slate-400">Dashboard placeholder</p>
        </div>

        <button
          className="rounded-lg bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700"
          onClick={handleLogout}
          type="button"
        >
          Logout
        </button>
      </header>

      <section className="p-6">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-lg font-semibold">Welcome</h2>

          <p className="mt-2 text-slate-400">
            Logged in as: {user?.email}
          </p>
        </div>
      </section>
    </main>
  );
}
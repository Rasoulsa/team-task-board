import { useState, type SyntheticEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { container } from '../../../core/di/container';
import { useAuthStore } from '../store/authStore';

export function RegisterPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((state) => state.setSession);

  const [fullName, setFullName] = useState('Demo User');
  const [organizationName, setOrganizationName] = useState('Demo Team');
  const [email, setEmail] = useState('demo@example.com');
  const [password, setPassword] = useState('Password123!');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await container.authService.register({
        email,
        password,
        full_name: fullName,
        organization_name: organizationName,
      });

      setSession({
        user: response.user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
      });

      navigate('/dashboard');
    } catch {
      setError('Could not create account. The email may already be registered.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-xl">
        <h1 className="text-2xl font-bold">Create account</h1>

        <p className="mt-2 text-sm text-slate-400">
          Create your workspace and start managing tasks.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="fullName" className="text-sm text-slate-300">
              Full name
            </label>

            <input
              id="fullName"
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              autoComplete="name"
              required
            />
          </div>

          <div>
            <label htmlFor="organizationName" className="text-sm text-slate-300">
              Organization
            </label>

            <input
              id="organizationName"
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
              value={organizationName}
              onChange={(event) => setOrganizationName(event.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="registerEmail" className="text-sm text-slate-300">
              Email
            </label>

            <input
              id="registerEmail"
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              autoComplete="email"
              required
            />
          </div>

          <div>
            <label htmlFor="registerPassword" className="text-sm text-slate-300">
              Password
            </label>

            <input
              id="registerPassword"
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete="new-password"
              required
            />
          </div>

          {error ? <p className="text-sm text-red-400">{error}</p> : null}

          <button
            className="w-full rounded-lg bg-blue-600 px-4 py-2 font-medium hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? 'Creating account...' : 'Register'}
          </button>
        </form>

        <p className="mt-4 text-sm text-slate-400">
          Already have an account?{' '}
          <Link className="text-blue-400 hover:text-blue-300" to="/login">
            Login
          </Link>
        </p>
      </div>
    </main>
  );
}
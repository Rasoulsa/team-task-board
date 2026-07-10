import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import type { AuthSessionPayload, User } from '../domain/types';

type AuthState = {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  setSession: (payload: AuthSessionPayload) => void;
  clearSession: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setSession: ({ user, accessToken, refreshToken }) => {
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        });
      },

      clearSession: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'team-task-board-auth',
    },
  ),
);
import { describe, expect, it, vi } from 'vitest';

import { AuthService } from './AuthService';
import type { AuthRepository } from '../domain/AuthRepository';

describe('AuthService', () => {
  it('logs in through repository', async () => {
    const repository: AuthRepository = {
      register: vi.fn(),
      login: vi.fn().mockResolvedValue({
        access_token: 'access',
        refresh_token: 'refresh',
        token_type: 'bearer',
        user: {
          id: 'user-id',
          email: 'demo@example.com',
          full_name: 'Demo User',
          is_active: true,
          is_verified: false,
        },
      }),
      refresh: vi.fn(),
      logout: vi.fn(),
      me: vi.fn(),
    };

    const service = new AuthService(repository);

    const response = await service.login({
      email: 'demo@example.com',
      password: 'Password123!',
    });

    expect(response.access_token).toBe('access');
    expect(repository.login).toHaveBeenCalledOnce();
  });
});
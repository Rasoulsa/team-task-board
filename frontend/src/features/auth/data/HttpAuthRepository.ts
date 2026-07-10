import { apiClient } from '../../../core/http/client';
import type { AuthRepository } from '../domain/AuthRepository';
import type { AuthResponse, LoginInput, RegisterInput, User } from '../domain/types';

export class HttpAuthRepository implements AuthRepository {
  async register(input: RegisterInput): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register', input);
    return response.data;
  }

  async login(input: LoginInput): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', input);
    return response.data;
  }

  async refresh(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    return response.data;
  }

  async logout(refreshToken: string): Promise<void> {
    await apiClient.post('/auth/logout', {
      refresh_token: refreshToken,
    });
  }

  async me(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  }
}
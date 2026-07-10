import type { AuthResponse, LoginInput, RegisterInput, User } from './types';

export interface AuthRepository {
  register(input: RegisterInput): Promise<AuthResponse>;
  login(input: LoginInput): Promise<AuthResponse>;
  refresh(refreshToken: string): Promise<AuthResponse>;
  logout(refreshToken: string): Promise<void>;
  me(): Promise<User>;
}
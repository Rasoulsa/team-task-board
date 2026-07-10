import type { AuthRepository } from '../domain/AuthRepository';
import type { AuthResponse, LoginInput, RegisterInput, User } from '../domain/types';

export class AuthService {
  private readonly authRepository: AuthRepository;

  constructor(authRepository: AuthRepository) {
    this.authRepository = authRepository;
  }

  register(input: RegisterInput): Promise<AuthResponse> {
    return this.authRepository.register(input);
  }

  login(input: LoginInput): Promise<AuthResponse> {
    return this.authRepository.login(input);
  }

  refresh(refreshToken: string): Promise<AuthResponse> {
    return this.authRepository.refresh(refreshToken);
  }

  logout(refreshToken: string): Promise<void> {
    return this.authRepository.logout(refreshToken);
  }

  me(): Promise<User> {
    return this.authRepository.me();
  }
}
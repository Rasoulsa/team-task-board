import { AuthService } from '../../features/auth/application/AuthService';
import { HttpAuthRepository } from '../../features/auth/data/HttpAuthRepository';

const authRepository = new HttpAuthRepository();

export const container = {
  authService: new AuthService(authRepository),
};
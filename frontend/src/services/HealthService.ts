import { HealthRepository } from '../repositories/HealthRepository';

export class HealthService {
  private readonly repo: HealthRepository;

  constructor(repo: HealthRepository) {
    this.repo = repo;
  }

  check(): Promise<string> {
    return this.repo.ping();
  }
}
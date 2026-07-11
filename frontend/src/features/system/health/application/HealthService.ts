import { HealthRepository } from '../data/HealthRepository';

export class HealthService {
  private readonly repo: HealthRepository;

  constructor(repo: HealthRepository) {
    this.repo = repo;
  }

  check(): Promise<string> {
    return this.repo.ping();
  }
}
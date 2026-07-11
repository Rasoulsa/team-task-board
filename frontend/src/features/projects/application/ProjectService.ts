import type { ProjectRepository } from '../domain/ProjectRepository';
import type {
  CreateProjectInput,
  Organization,
  Project,
  UpdateProjectInput,
} from '../domain/types';

export class ProjectService {
  private readonly projectRepository: ProjectRepository;

  constructor(projectRepository: ProjectRepository) {
    this.projectRepository = projectRepository;
  }

  listOrganizations(): Promise<Organization[]> {
    return this.projectRepository.listOrganizations();
  }

  listProjects(organizationId: string): Promise<Project[]> {
    return this.projectRepository.listProjects(organizationId);
  }

  createProject(input: CreateProjectInput): Promise<Project> {
    return this.projectRepository.createProject(input);
  }

  updateProject(
    projectId: string,
    input: UpdateProjectInput,
  ): Promise<Project> {
    return this.projectRepository.updateProject(projectId, input);
  }

  deleteProject(projectId: string): Promise<void> {
    return this.projectRepository.deleteProject(projectId);
  }
}
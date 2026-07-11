import type {
  CreateProjectInput,
  Organization,
  Project,
  UpdateProjectInput,
} from './types';

export interface ProjectRepository {
  listOrganizations(): Promise<Organization[]>;
  listProjects(organizationId: string): Promise<Project[]>;
  createProject(input: CreateProjectInput): Promise<Project>;
  updateProject(projectId: string, input: UpdateProjectInput): Promise<Project>;
  deleteProject(projectId: string): Promise<void>;
}
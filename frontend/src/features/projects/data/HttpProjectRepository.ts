import { apiClient } from '../../../core/http/client';
import type { ProjectRepository } from '../domain/ProjectRepository';
import type {
  CreateProjectInput,
  Organization,
  Project,
  UpdateProjectInput,
} from '../domain/types';

export class HttpProjectRepository implements ProjectRepository {
  async listOrganizations(): Promise<Organization[]> {
    const response = await apiClient.get<Organization[]>('/organizations');
    return response.data;
  }

  async listProjects(organizationId: string): Promise<Project[]> {
    const response = await apiClient.get<Project[]>('/projects', {
      params: {
        organization_id: organizationId,
      },
    });

    return response.data;
  }

  async createProject(input: CreateProjectInput): Promise<Project> {
    const response = await apiClient.post<Project>('/projects', input);
    return response.data;
  }

  async updateProject(
    projectId: string,
    input: UpdateProjectInput,
  ): Promise<Project> {
    const response = await apiClient.patch<Project>(
      `/projects/${projectId}`,
      input,
    );

    return response.data;
  }

  async deleteProject(projectId: string): Promise<void> {
    await apiClient.delete(`/projects/${projectId}`);
  }
}
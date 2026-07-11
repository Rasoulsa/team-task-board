import { describe, expect, it, vi } from 'vitest';

import { ProjectService } from './ProjectService';
import type { ProjectRepository } from '../domain/ProjectRepository';

describe('ProjectService', () => {
  it('lists projects through repository', async () => {
    const repository: ProjectRepository = {
      listOrganizations: vi.fn(),
      listProjects: vi.fn().mockResolvedValue([
        {
          id: 'project-id',
          organization_id: 'org-id',
          name: 'Demo Project',
          description: null,
          created_at: '2026-07-11T00:00:00Z',
          updated_at: '2026-07-11T00:00:00Z',
        },
      ]),
      createProject: vi.fn(),
      updateProject: vi.fn(),
      deleteProject: vi.fn(),
    };

    const service = new ProjectService(repository);

    const projects = await service.listProjects('org-id');

    expect(projects).toHaveLength(1);
    expect(projects[0].name).toBe('Demo Project');
    expect(repository.listProjects).toHaveBeenCalledWith('org-id');
  });
});
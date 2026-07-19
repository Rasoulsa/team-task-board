import type { OrganizationRole } from "../../../core/domain/roles";

export type Organization = {
  id: string;
  name: string;
  role: OrganizationRole;
  created_at: string;
  updated_at: string;
};

export type Project = {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type CreateProjectInput = {
  organization_id: string;
  name: string;
  description?: string | null;
};

export type UpdateProjectInput = {
  name?: string;
  description?: string | null;
};
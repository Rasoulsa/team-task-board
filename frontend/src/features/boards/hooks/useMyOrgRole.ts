import { useQuery } from "@tanstack/react-query";
import { container } from "../../../core/di/container";
import type { OrganizationRole } from "../../../core/domain/roles";

export function useMyOrgRole(organizationId: string) {
  const { data: organizations } = useQuery({
    queryKey: ["organizations"],
    queryFn: () => container.projectService.listOrganizations(),
  });

  const role = organizations?.find(
    (org) => org.id === organizationId,
  )?.role as OrganizationRole | undefined;

  return role;
}
import { useQuery } from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import { organizationQueryKeys } from "./queryKeys";

export function useOrganizationMembers(
  organizationId: string,
) {
  return useQuery({
    queryKey:
      organizationQueryKeys.members(
        organizationId,
      ),
    queryFn: () =>
      container.organizationService.listMembers(
        organizationId,
      ),
    enabled: Boolean(organizationId),
  });
}
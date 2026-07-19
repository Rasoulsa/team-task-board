import { useState } from "react";

import type { Organization } from "../../features/projects/domain/types";

const ACTIVE_ORG_KEY = "activeOrganizationId";

export function useActiveOrganization(organizations: Organization[]) {
  const [stored, setStored] = useState<string>(
    () => localStorage.getItem(ACTIVE_ORG_KEY) ?? "",
  );

  // Ensure the stored ID is still valid; fall back to first org if not
  const activeOrganizationId =
    (organizations.some((o) => o.id === stored) && stored) ||
    organizations[0]?.id ||
    "";

  const activeOrganization = organizations.find(
    (o) => o.id === activeOrganizationId,
  );

  function setActiveOrganization(id: string) {
    localStorage.setItem(ACTIVE_ORG_KEY, id);
    setStored(id);
  }

  return {
    activeOrganizationId,
    activeOrganization,
    setActiveOrganization,
  };
}
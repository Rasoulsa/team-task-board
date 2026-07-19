export const organizationQueryKeys = {
  all: ["organizations"] as const,

  members: (organizationId: string) =>
    [
      ...organizationQueryKeys.all,
      organizationId,
      "members",
    ] as const,
};
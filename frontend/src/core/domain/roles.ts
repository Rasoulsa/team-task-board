export type OrganizationRole =
  | "owner"
  | "admin"
  | "member"
  | "viewer"
  | "guest";

export function isViewerOrGuest(
  role: OrganizationRole | undefined,
): boolean {
  return role === "viewer" || role === "guest";
}

export function isGuestOnly(role: OrganizationRole | undefined): boolean {
  return role === "guest";
}
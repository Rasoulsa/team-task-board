import type { OrganizationRole } from './types';

export const isGuestRole = (role: OrganizationRole | undefined) => role === 'guest';
export const isViewerOrGuest = (role: OrganizationRole | undefined) =>
  role === 'viewer' || role === 'guest';
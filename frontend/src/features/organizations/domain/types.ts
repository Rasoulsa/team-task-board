// Import from core
import type { OrganizationRole } from "../../../core/domain/roles";

// Re-export it
export type { OrganizationRole };

export type InvitationStatus =
  | "pending"
  | "accepted"
  | "revoked"
  | "expired";

export interface OrganizationMember {
  id: string;
  user_id: string;
  organization_id: string;
  full_name: string;
  email: string;
  role: OrganizationRole;
  created_at: string;
}

export interface Invitation {
  id: string;
  organization_id: string;
  inviter_id: string;
  email: string;
  token: string;
  role: OrganizationRole;
  status: InvitationStatus;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
}

export interface InviteMemberInput {
  email: string;
  role: OrganizationRole;
}
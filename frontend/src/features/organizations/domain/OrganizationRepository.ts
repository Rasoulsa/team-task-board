import type {
  Invitation,
  InviteMemberInput,
  OrganizationMember,
} from "./types";

export interface OrganizationRepository {
  listMembers(
    organizationId: string,
  ): Promise<OrganizationMember[]>;

  inviteMember(
    organizationId: string,
    input: InviteMemberInput,
  ): Promise<Invitation>;

  acceptInvitation(token: string): Promise<void>;
}
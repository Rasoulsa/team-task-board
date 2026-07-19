import { apiClient } from "../../../core/http/client";
import type { OrganizationRepository } from "../domain/OrganizationRepository";
import type {
  Invitation,
  InviteMemberInput,
  OrganizationMember,
} from "../domain/types";

export class HttpOrganizationRepository
  implements OrganizationRepository
{
  async listMembers(
    organizationId: string,
  ): Promise<OrganizationMember[]> {
    const response = await apiClient.get<
      OrganizationMember[]
    >(`/organizations/${organizationId}/members`);

    return response.data;
  }

  async inviteMember(
    organizationId: string,
    input: InviteMemberInput,
  ): Promise<Invitation> {
    const response =
      await apiClient.post<Invitation>(
        `/organizations/${organizationId}/invitations`,
        input,
      );

    return response.data;
  }

  async acceptInvitation(
    token: string,
  ): Promise<void> {
    await apiClient.post(
      `/invitations/${token}/accept`,
    );
  }
}
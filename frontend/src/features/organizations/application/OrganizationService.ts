import type { OrganizationRepository } from "../domain/OrganizationRepository";
import type {
  Invitation,
  InviteMemberInput,
  OrganizationMember,
} from "../domain/types";

export class OrganizationService {
  private readonly organizationRepository: OrganizationRepository;

  constructor(
    organizationRepository: OrganizationRepository,
  ) {
    this.organizationRepository =
      organizationRepository;
  }

  listMembers(
    organizationId: string,
  ): Promise<OrganizationMember[]> {
    return this.organizationRepository.listMembers(
      organizationId,
    );
  }

  inviteMember(
    organizationId: string,
    input: InviteMemberInput,
  ): Promise<Invitation> {
    return this.organizationRepository.inviteMember(
      organizationId,
      input,
    );
  }

  acceptInvitation(token: string): Promise<void> {
    return this.organizationRepository.acceptInvitation(
      token,
    );
  }
}
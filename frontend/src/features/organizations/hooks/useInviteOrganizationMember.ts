import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import type { InviteMemberInput } from "../domain/types";
import { organizationQueryKeys } from "./queryKeys";

interface InviteVariables {
  organizationId: string;
  input: InviteMemberInput;
}

export function useInviteOrganizationMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      organizationId,
      input,
    }: InviteVariables) =>
      container.organizationService.inviteMember(
        organizationId,
        input,
      ),

    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({
        queryKey:
          organizationQueryKeys.members(
            variables.organizationId,
          ),
      });
    },
  });
}
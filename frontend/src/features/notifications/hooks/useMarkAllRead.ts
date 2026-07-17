import { useMutation, useQueryClient } from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import { notificationKeys } from "./queryKeys";

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => container.notificationService.markAllRead(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}
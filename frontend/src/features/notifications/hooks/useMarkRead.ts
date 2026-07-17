import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { AppNotification } from "../domain/types";
import { container } from "../../../core/di/container";
import { notificationKeys } from "./queryKeys";

interface MutationContext {
  previousList: AppNotification[] | undefined;
  previousCount: number | undefined;
}

export function useMarkRead() {
  const queryClient = useQueryClient();

  return useMutation<void, unknown, string, MutationContext>({
    mutationFn: (id: string) => container.notificationService.markRead(id),

    onMutate: async (id: string) => {
      await queryClient.cancelQueries({ queryKey: notificationKeys.list() });

      const previousList = queryClient.getQueryData<AppNotification[]>(
        notificationKeys.list(),
      );
      const previousCount = queryClient.getQueryData<number>(
        notificationKeys.unreadCount(),
      );

      queryClient.setQueryData<AppNotification[]>(
        notificationKeys.list(),
        (old) => old?.map((n) => (n.id === id ? { ...n, isRead: true } : n)),
      );

      const wasUnread = previousList?.find((n) => n.id === id)?.isRead === false;
      if (wasUnread && typeof previousCount === "number") {
        queryClient.setQueryData<number>(
          notificationKeys.unreadCount(),
          Math.max(0, previousCount - 1),
        );
      }

      return { previousList, previousCount };
    },

    onError: (_err, _id, context) => {
      if (context?.previousList) {
        queryClient.setQueryData(notificationKeys.list(), context.previousList);
      }
      if (typeof context?.previousCount === "number") {
        queryClient.setQueryData(
          notificationKeys.unreadCount(),
          context.previousCount,
        );
      }
    },

    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}
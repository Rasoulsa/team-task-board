import { useQuery } from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import { notificationKeys } from "./queryKeys";

export function useUnreadCount() {
  return useQuery({
    queryKey: notificationKeys.unreadCount(),
    queryFn: () => container.notificationService.unreadCount(),
    staleTime: 30_000,
  });
}
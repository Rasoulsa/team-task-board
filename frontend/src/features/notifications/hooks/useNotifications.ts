import { useQuery } from "@tanstack/react-query";

import { container } from "../../../core/di/container";
import { notificationKeys } from "./queryKeys";

export function useNotifications() {
  return useQuery({
    queryKey: notificationKeys.list(),
    queryFn: () => container.notificationService.list(),
  });
}
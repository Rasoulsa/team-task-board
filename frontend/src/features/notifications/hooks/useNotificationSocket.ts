import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useAuthStore } from "../../auth/store/authStore";
import { SocketClient } from "../../realtime/SocketClient";
import { notificationKeys } from "./queryKeys";

interface NotificationSocketPayload {
  id: string;
  title: string;
  unread_count: number;
}

interface NotificationMessage {
  type: string;
  user_id: string;
  payload: NotificationSocketPayload;
}

function buildUrl(token: string): string {
  const base = (import.meta.env.VITE_WS_URL as string).replace(/\/+$/, "");
  return `${base}/notifications?token=${encodeURIComponent(token)}`;
}

export function useNotificationSocket(): void {
  const queryClient = useQueryClient();
  const token = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    if (!token) {
      return;
    }

    const client = new SocketClient(buildUrl(token));

    const unsubscribe = client.onMessage((raw) => {
      const message = raw as NotificationMessage;
      if (message.type !== "notification.created") {
        return;
      }

      queryClient.setQueryData(
        notificationKeys.unreadCount(),
        message.payload.unread_count,
      );
      void queryClient.invalidateQueries({ queryKey: notificationKeys.list() });
    });

    client.connect();

    return () => {
      unsubscribe();
      client.close();
    };
  }, [token, queryClient]);
}
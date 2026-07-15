import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useAuthStore } from "../auth/store/authStore";
import { cardQueryKeys } from "../cards/hooks/queryKeys";
import { SocketClient } from "./SocketClient";

interface RealtimeMessage {
  type: string;
  board_id: string;
  actor_id: string;
  payload: Record<string, unknown>;
}

function buildUrl(boardId: string, token: string): string {
  const configuredBase = import.meta.env.VITE_WS_URL as string | undefined;

  if (!configuredBase) {
    throw new Error("VITE_WS_URL is not configured");
  }

  const base = configuredBase.replace(/\/+$/, "");

  return `${base}/boards/${boardId}?token=${encodeURIComponent(token)}`;
}

export function useBoardSocket(boardId: string): void {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const currentUserId = useAuthStore((state) => state.user?.id ?? null);

  useEffect(() => {
    if (!boardId || !token) {
      return;
    }

    const url = buildUrl(boardId, token);
    const client = new SocketClient(url);

    const unsubscribe = client.onMessage((raw) => {
      const message = raw as RealtimeMessage;

      // Presence events do not affect card data.
      if (message.type.startsWith("presence.")) {
        return;
      }

      // Ignore events triggered by the current user. The local
      // optimistic update already reflects the change, so refetching
      // here would be redundant and can cause a visual flicker.
      if (currentUserId !== null && message.actor_id === currentUserId) {
        return;
      }

      void queryClient.invalidateQueries({
        queryKey: cardQueryKeys.board(boardId),
      });
    });

    client.connect();

    return () => {
      unsubscribe();
      client.close();
    };
  }, [boardId, token, currentUserId, queryClient]);
}
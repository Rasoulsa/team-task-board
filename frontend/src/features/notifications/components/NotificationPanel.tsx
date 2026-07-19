import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { container } from "../../../core/di/container";
import type { AppNotification } from "../domain/types";
import { useMarkAllRead } from "../hooks/useMarkAllRead";
import { useMarkRead } from "../hooks/useMarkRead";
import { useNotifications } from "../hooks/useNotifications";

interface Props {
  onClose: () => void;
}

export function NotificationPanel({
  onClose,
}: Props) {
  const navigate = useNavigate();

  const {
    data: notifications = [],
    isLoading,
  } = useNotifications();

  const markAllRead = useMarkAllRead();
  const markRead = useMarkRead();

  const [openingId, setOpeningId] = useState<
    string | null
  >(null);

  const [navigationError, setNavigationError] =
    useState(false);

  async function handleItemClick(
    notification: AppNotification,
  ) {
    if (!notification.isRead) {
      markRead.mutate(notification.id);
    }

    if (!notification.boardId) {
      return;
    }

    setOpeningId(notification.id);
    setNavigationError(false);

    try {
      /*
       * Notifications contain boardId and cardId, but the
       * frontend route also requires projectId. Retrieve the
       * board to resolve its project.
       */
      const board =
        await container.boardService.getBoard(
          notification.boardId,
        );

      const cardQuery = notification.cardId
        ? `?card=${encodeURIComponent(
            notification.cardId,
          )}`
        : "";

      navigate(
        `/projects/${board.project_id}/boards/${notification.boardId}${cardQuery}`,
      );

      onClose();
    } catch {
      setNavigationError(true);
    } finally {
      setOpeningId(null);
    }
  }

  return (
    <div className="absolute right-0 z-50 mt-2 w-80 rounded-lg border border-slate-700 bg-slate-900 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2">
        <span className="text-sm font-semibold text-slate-200">
          Notifications
        </span>

        <button
          type="button"
          onClick={() => markAllRead.mutate()}
          disabled={markAllRead.isPending}
          className="text-xs text-sky-400 hover:underline disabled:opacity-50"
        >
          {markAllRead.isPending
            ? "Marking…"
            : "Mark all read"}
        </button>
      </div>

      {navigationError ? (
        <p
          role="alert"
          className="border-b border-red-900 bg-red-950/40 px-4 py-2 text-xs text-red-300"
        >
          Unable to open the related board.
        </p>
      ) : null}

      <div className="max-h-96 overflow-y-auto">
        {isLoading ? (
          <p className="p-4 text-sm text-slate-400">
            Loading…
          </p>
        ) : notifications.length === 0 ? (
          <p className="p-4 text-sm text-slate-400">
            No notifications yet.
          </p>
        ) : (
          notifications.map((notification) => {
            const isOpening =
              openingId === notification.id;

            return (
              <button
                type="button"
                key={notification.id}
                disabled={isOpening}
                onClick={() => {
                  void handleItemClick(
                    notification,
                  );
                }}
                className={`block w-full border-b border-slate-800 px-4 py-3 text-left text-sm transition hover:bg-slate-800 disabled:cursor-wait disabled:opacity-70 ${
                  notification.isRead
                    ? "text-slate-400"
                    : "text-slate-100"
                }`}
              >
                <p className="font-medium">
                  {notification.title}
                </p>

                <p className="text-xs text-slate-400">
                  {notification.body}
                </p>

                {isOpening ? (
                  <p className="mt-1 text-xs text-sky-400">
                    Opening card…
                  </p>
                ) : null}
              </button>
            );
          })
        )}
      </div>

      <button
        type="button"
        onClick={onClose}
        className="w-full border-t border-slate-700 py-2 text-xs text-slate-400 hover:bg-slate-800"
      >
        Close
      </button>
    </div>
  );
}
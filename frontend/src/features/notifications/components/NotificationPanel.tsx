import { useNotifications } from "../hooks/useNotifications";
import { useMarkAllRead } from "../hooks/useMarkAllRead";
import { useMarkRead } from "../hooks/useMarkRead";

interface Props {
  onClose: () => void;
}

export function NotificationPanel({ onClose }: Props) {
  const { data: notifications = [], isLoading } = useNotifications();
  const markAllRead = useMarkAllRead();
  const markRead = useMarkRead();

  const handleItemClick = (id: string, isRead: boolean) => {
    if (!isRead) {
      markRead.mutate(id);
    }
  };

  return (
    <div className="absolute right-0 z-50 mt-2 w-80 rounded-lg border border-slate-700 bg-slate-900 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2">
        <span className="text-sm font-semibold text-slate-200">
          Notifications
        </span>
        <button
          type="button"
          onClick={() => markAllRead.mutate()}
          className="text-xs text-sky-400 hover:underline"
        >
          Mark all read
        </button>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {isLoading ? (
          <p className="p-4 text-sm text-slate-400">Loading…</p>
        ) : notifications.length === 0 ? (
          <p className="p-4 text-sm text-slate-400">No notifications yet.</p>
        ) : (
          notifications.map((n) => (
            <button
              type="button"
              key={n.id}
              onClick={() => handleItemClick(n.id, n.isRead)}
              className={`block w-full border-b border-slate-800 px-4 py-3 text-left text-sm transition hover:bg-slate-800 ${
                n.isRead ? "text-slate-400" : "text-slate-100"
              }`}
            >
              <p className="font-medium">{n.title}</p>
              <p className="text-xs text-slate-400">{n.body}</p>
            </button>
          ))
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
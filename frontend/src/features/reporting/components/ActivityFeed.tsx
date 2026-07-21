import { useBoardActivity } from "../hooks/useBoardActivity";

interface Props {
  boardId: string;
}

export function ActivityFeed({ boardId }: Props) {
  const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useBoardActivity(boardId);

  if (isLoading) return <div className="p-4">Loading activity…</div>;
  if (isError) return <div className="p-4 text-red-600">Failed to load activity.</div>;

  const items = data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <div className="space-y-2 p-4">
      <h3 className="font-semibold">Activity</h3>
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item.id} className="rounded border bg-white p-2 text-sm">
            <span className="font-medium">{item.actor_name ?? "Someone"}</span>{" "}
            <span className="text-gray-600">{item.action.replace("card.", "")}</span>{" "}
            <span className="text-gray-400">
              · {new Date(item.created_at).toLocaleString()}
            </span>
          </li>
        ))}
      </ul>
      {hasNextPage && (
        <button
          className="mt-2 rounded bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
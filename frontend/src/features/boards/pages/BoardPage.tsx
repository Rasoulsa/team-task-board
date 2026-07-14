import { Link, useParams } from 'react-router-dom';

import { KanbanBoard } from '../../cards/components/KanbanBoard';

export function BoardPage() {
  const { projectId, boardId } = useParams<{
    projectId: string;
    boardId: string;
  }>();

  if (!projectId || !boardId) {
    return (
      <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5 text-red-300">
        Missing project or board id.
      </div>
    );
  }

  return (
    <div className="min-w-0">
      <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-2xl font-bold">Kanban board</h1>
          <p className="mt-1 text-sm text-slate-400">
            Drag cards between columns, update their details, and manage work.
          </p>
        </div>

        <Link
          to={`/projects/${projectId}/boards`}
          className="w-fit rounded-lg bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700"
        >
          Back to boards
        </Link>
      </div>

      <KanbanBoard boardId={boardId} />
    </div>
  );
}
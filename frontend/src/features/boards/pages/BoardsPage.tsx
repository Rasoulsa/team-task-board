import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type SyntheticEvent } from 'react';
import { Link, useParams } from 'react-router-dom';

import { container } from '../../../core/di/container';

export function BoardsPage() {
  const queryClient = useQueryClient();
  const { projectId } = useParams<{ projectId: string }>();

  const [name, setName] = useState('Demo Board');
  const [description, setDescription] = useState(
    'Board created from the app shell.',
  );

  const boardsQuery = useQuery({
    queryKey: ['boards', projectId],
    queryFn: () => container.boardService.listBoards(projectId ?? ''),
    enabled: Boolean(projectId),
  });

  const boards = boardsQuery.data ?? [];

  const createBoardMutation = useMutation({
    mutationFn: () =>
      container.boardService.createBoard(projectId ?? '', {
        name,
        description: description.trim() ? description : null,
      }),
    onSuccess: async () => {
      setName('');
      setDescription('');

      await queryClient.invalidateQueries({
        queryKey: ['boards', projectId],
      });
    },
  });

  const deleteBoardMutation = useMutation({
    mutationFn: (boardId: string) => container.boardService.deleteBoard(boardId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ['boards', projectId],
      });
    },
  });

  async function handleCreateBoard(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!projectId) {
      return;
    }

    await createBoardMutation.mutateAsync();
  }

  async function handleDeleteBoard(boardId: string) {
    const confirmed = window.confirm('Delete this board?');

    if (!confirmed) {
      return;
    }

    await deleteBoardMutation.mutateAsync(boardId);
  }

  if (!projectId) {
    return (
      <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5 text-red-300">
        Missing project id.
      </div>
    );
  }

  const errorMessage =
    boardsQuery.isError
      ? 'Could not load boards.'
      : createBoardMutation.isError
        ? 'Could not create board.'
        : deleteBoardMutation.isError
          ? 'Could not delete board.'
          : null;

  const isLoading =
    boardsQuery.isLoading ||
    createBoardMutation.isPending ||
    deleteBoardMutation.isPending;

  return (
    <div>
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-2xl font-bold">Boards</h1>
          <p className="mt-1 text-sm text-slate-400">
            Manage boards for the selected project.
          </p>
        </div>

        <Link
          to="/projects"
          className="rounded-lg bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700"
        >
          Back to projects
        </Link>
      </div>

      {errorMessage ? (
        <div className="mt-4 rounded-lg border border-red-900 bg-red-950/40 p-3 text-sm text-red-300">
          {errorMessage}
        </div>
      ) : null}

      <form
        onSubmit={(event) => void handleCreateBoard(event)}
        className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-5"
      >
        <h2 className="text-lg font-semibold">Create board</h2>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="boardName" className="text-sm text-slate-300">
              Name
            </label>

            <input
              id="boardName"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
              required
              minLength={2}
            />
          </div>

          <div>
            <label
              htmlFor="boardDescription"
              className="text-sm text-slate-300"
            >
              Description
            </label>

            <input
              id="boardDescription"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={createBoardMutation.isPending || !name.trim()}
          className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {createBoardMutation.isPending ? 'Saving...' : 'Create board'}
        </button>
      </form>

      <section className="mt-6">
        <h2 className="text-lg font-semibold">Board list</h2>

        {isLoading ? (
          <p className="mt-4 text-sm text-slate-400">Loading...</p>
        ) : null}

        {!isLoading && boards.length === 0 ? (
          <div className="mt-4 rounded-2xl border border-dashed border-slate-700 p-8 text-center">
            <p className="text-slate-300">No boards yet.</p>
            <p className="mt-1 text-sm text-slate-500">
              Create a board to start managing cards with the Kanban UI.
            </p>
          </div>
        ) : null}

        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {boards.map((board) => (
            <article
              key={board.id}
              className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
            >
              <h3 className="font-semibold">{board.name}</h3>

              <p className="mt-2 min-h-10 text-sm text-slate-400">
                {board.description || 'No description'}
              </p>

              <div className="mt-4 flex items-center gap-2">
                <Link
                to={`/projects/${projectId}/boards/${board.id}`}
                className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-500"
                >
                  Open Kanban
                </Link>

                <button
                  type="button"
                  onClick={() => void handleDeleteBoard(board.id)}
                  disabled={deleteBoardMutation.isPending}
                  className="rounded-lg bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
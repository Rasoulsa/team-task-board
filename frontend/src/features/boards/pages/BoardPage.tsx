import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { isViewerOrGuest } from "../../../core/domain/roles";
import { KanbanBoard } from "../../cards/components/KanbanBoard";
import { useBoardMembers } from "../../cards/hooks/useBoardMembers";
import { useMyOrgRole } from "../hooks/useMyOrgRole";
import { OrganizationMembersModal } from "../../organizations/components/OrganizationMembersModal";

export function BoardPage() {
  const { projectId, boardId } = useParams<{
    projectId: string;
    boardId: string;
  }>();

  const [showMembers, setShowMembers] = useState(false);

  const boardMembers = useBoardMembers(boardId ?? "");

  const organizationId =
    boardMembers.data?.[0]?.organization_id ?? "";

  const myRole = useMyOrgRole(organizationId);

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

        <div className="flex w-fit gap-2">
          <button
            type="button"
            onClick={() => setShowMembers(true)}
            disabled={!organizationId}
            className="rounded-lg bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700 disabled:opacity-50"
          >
            Manage members
          </button>

          <Link
            to={`/projects/${projectId}/boards`}
            className="rounded-lg bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700"
          >
            Back to boards
          </Link>
        </div>
      </div>

      <KanbanBoard
        boardId={boardId}
        readOnlyExceptDescription={isViewerOrGuest(myRole)}
      />

      {showMembers && organizationId ? (
        <OrganizationMembersModal
          organizationId={organizationId}
          onClose={() => setShowMembers(false)}
        />
      ) : null}
    </div>
  );
}
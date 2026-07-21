import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { isViewerOrGuest } from "../../../core/domain/roles";
import { KanbanBoard } from "../../cards/components/KanbanBoard";
import { useBoardMembers } from "../../cards/hooks/useBoardMembers";
import { useMyOrgRole } from "../hooks/useMyOrgRole";
import { OrganizationMembersModal } from "../../organizations/components/OrganizationMembersModal";
import { StatsDashboard } from "../../reporting/pages/StatsDashboard";
import { ActivityFeed } from "../../reporting/components/ActivityFeed";

type Tab = "board" | "stats" | "activity";

const TABS: { key: Tab; label: string }[] = [
  { key: "board", label: "Board" },
  { key: "stats", label: "Stats" },
  { key: "activity", label: "Activity" },
];

export function BoardPage() {
  const { projectId, boardId } = useParams<{
    projectId: string;
    boardId: string;
  }>();

  const [showMembers, setShowMembers] = useState(false);
  const [tab, setTab] = useState<Tab>("board");

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

      <div className="mb-4 flex gap-1 border-b border-slate-800">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm font-medium transition ${
              tab === key
                ? "border-b-2 border-indigo-500 text-indigo-400"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "board" ? (
        <KanbanBoard
          boardId={boardId}
          readOnlyExceptDescription={isViewerOrGuest(myRole)}
        />
      ) : null}

      {tab === "stats" ? <StatsDashboard boardId={boardId} /> : null}

      {tab === "activity" ? <ActivityFeed boardId={boardId} /> : null}

      {showMembers && organizationId ? (
        <OrganizationMembersModal
          organizationId={organizationId}
          onClose={() => setShowMembers(false)}
        />
      ) : null}
    </div>
  );
}
import { useState } from "react";
import { AxiosError } from "axios";

import type { OrganizationRole } from "../domain/types";
import { useInviteOrganizationMember } from "../hooks/useInviteOrganizationMember";
import { useOrganizationMembers } from "../hooks/useOrganizationMembers";

interface OrganizationMembersModalProps {
  organizationId: string;
  onClose: () => void;
}

const roles: OrganizationRole[] = [
  "admin",
  "member",
  "viewer",
  "guest",
];

export function OrganizationMembersModal({
  organizationId,
  onClose,
}: OrganizationMembersModalProps) {
  const members = useOrganizationMembers(organizationId);
  const invite = useInviteOrganizationMember();

  const [email, setEmail] = useState("");
  const [role, setRole] =
    useState<OrganizationRole>("guest");
  const [message, setMessage] =
    useState<string | null>(null);
  const [isSuccess, setIsSuccess] =
    useState(false);

  async function handleInvite() {
    const normalizedEmail = email.trim();
    setMessage(null);
    setIsSuccess(false);

    if (!normalizedEmail) {
      return;
    }

    try {
      await invite.mutateAsync({
        organizationId,
        input: { email: normalizedEmail, role },
      });
      setEmail("");
      setIsSuccess(true);
      setMessage(
        "Invitation sent. The user must accept it to gain access.",
      );
    } catch (error) {
      if (error instanceof AxiosError) {
        if (error.response?.status === 409) {
          setMessage(
            "A pending invitation already exists, or the user is already a member.",
          );
          return;
        }
      }
      setMessage(
        "Unable to send the invitation. Please try again.",
      );
    }
  }

  return (
    <div
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
      className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 p-4"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="org-members-title"
        className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"
      >
        <h2
          id="org-members-title"
          className="text-xl font-bold text-slate-100"
        >
          Organization members
        </h2>

        <section className="mt-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Invite a member
          </h3>

          <label className="mt-3 block text-sm text-slate-300">
            Email
            <input
              type="email"
              value={email}
              placeholder="user@example.com"
              onChange={(event) =>
                setEmail(event.target.value)
              }
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
            />
          </label>

          <label className="mt-3 block text-sm text-slate-300">
            Role
            <select
              value={role}
              onChange={(event) =>
                setRole(
                  event.target.value as OrganizationRole,
                )
              }
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
            >
              {roles.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <p className="mt-1 text-xs text-slate-500">
            Guests can only open cards they are
            assigned to and edit the description.
          </p>

          <button
            type="button"
            onClick={() => void handleInvite()}
            disabled={
              invite.isPending ||
              email.trim().length === 0
            }
            className="mt-4 w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {invite.isPending
              ? "Sending…"
              : "Send invite"}
          </button>

          {message ? (
            <p
              className={
                isSuccess
                  ? "mt-2 rounded-lg border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-300"
                  : "mt-2 rounded-lg border border-amber-900 bg-amber-950/40 px-3 py-2 text-sm text-amber-300"
              }
            >
              {message}
            </p>
          ) : null}
        </section>

        <section className="mt-6">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Current members
          </h3>

          {members.isLoading ? (
            <p className="mt-3 text-sm text-slate-400">
              Loading members…
            </p>
          ) : members.isError ? (
            <p
              role="alert"
              className="mt-3 text-sm text-red-300"
            >
              Unable to load members.
            </p>
          ) : members.data?.length ? (
            <ul className="mt-3 space-y-2">
              {members.data.map((member) => {
                const displayName =
                  member.full_name?.trim() ||
                  member.email;

                return (
                  <li
                    key={member.user_id}
                    className="flex items-center gap-3 rounded-lg border border-slate-700 bg-slate-800/50 p-2"
                  >
                    <span
                      title={displayName}
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white"
                    >
                      {displayName
                        .charAt(0)
                        .toUpperCase()}
                    </span>

                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium text-slate-200">
                        {member.full_name}
                      </span>
                      <span className="block truncate text-xs text-slate-400">
                        {member.email}
                      </span>
                    </span>

                    <span className="shrink-0 rounded-full bg-slate-700 px-2 py-0.5 text-xs text-slate-300">
                      {member.role}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-slate-400">
              No members yet.
            </p>
          )}
        </section>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
import { useState } from "react";

import { useAddAssignee } from "../hooks/useAddAssignee";
import { useBoardMembers } from "../hooks/useBoardMembers";
import { useRemoveAssignee } from "../hooks/useRemoveAssignee";

import type { Card, CardPriority } from "../domain/types";
import { useUpdateCard } from "../hooks/useUpdateCard";

interface CardModalProps {
  boardId: string;
  card: Card;
  onClose: () => void;
  onDelete: (card: Card) => void;
  readOnlyExceptDescription?: boolean;
}

const priorities: CardPriority[] = [
  "low",
  "medium",
  "high",
  "urgent",
];

export function CardModal({
  boardId,
  card,
  onClose,
  onDelete,
  readOnlyExceptDescription = false,
}: CardModalProps) {
  const isGuest = readOnlyExceptDescription;

  const updateCard = useUpdateCard(boardId);

  const boardMembers = useBoardMembers(boardId);
  const addAssignee = useAddAssignee(boardId);
  const removeAssignee = useRemoveAssignee(boardId);

  const isUpdatingAssignees =
    addAssignee.isPending ||
    removeAssignee.isPending;

  const checklist = Array.isArray(card.checklist)
    ? card.checklist
    : [];

  const labels = Array.isArray(card.labels)
    ? card.labels
    : [];

  const assignees = Array.isArray(card.assignees)
    ? card.assignees
    : [];

  const [title, setTitle] = useState(card.title);

  const [description, setDescription] = useState(
    card.description ?? "",
  );

  const [priority, setPriority] =
    useState<CardPriority>(card.priority);

  const [dueDate, setDueDate] = useState(
    card.due_date?.slice(0, 10) ?? "",
  );

  async function handleAssigneeChange(
    userId: string,
    isAssigned: boolean,
  ) {
    try {
      if (isAssigned) {
        await removeAssignee.mutateAsync({
          cardId: card.id,
          userId,
        });

        return;
      }

      await addAssignee.mutateAsync({
        cardId: card.id,
        userId,
      });
    } catch {
      // The mutation error is rendered below.
    }
  }

  async function save() {
    // Guests may update only the description.
    if (isGuest) {
      try {
        await updateCard.mutateAsync({
          cardId: card.id,
          payload: {
            description:
              description.trim() || null,
          },
        });

        onClose();
      } catch {
        // Error surfaced via updateCard.isError.
      }

      return;
    }

    const normalizedTitle = title.trim();

    if (!normalizedTitle) {
      return;
    }

    try {
      await updateCard.mutateAsync({
        cardId: card.id,
        payload: {
          title: normalizedTitle,
          description: description.trim() || null,
          priority,
          due_date: dueDate
            ? new Date(
                `${dueDate}T00:00:00.000Z`,
              ).toISOString()
            : null,
        },
      });

      onClose();
    } catch {
      // React Query exposes the error via updateCard.isError.
    }
  }

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="card-modal-title"
      >
        <h2 id="card-modal-title">
          {isGuest ? "Card" : "Edit card"}
        </h2>

        <label>
          Title
          <input
            value={title}
            readOnly={isGuest}
            disabled={isGuest}
            onChange={(event) =>
              setTitle(event.target.value)
            }
          />
        </label>

        <label>
          Description
          <textarea
            value={description}
            onChange={(event) =>
              setDescription(event.target.value)
            }
          />
        </label>

        <label>
          Priority
          {isGuest ? (
            <input
              value={priority}
              readOnly
              disabled
            />
          ) : (
            <select
              value={priority}
              onChange={(event) =>
                setPriority(
                  event.target
                    .value as CardPriority,
                )
              }
            >
              {priorities.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          )}
        </label>

        <label>
          Due date
          <input
            type="date"
            value={dueDate}
            readOnly={isGuest}
            disabled={isGuest}
            onChange={(event) =>
              setDueDate(event.target.value)
            }
          />
        </label>

        <section className="modal__checklist">
          <h3>Checklist</h3>

          {checklist.length > 0 ? (
            <ul>
              {checklist.map((item) => (
                <li key={item.id}>
                  <input
                    type="checkbox"
                    checked={item.is_done}
                    readOnly
                  />
                  <span>{item.content}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p>No checklist items.</p>
          )}
        </section>

        <section className="modal__labels">
          <h3>Labels</h3>

          {labels.length > 0 ? (
            <div>
              {labels.map((label) => (
                <span
                  key={label.id}
                  className="label-chip"
                  style={{
                    backgroundColor: label.color,
                  }}
                >
                  {label.name}
                </span>
              ))}
            </div>
          ) : (
            <p>No labels.</p>
          )}
        </section>

        {/* Assignee management is hidden for guests. */}
        {!isGuest ? (
          <section className="modal__assignees">
            <h3>Assignees</h3>

            {boardMembers.isLoading ? (
              <p>Loading board members…</p>
            ) : boardMembers.isError ? (
              <p role="alert">
                Unable to load board members.
              </p>
            ) : boardMembers.data?.length ? (
              <div className="space-y-2">
                {boardMembers.data.map(
                  (member) => {
                    const isAssigned =
                      assignees.some(
                        (assignee) =>
                          assignee.user_id ===
                          member.user_id,
                      );

                    const displayName =
                      member.full_name?.trim() ||
                      member.email ||
                      "Unknown user";

                    return (
                      <label
                        key={member.user_id}
                        className="flex cursor-pointer items-center gap-3 rounded-md border border-slate-700 p-2 hover:bg-slate-800"
                      >
                        <input
                          type="checkbox"
                          checked={isAssigned}
                          disabled={
                            isUpdatingAssignees
                          }
                          onChange={() => {
                            void handleAssigneeChange(
                              member.user_id,
                              isAssigned,
                            );
                          }}
                        />

                        <span
                          className="avatar"
                          title={displayName}
                        >
                          {displayName
                            .charAt(0)
                            .toUpperCase()}
                        </span>

                        <span className="min-w-0">
                          <span className="block text-sm font-medium text-slate-200">
                            {member.full_name}
                          </span>

                          <span className="block truncate text-xs text-slate-400">
                            {member.email}
                          </span>
                        </span>
                      </label>
                    );
                  },
                )}
              </div>
            ) : (
              <p>No board members available.</p>
            )}

            {addAssignee.isError ? (
              <p role="alert">
                Unable to add the assignee.
              </p>
            ) : null}

            {removeAssignee.isError ? (
              <p role="alert">
                Unable to remove the assignee.
              </p>
            ) : null}
          </section>
        ) : null}

        {updateCard.isError ? (
          <p role="alert">
            Unable to update the card. Please try
            again.
          </p>
        ) : null}

        <div className="modal__actions">
          {/* Guests cannot delete. */}
          {!isGuest ? (
            <button
              type="button"
              className="modal__delete"
              onClick={() => onDelete(card)}
              disabled={updateCard.isPending}
            >
              Delete
            </button>
          ) : null}

          <button
            type="button"
            className="modal__cancel"
            onClick={onClose}
            disabled={updateCard.isPending}
          >
            Cancel
          </button>

          <button
            type="button"
            className="modal__save"
            onClick={() => void save()}
            disabled={
              updateCard.isPending ||
              (!isGuest &&
                title.trim().length === 0)
            }
          >
            {updateCard.isPending
              ? "Saving…"
              : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
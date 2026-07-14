import { useState } from "react";

import type {
  Card,
  CardPriority,
} from "../domain/types";
import { useUpdateCard } from "../hooks/useUpdateCard";

interface CardModalProps {
  boardId: string;
  card: Card;
  onClose: () => void;
  onDelete: (card: Card) => void;
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
}: CardModalProps) {
  const updateCard = useUpdateCard(boardId);

  /*
   * API responses are normalized in HttpCardRepository before they
   * reach the domain and presentation layers. These checks provide
   * additional protection against malformed cached data.
   */
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

  async function save() {
    const normalizedTitle = title.trim();

    if (!normalizedTitle) {
      return;
    }

    try {
      await updateCard.mutateAsync({
        cardId: card.id,
        payload: {
          title: normalizedTitle,
          description:
            description.trim() || null,
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
      /*
       * React Query exposes the error through updateCard.isError.
       * Keep the modal open so the user can retry.
       */
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
        <h2 id="card-modal-title">Edit card</h2>

        <label>
          Title
          <input
            value={title}
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
        </label>

        <label>
          Due date
          <input
            type="date"
            value={dueDate}
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
                    backgroundColor:
                      label.color,
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

        <section className="modal__assignees">
          <h3>Assignees</h3>

          {assignees.length > 0 ? (
            <div>
              {assignees.map((assignee) => (
                <span key={assignee.id}>
                  {assignee.user_id}
                </span>
              ))}
            </div>
          ) : (
            <p>No assignees.</p>
          )}
        </section>

        {updateCard.isError ? (
          <p role="alert">
            Unable to update the card. Please
            try again.
          </p>
        ) : null}

        <div className="modal__actions">
          <button
            type="button"
            className="modal__delete"
            onClick={() => onDelete(card)}
            disabled={updateCard.isPending}
          >
            Delete
          </button>

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
              title.trim().length === 0
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
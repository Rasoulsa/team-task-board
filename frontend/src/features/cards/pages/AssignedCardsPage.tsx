import { useState } from "react";

import type { Card } from "../domain/types";
import { useAssignedCards } from "../hooks/useAssignedCards";
import { CardModal } from "../components/CardModal";

export function AssignedCardsPage() {
  const { data, isLoading, isError } =
    useAssignedCards();
  const [openCard, setOpenCard] =
    useState<Card | null>(null);

  if (isLoading) {
    return (
      <p className="p-6 text-sm text-slate-400">
        Loading your cards…
      </p>
    );
  }

  if (isError) {
    return (
      <p className="p-6 text-sm text-red-300">
        Unable to load your cards.
      </p>
    );
  }

  const cards = data ?? [];

  return (
    <div className="min-w-0 p-6">
      <h1 className="mb-4 text-2xl font-bold text-slate-100">
        Cards assigned to you
      </h1>

      {cards.length === 0 ? (
        <p className="text-sm text-slate-400">
          You have no assigned cards yet.
        </p>
      ) : (
        <ul className="space-y-2">
          {cards.map((card) => (
            <li key={card.id}>
              <button
                type="button"
                onClick={() => setOpenCard(card)}
                className="w-full rounded-lg border border-slate-700 bg-slate-800/50 p-3 text-left hover:bg-slate-800"
              >
                <span className="block text-sm font-medium text-slate-200">
                  {card.title}
                </span>
                {card.due_date ? (
                  <span className="block text-xs text-slate-400">
                    Due:{" "}
                    {new Date(
                      card.due_date,
                    ).toLocaleString()}
                  </span>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
      )}

      {openCard ? (
        <CardModal
          key={openCard.id}
          boardId=""
          card={openCard}
          onClose={() => setOpenCard(null)}
          onDelete={() => setOpenCard(null)}
          readOnlyExceptDescription
        />
      ) : null}
    </div>
  );
}
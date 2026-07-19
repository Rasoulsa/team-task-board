import { useQuery } from "@tanstack/react-query";

import { fetchAssignedCards } from "../api/assignedCards";

export function useAssignedCards() {
  return useQuery({
    queryKey: ["assigned-cards"],
    queryFn: fetchAssignedCards,
  });
}
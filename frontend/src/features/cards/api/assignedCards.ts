import { apiClient } from "../../../core/http/client";
import type { Card } from "../domain/types";

export async function fetchAssignedCards(): Promise<Card[]> {
  const response =
    await apiClient.get<Card[]>("/me/assigned-cards");
  return response.data;
}
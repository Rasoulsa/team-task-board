import { apiClient } from "../../../core/http/client";
import type {
  BoardDetail,
  Card,
  CardAssignee,
  CreateCardInput,
  MoveCardInput,
  MoveCardResult,
  UpdateCardInput,
} from "./types";

export interface CardRepository {
  getBoard(boardId: string): Promise<BoardDetail>;

  createCard(
    columnId: string,
    input: CreateCardInput,
  ): Promise<Card>;

  updateCard(
    cardId: string,
    input: UpdateCardInput,
  ): Promise<Card>;

  moveCard(
    cardId: string,
    input: MoveCardInput,
  ): Promise<MoveCardResult>;

  deleteCard(cardId: string): Promise<void>;

  addAssignee(
    cardId: string,
    userId: string,
  ): Promise<CardAssignee>;

  removeAssignee(
    cardId: string,
    userId: string,
  ): Promise<void>;
}

export async function fetchAssignedCards(): Promise<Card[]> {
  const response =
    await apiClient.get<Card[]>("/me/assigned-cards");
  return response.data;
}
import { axiosClient } from "../../../core/http/axiosClient";
import type { CardRepository } from "../domain/CardRepository";
import type {
  BoardDetail,
  Card,
  CreateCardInput,
  MoveCardInput,
  MoveCardResult,
  UpdateCardInput,
} from "../domain/types";
import type {
  BoardDetailApiResponse,
  CardApiResponse,
  MoveCardApiResponse,
} from "./cardApiTypes";
import {
  mapBoardDetailResponse,
  mapCardResponse,
  mapMoveCardResponse,
} from "./cardResponseMapper";

function assertBoardDetailApiResponse(
  value: unknown,
): asserts value is BoardDetailApiResponse {
  if (!value || typeof value !== "object") {
    throw new Error(
      "Invalid board response: expected an object.",
    );
  }

  const board = value as Record<string, unknown>;

  if (typeof board.id !== "string") {
    throw new Error(
      "Invalid board response: missing board id.",
    );
  }

  if (typeof board.name !== "string") {
    throw new Error(
      "Invalid board response: missing board name.",
    );
  }

  if (!Array.isArray(board.columns)) {
    throw new Error(
      "Invalid board response: expected board.columns to be an array.",
    );
  }
}

export class HttpCardRepository
  implements CardRepository
{
  async getBoard(
    boardId: string,
  ): Promise<BoardDetail> {
    const response = await axiosClient.get<unknown>(
      `/boards/${boardId}/kanban`,
    );

    assertBoardDetailApiResponse(response.data);

    return mapBoardDetailResponse(response.data);
  }

  async createCard(
    columnId: string,
    input: CreateCardInput,
  ): Promise<Card> {
    const response =
      await axiosClient.post<CardApiResponse>(
        `/columns/${columnId}/cards`,
        input,
      );

    return mapCardResponse(response.data);
  }

  async updateCard(
    cardId: string,
    input: UpdateCardInput,
  ): Promise<Card> {
    const response =
      await axiosClient.patch<CardApiResponse>(
        `/cards/${cardId}`,
        input,
      );

    return mapCardResponse(response.data);
  }

  async moveCard(
    cardId: string,
    input: MoveCardInput,
  ): Promise<MoveCardResult> {
    const response =
      await axiosClient.post<MoveCardApiResponse>(
        `/cards/${cardId}/move`,
        input,
      );

    return mapMoveCardResponse(response.data);
  }

  async deleteCard(cardId: string): Promise<void> {
    await axiosClient.delete(`/cards/${cardId}`);
  }
}
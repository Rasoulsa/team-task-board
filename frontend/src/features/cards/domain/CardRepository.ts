import type {
  BoardDetail,
  Card,
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
}
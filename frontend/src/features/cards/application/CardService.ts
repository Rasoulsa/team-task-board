import type { CardRepository } from "../domain/CardRepository";
import type {
  CreateCardInput,
  MoveCardInput,
  UpdateCardInput,
} from "../domain/types";

export class CardService {
  private readonly cardRepository: CardRepository;

  constructor(cardRepository: CardRepository) {
    this.cardRepository = cardRepository;
  }

  getBoard(boardId: string) {
    return this.cardRepository.getBoard(boardId);
  }

  createCard(
    columnId: string,
    input: CreateCardInput,
  ) {
    return this.cardRepository.createCard(
      columnId,
      input,
    );
  }

  updateCard(
    cardId: string,
    input: UpdateCardInput,
  ) {
    return this.cardRepository.updateCard(
      cardId,
      input,
    );
  }

  moveCard(
    cardId: string,
    input: MoveCardInput,
  ) {
    return this.cardRepository.moveCard(
      cardId,
      input,
    );
  }

  deleteCard(cardId: string) {
    return this.cardRepository.deleteCard(cardId);
  }
}
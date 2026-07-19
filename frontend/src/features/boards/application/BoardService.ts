import type { BoardRepository } from "../domain/BoardRepository";
import type {
  Board,
  BoardColumn,
  BoardMember,
  CreateBoardInput,
  CreateColumnInput,
  UpdateBoardInput,
} from "../domain/types";

export class BoardService {
  private readonly boardRepository: BoardRepository;

  constructor(boardRepository: BoardRepository) {
    this.boardRepository = boardRepository;
  }

  getBoard(boardId: string): Promise<Board> {
    return this.boardRepository.getBoard(boardId);
  }

  listBoards(projectId: string): Promise<Board[]> {
    return this.boardRepository.listBoards(projectId);
  }

  createBoard(
    projectId: string,
    input: CreateBoardInput,
  ): Promise<Board> {
    return this.boardRepository.createBoard(
      projectId,
      input,
    );
  }

  updateBoard(
    boardId: string,
    input: UpdateBoardInput,
  ): Promise<Board> {
    return this.boardRepository.updateBoard(
      boardId,
      input,
    );
  }

  deleteBoard(boardId: string): Promise<void> {
    return this.boardRepository.deleteBoard(boardId);
  }

  listMembers(boardId: string): Promise<BoardMember[]> {
    return this.boardRepository.listMembers(boardId);
  }

  listColumns(boardId: string): Promise<BoardColumn[]> {
    return this.boardRepository.listColumns(boardId);
  }

  createColumn(
    boardId: string,
    input: CreateColumnInput,
  ): Promise<BoardColumn> {
    return this.boardRepository.createColumn(
      boardId,
      input,
    );
  }
}
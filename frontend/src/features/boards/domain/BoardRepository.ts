import type {
  Board,
  BoardColumn,
  BoardMember,
  CreateBoardInput,
  CreateColumnInput,
  UpdateBoardInput,
} from "./types";

export interface BoardRepository {
  getBoard(boardId: string): Promise<Board>;

  listBoards(projectId: string): Promise<Board[]>;

  createBoard(
    projectId: string,
    input: CreateBoardInput,
  ): Promise<Board>;

  updateBoard(
    boardId: string,
    input: UpdateBoardInput,
  ): Promise<Board>;

  deleteBoard(boardId: string): Promise<void>;

  listMembers(boardId: string): Promise<BoardMember[]>;

  listColumns(boardId: string): Promise<BoardColumn[]>;

  createColumn(
    boardId: string,
    input: CreateColumnInput,
  ): Promise<BoardColumn>;
}
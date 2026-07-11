import type {
  Board,
  BoardColumn,
  CreateBoardInput,
  CreateColumnInput,
  UpdateBoardInput,
} from './types';

export interface BoardRepository {
  listBoards(projectId: string): Promise<Board[]>;
  createBoard(projectId: string, input: CreateBoardInput): Promise<Board>;
  updateBoard(boardId: string, input: UpdateBoardInput): Promise<Board>;
  deleteBoard(boardId: string): Promise<void>;

  listColumns(boardId: string): Promise<BoardColumn[]>;
  createColumn(
    boardId: string,
    input: CreateColumnInput,
  ): Promise<BoardColumn>;
}
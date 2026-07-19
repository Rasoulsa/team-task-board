import { apiClient } from "../../../core/http/client";
import type { BoardRepository } from "../domain/BoardRepository";
import type {
  Board,
  BoardColumn,
  BoardMember,
  CreateBoardInput,
  CreateColumnInput,
  UpdateBoardInput,
} from "../domain/types";

export class HttpBoardRepository
  implements BoardRepository
{
  async getBoard(boardId: string): Promise<Board> {
    const response = await apiClient.get<Board>(
      `/boards/${boardId}`,
    );

    return response.data;
  }

  async listBoards(projectId: string): Promise<Board[]> {
    const response = await apiClient.get<Board[]>(
      `/projects/${projectId}/boards`,
    );

    return response.data;
  }

  async createBoard(
    projectId: string,
    input: CreateBoardInput,
  ): Promise<Board> {
    const response = await apiClient.post<Board>(
      `/projects/${projectId}/boards`,
      input,
    );

    return response.data;
  }

  async updateBoard(
    boardId: string,
    input: UpdateBoardInput,
  ): Promise<Board> {
    const response = await apiClient.patch<Board>(
      `/boards/${boardId}`,
      input,
    );

    return response.data;
  }

  async deleteBoard(boardId: string): Promise<void> {
    await apiClient.delete(`/boards/${boardId}`);
  }

  async listMembers(
    boardId: string,
  ): Promise<BoardMember[]> {
    const response = await apiClient.get<BoardMember[]>(
      `/boards/${boardId}/members`,
    );

    return response.data;
  }

  async listColumns(
    boardId: string,
  ): Promise<BoardColumn[]> {
    const response = await apiClient.get<BoardColumn[]>(
      `/boards/${boardId}/columns`,
    );

    return response.data;
  }

  async createColumn(
    boardId: string,
    input: CreateColumnInput,
  ): Promise<BoardColumn> {
    const response = await apiClient.post<BoardColumn>(
      `/boards/${boardId}/columns`,
      input,
    );

    return response.data;
  }
}
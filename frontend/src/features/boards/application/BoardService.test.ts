import { describe, expect, it, vi } from 'vitest';

import { BoardService } from './BoardService';
import type { BoardRepository } from '../domain/BoardRepository';

describe('BoardService', () => {
  it('lists boards through repository', async () => {
    const repository: BoardRepository = {
      listBoards: vi.fn().mockResolvedValue([
        {
          id: 'board-id',
          project_id: 'project-id',
          name: 'Demo Board',
          description: null,
          created_at: '2026-07-11T00:00:00Z',
          updated_at: '2026-07-11T00:00:00Z',
        },
      ]),
      createBoard: vi.fn(),
      updateBoard: vi.fn(),
      deleteBoard: vi.fn(),
      listColumns: vi.fn(),
      createColumn: vi.fn(),
    };

    const service = new BoardService(repository);

    const boards = await service.listBoards('project-id');

    expect(boards).toHaveLength(1);
    expect(boards[0].name).toBe('Demo Board');
    expect(repository.listBoards).toHaveBeenCalledWith('project-id');
  });
});
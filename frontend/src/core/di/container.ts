import { AuthService } from '../../features/auth/application/AuthService';
import { HttpAuthRepository } from '../../features/auth/data/HttpAuthRepository';
import { BoardService } from '../../features/boards/application/BoardService';
import { HttpBoardRepository } from '../../features/boards/data/HttpBoardRepository';
import { ProjectService } from '../../features/projects/application/ProjectService';
import { HttpProjectRepository } from '../../features/projects/data/HttpProjectRepository';

const authRepository = new HttpAuthRepository();
const projectRepository = new HttpProjectRepository();
const boardRepository = new HttpBoardRepository();

export const container = {
  authService: new AuthService(authRepository),
  projectService: new ProjectService(projectRepository),
  boardService: new BoardService(boardRepository),
};
import { AuthService } from "../../features/auth/application/AuthService";
import { HttpAuthRepository } from "../../features/auth/data/HttpAuthRepository";
import { BoardService } from "../../features/boards/application/BoardService";
import { HttpBoardRepository } from "../../features/boards/data/HttpBoardRepository";
import { CardService } from "../../features/cards/application/CardService";
import { HttpCardRepository } from "../../features/cards/data/HttpCardRepository";
import { ProjectService } from "../../features/projects/application/ProjectService";
import { HttpProjectRepository } from "../../features/projects/data/HttpProjectRepository";
import { HttpNotificationRepository } from "../../features/notifications/data/HttpNotificationRepository";
import { NotificationService } from "../../features/notifications/application/NotificationService";

const authRepository = new HttpAuthRepository();
const projectRepository = new HttpProjectRepository();
const boardRepository = new HttpBoardRepository();
const cardRepository = new HttpCardRepository();
const notificationRepository = new HttpNotificationRepository();

export const container = {
  authService: new AuthService(authRepository),
  projectService: new ProjectService(projectRepository),
  boardService: new BoardService(boardRepository),
  cardService: new CardService(cardRepository),
  notificationService: new NotificationService(notificationRepository),
};

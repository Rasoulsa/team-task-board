export const cardQueryKeys = {
  all: ["cards"] as const,

  boards: () => [...cardQueryKeys.all, "boards"] as const,

  board: (boardId: string) => [...cardQueryKeys.boards(), boardId] as const,
};

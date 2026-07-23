import { test, expect, Page, BrowserContext } from "@playwright/test";

const unique = () =>
  Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

async function register(page: Page, email: string, password: string) {
  await page.goto("/register");
  await page.getByTestId("register-fullname").fill("Demo User");
  await page.getByTestId("register-organization").fill(`Org ${unique()}`);
  await page.getByTestId("register-email").fill(email);
  await page.getByTestId("register-password").fill(password);
  await page.getByTestId("register-submit").click();
  await expect(page).toHaveURL(/.*dashboard.*/, { timeout: 20_000 });
}

async function login(page: Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByTestId("login-email").fill(email);
  await page.getByTestId("login-password").fill(password);
  await page.getByTestId("login-submit").click();
  await expect(page).toHaveURL(/.*dashboard.*/, { timeout: 20_000 });
}

/** dnd-kit sortable: press, small move to activate, stepped move to target, release. */
async function dragCardToColumn(page: Page, cardId: string, columnId: string) {
  const card = page.locator(`[data-testid="card"][data-card-id="${cardId}"]`);
  const dropZone = page.locator(
    `[data-testid="column-body"][data-column-id="${columnId}"]`
  );
  await card.scrollIntoViewIfNeeded();
  const c = await card.boundingBox();
  const d = await dropZone.boundingBox();
  if (!c || !d) throw new Error("card or column body not visible");

  await page.mouse.move(c.x + c.width / 2, c.y + c.height / 2);
  await page.mouse.down();
  await page.mouse.move(c.x + c.width / 2, c.y + c.height / 2 + 12, { steps: 6 });
  await page.mouse.move(d.x + d.width / 2, d.y + Math.min(40, d.height / 2), {
    steps: 15,
  });
  await page.mouse.move(d.x + d.width / 2, d.y + Math.min(60, d.height / 2), {
    steps: 5,
  });
  await page.mouse.up();
}

test("register → project → board → card → drag → live update in 2nd session", async ({
  browser,
}) => {
  const email = `e2e_${unique()}@example.com`;
  const password = "Str0ng-Passw0rd!";

  // --- Session A ---
  const ctxA: BrowserContext = await browser.newContext();
  const a = await ctxA.newPage();
  await register(a, email, password);

  // Create project (form is always on the Projects page)
  await a.goto("/projects");
  const projectName = `Proj ${unique()}`;
  await a.getByTestId("project-name-input").fill(projectName);
  await a.getByTestId("project-submit").click();
  const project = a
    .getByTestId("project-item")
    .filter({ hasText: projectName });
  await expect(project).toBeVisible({ timeout: 15_000 });

  // Open its boards
  await project.getByTestId("open-boards-link").click();
  await expect(a).toHaveURL(/.*\/projects\/.*\/boards.*/);

  // Create board
  const boardName = `Board ${unique()}`;
  await a.getByTestId("board-name-input").fill(boardName);
  await a.getByTestId("board-submit").click();
  const board = a.getByTestId("board-item").filter({ hasText: boardName });
  await expect(board).toBeVisible({ timeout: 15_000 });

  // Open Kanban
  await board.getByTestId("open-kanban-link").click();
  await expect(a).toHaveURL(/.*\/boards\/.*/);

  // Columns must exist (board seeds default columns)
  const columns = a.locator('[data-testid="board-column"]');
  await expect(columns.first()).toBeVisible({ timeout: 20_000 });
  const firstColId = await columns.nth(0).getAttribute("data-column-id");
  const secondColId = await columns.nth(1).getAttribute("data-column-id");
  if (!firstColId || !secondColId) throw new Error("need >= 2 columns");

  // Add a card to the first column (inline form)
  const cardTitle = `Card ${unique()}`;
  const firstColumn = columns.nth(0);
  await firstColumn.getByTestId("add-card-input").fill(cardTitle);
  await firstColumn.getByTestId("add-card-submit").click();

  const cardLoc = a
    .locator('[data-testid="card"]')
    .filter({ hasText: cardTitle });
  await expect(cardLoc).toBeVisible({ timeout: 15_000 });
  const cardId = await cardLoc.getAttribute("data-card-id");
  if (!cardId) throw new Error("card id missing");

  const boardURL = a.url();

  // --- Session B: same user, second context on same board ---
  const ctxB: BrowserContext = await browser.newContext();
  const b = await ctxB.newPage();
  await login(b, email, password);
  await b.goto(boardURL);
  await expect(
    b.locator('[data-testid="card"]').filter({ hasText: cardTitle })
  ).toBeVisible({ timeout: 20_000 });

  // --- Drag in A ---
  await dragCardToColumn(a, cardId, secondColId);

  // A: card is now inside the second column's body
  await expect(
    a
      .locator(`[data-testid="column-body"][data-column-id="${secondColId}"]`)
      .locator(`[data-card-id="${cardId}"]`)
  ).toBeVisible({ timeout: 15_000 });

  // B: same move arrives over WebSocket without refresh
  await expect(
    b
      .locator(`[data-testid="column-body"][data-column-id="${secondColId}"]`)
      .locator(`[data-card-id="${cardId}"]`)
  ).toBeVisible({ timeout: 20_000 });

  await ctxA.close();
  await ctxB.close();
});
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { NotificationBell } from "./NotificationBell";
import * as hook from "../hooks/useUnreadCount";

describe("NotificationBell", () => {
  it("shows the unread badge", () => {
    vi.spyOn(hook, "useUnreadCount").mockReturnValue({
      data: 3,
    } as unknown as ReturnType<typeof hook.useUnreadCount>);

    render(
      <QueryClientProvider client={new QueryClient()}>
        <NotificationBell />
      </QueryClientProvider>,
    );

    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("hides the badge when unread count is zero", () => {
    vi.spyOn(hook, "useUnreadCount").mockReturnValue({
      data: 0,
    } as unknown as ReturnType<typeof hook.useUnreadCount>);

    render(
      <QueryClientProvider client={new QueryClient()}>
        <NotificationBell />
      </QueryClientProvider>,
    );

    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });
});
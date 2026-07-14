import { describe, expect, it } from "vitest";

import { DEFAULT_RANK, rankBetween } from "./lexorank";

describe("rankBetween", () => {
  it("returns the default rank without boundaries", () => {
    expect(rankBetween(null, null)).toBe(DEFAULT_RANK);
  });

  it("creates a rank after the previous rank", () => {
    const previous = "n";
    const result = rankBetween(previous, null);

    expect(result > previous).toBe(true);
  });

  it("creates a rank before the following rank", () => {
    const following = "n";
    const result = rankBetween(null, following);

    expect(result < following).toBe(true);
  });

  it("creates a rank between two ranks", () => {
    const previous = "a";
    const following = "c";
    const result = rankBetween(previous, following);

    expect(result > previous).toBe(true);
    expect(result < following).toBe(true);
  });

  it("rejects incorrectly ordered boundaries", () => {
    expect(() => rankBetween("c", "a")).toThrow(
      "previous must be strictly less than following",
    );
  });
});

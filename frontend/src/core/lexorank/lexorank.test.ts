import { describe, expect, it } from 'vitest';

import { DEFAULT_RANK, rankBetween } from './lexorank';

describe('rankBetween', () => {
  it('returns default when both are null', () => {
    expect(rankBetween(null, null)).toBe(DEFAULT_RANK);
  });

  it('returns a rank after previous', () => {
    const result = rankBetween('n', null);
    expect(result > 'n').toBe(true);
  });

  it('returns a rank before following', () => {
    const result = rankBetween(null, 'n');
    expect(result < 'n').toBe(true);
  });

  it('returns a strictly between rank', () => {
    const result = rankBetween('a', 'c');
    expect('a' < result && result < 'c').toBe(true);
  });

  it('handles adjacent ranks', () => {
    const result = rankBetween('a', 'b');
    expect('a' < result && result < 'b').toBe(true);
  });

  it('keeps order over many inserts', () => {
    const low = rankBetween(null, null);
    const high = rankBetween(low, null);

    const ordered = [low, high];

    for (let i = 0; i < 50; i += 1) {
      const mid = rankBetween(ordered[0], ordered[1]);
      expect(ordered[0] < mid && mid < ordered[1]).toBe(true);
      ordered.splice(1, 0, mid);
    }

    const sorted = [...ordered].sort();
    expect(ordered).toEqual(sorted);
  });

  it('throws on invalid order', () => {
    expect(() => rankBetween('c', 'a')).toThrow();
  });
});
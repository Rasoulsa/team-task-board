const BASE_DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz';
const BASE = BASE_DIGITS.length;

const MIN_CHAR = BASE_DIGITS[0];
const MAX_CHAR = BASE_DIGITS[BASE - 1];

export const DEFAULT_RANK = 'n';

function charToValue(char: string): number {
  return BASE_DIGITS.indexOf(char);
}

function valueToChar(value: number): string {
  return BASE_DIGITS[value];
}

function rankAfter(previous: string): string {
  for (let index = 0; index < previous.length; index += 1) {
    const char = previous[index];

    if (char !== MAX_CHAR) {
      const nextChar = valueToChar(charToValue(char) + 1);
      return previous.slice(0, index) + nextChar;
    }
  }

  return previous + DEFAULT_RANK;
}

function rankBefore(following: string): string {
  for (let index = 0; index < following.length; index += 1) {
    const char = following[index];

    if (char !== MIN_CHAR) {
      const prevChar = valueToChar(charToValue(char) - 1);
      const candidate = following.slice(0, index) + prevChar;

      if (candidate < following && candidate !== '') {
        return candidate;
      }
    }
  }

  return following + DEFAULT_RANK;
}

function rankMid(previous: string, following: string): string {
  if (previous >= following) {
    throw new Error('previous must be strictly less than following');
  }

  const maxLength = Math.max(previous.length, following.length);
  let result = '';

  for (let index = 0; index <= maxLength; index += 1) {
    const prevValue = index < previous.length ? charToValue(previous[index]) : 0;
    const nextValue =
      index < following.length ? charToValue(following[index]) : BASE;

    if (prevValue === nextValue) {
      result += valueToChar(prevValue);
      continue;
    }

    const midValue = Math.floor((prevValue + nextValue) / 2);

    if (midValue !== prevValue) {
      result += valueToChar(midValue);
      const candidate = result;

      if (previous < candidate && candidate < following) {
        return candidate;
      }
    }

    result += valueToChar(prevValue);
  }

  return result + DEFAULT_RANK;
}

export function rankBetween(
  previous: string | null,
  following: string | null,
): string {
  if (previous === null && following === null) {
    return DEFAULT_RANK;
  }

  if (previous === null) {
    return rankBefore(following as string);
  }

  if (following === null) {
    return rankAfter(previous);
  }

  return rankMid(previous, following);
}
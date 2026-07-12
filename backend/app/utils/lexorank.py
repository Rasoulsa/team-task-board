"""Minimal LexoRank-style ordering utility.

This generates string ranks between two existing ranks so that items can be
reordered without renumbering every sibling.

Ranks use lowercase base-36 characters: 0-9 then a-z.
"""

from __future__ import annotations

BASE_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"
BASE = len(BASE_DIGITS)

MIN_CHAR = BASE_DIGITS[0]
MAX_CHAR = BASE_DIGITS[-1]

DEFAULT_RANK = "n"


def _char_to_value(char: str) -> int:
    return BASE_DIGITS.index(char)


def _value_to_char(value: int) -> str:
    return BASE_DIGITS[value]


def rank_between(previous: str | None, following: str | None) -> str:
    """Return a rank strictly between previous and following.

    If both are None, return a middle default rank.
    If previous is None, generate a rank before following.
    If following is None, generate a rank after previous.
    """

    if previous is None and following is None:
        return DEFAULT_RANK

    if previous is None:
        assert following is not None
        return _rank_before(following)

    if following is None:
        return _rank_after(previous)

    return _rank_mid(previous, following)


def _rank_after(previous: str) -> str:
    """Generate a rank strictly greater than previous."""

    for index in range(len(previous)):
        char = previous[index]

        if char != MAX_CHAR:
            next_char = _value_to_char(_char_to_value(char) + 1)
            return previous[:index] + next_char

    # previous is all max chars, so append a middle char.
    return previous + DEFAULT_RANK


def _rank_before(following: str) -> str:
    """Generate a rank strictly less than following."""

    for index in range(len(following)):
        char = following[index]

        if char != MIN_CHAR:
            prev_char = _value_to_char(_char_to_value(char) - 1)
            candidate = following[:index] + prev_char

            if candidate < following and candidate != "":
                return candidate

    # following starts with min chars, so insert a middle char deeper.
    return following + DEFAULT_RANK


def _rank_mid(previous: str, following: str) -> str:
    """Generate a rank strictly between previous and following."""

    if previous >= following:
        raise ValueError("previous must be strictly less than following")

    max_length = max(len(previous), len(following))
    result = ""

    for index in range(max_length + 1):
        prev_value = _char_to_value(previous[index]) if index < len(previous) else 0
        next_value = _char_to_value(following[index]) if index < len(following) else BASE

        if prev_value == next_value:
            result += _value_to_char(prev_value)
            continue

        mid_value = (prev_value + next_value) // 2

        if mid_value != prev_value:
            result += _value_to_char(mid_value)
            candidate = result

            if previous < candidate < following:
                return candidate

        # No integer gap here, descend one level deeper.
        result += _value_to_char(prev_value)

    # If we exhausted the loop, append a middle char to break the tie.
    return result + DEFAULT_RANK

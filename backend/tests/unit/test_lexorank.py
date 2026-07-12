from __future__ import annotations

from app.utils.lexorank import DEFAULT_RANK, rank_between


def test_both_none_returns_default():
    assert rank_between(None, None) == DEFAULT_RANK


def test_after_previous_is_greater():
    previous = "n"
    result = rank_between(previous, None)
    assert result > previous


def test_before_following_is_smaller():
    following = "n"
    result = rank_between(None, following)
    assert result < following


def test_between_two_ranks_is_strictly_between():
    previous = "a"
    following = "c"
    result = rank_between(previous, following)
    assert previous < result < following


def test_between_adjacent_ranks_creates_deeper_rank():
    previous = "a"
    following = "b"
    result = rank_between(previous, following)
    assert previous < result < following


def test_sequential_inserts_keep_order():
    ranks: list[str] = []

    first = rank_between(None, None)
    ranks.append(first)

    second = rank_between(first, None)
    ranks.append(second)

    third = rank_between(first, second)
    ranks.insert(1, third)

    assert ranks == sorted(ranks)


def test_many_middle_inserts_stay_ordered():
    low = rank_between(None, None)
    high = rank_between(low, None)

    ordered = [low, high]

    for _ in range(50):
        mid = rank_between(ordered[0], ordered[1])
        assert ordered[0] < mid < ordered[1]
        ordered.insert(1, mid)

    assert ordered == sorted(ordered)


def test_all_max_previous_appends():
    previous = "z"
    result = rank_between(previous, None)
    assert result > previous


def test_invalid_order_raises():
    import pytest

    with pytest.raises(ValueError):
        rank_between("c", "a")

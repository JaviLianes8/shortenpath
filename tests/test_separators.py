"""Hand-written literal separator cases and long near matches."""

from __future__ import annotations

import random

import pytest

from shortenpath import shorten
from shortenpath._literal import literal_runs


@pytest.mark.parametrize(
    ("path", "sep", "home", "expected"),
    [
        ("abaHOMEabaUSERabaFILE", "aba", "abaHOMEabaUSER", "~abaFILE"),
        ("abaabaHOMEabaabaUSERabaFILEaba", "aba", "abaHOMEabaUSER", "~abaFILEaba"),
        ("ababaHOMEabaFILE", "aba", "ababaHOME", "~abaFILE"),
        ("aaaaaHOMEaaFILE", "aa", "aaaHOME", "~aaFILE"),
        (".*HOME.*USER.*FILE", ".*", ".*HOME.*USER", "~.*FILE"),
    ],
)
def test_custom_separator_runs_are_literal_and_nonoverlapping(
    path: str, sep: str, home: str, expected: str
) -> None:
    assert shorten(path, 100, sep=sep, home=home) == expected
    assert shorten(path, 100, sep=sep, home_tilde=False) == path


def test_long_near_matching_separator_keeps_the_filename_cut() -> None:
    size = 64000
    assert shorten("a" * size, 20, sep="a" * (size // 2) + "b", home_tilde=False) == (
        "a" * 9 + "..." + "a" * 8
    )


def test_literal_runs_match_a_naive_nonoverlapping_search() -> None:
    rng = random.Random(415)
    for _ in range(3000):
        text = "".join(rng.choices("aab:", k=rng.randrange(100)))
        sep = "".join(rng.choices("aab:", k=rng.randrange(1, 15)))
        expected: list[tuple[int, int]] = []
        cursor = 0
        while (begin := text.find(sep, cursor)) != -1:
            cursor = begin + len(sep)
            if expected and begin == expected[-1][1]:
                expected[-1] = expected[-1][0], cursor
            else:
                expected.append((begin, cursor))
        assert list(literal_runs(text, sep)) == expected, (text, sep)

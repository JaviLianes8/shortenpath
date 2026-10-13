"""Columns, not characters: wide characters count two, marks none, cuts keep marks attached."""

from __future__ import annotations

import os

import pytest

from shortenpath import display_width, shorten
from shortenpath._name import extension, squeeze
from shortenpath._width import char_width, clusters

CJK = "\u65e5\u672c\u8a9e"  # three Wide ideographs
E_ACUTE = "e\u0301"  # e followed by a combining acute accent
FULL_A = "\uff21"  # FULLWIDTH LATIN CAPITAL LETTER A, class F


@pytest.mark.parametrize(
    ("text", "width"),
    [
        ("", 0),
        ("abc", 3),
        (CJK, 6),
        (FULL_A, 2),
        (E_ACUTE * 3, 3),
        ("\u200b", 0),  # zero width space, Cf
        ("\u200d", 0),  # zero width joiner, Cf
        ("\u00ad", 1),  # soft hyphen, shown as a hyphen
        ("\u1100\u1161\u11a8", 2),  # Hangul jamo: leading consonant, vowel, final consonant
        ("\u20dd", 0),  # combining enclosing circle, Me
        ("\uff61", 1),  # halfwidth ideographic full stop, class H
        ("\u00e9", 1),  # precomposed e acute
        ("\x07", 1),  # a control character takes one column
    ],
)
def test_display_width(text: str, width: int) -> None:
    assert display_width(text) == width


def test_display_width_rejects_non_text() -> None:
    with pytest.raises(TypeError, match="text must be str"):
        display_width(b"abc")  # type: ignore[arg-type]


def test_char_width_is_zero_one_or_two() -> None:
    assert {char_width(chr(code)) for code in range(0x3000)} == {0, 1, 2}


def test_clusters_keep_marks_and_joined_characters_together() -> None:
    family = "\U0001f468\u200d\U0001f469"
    assert clusters(E_ACUTE + "x") == [(E_ACUTE, 1), ("x", 1)]
    assert clusters(family) == [(family, 4)]
    assert clusters("\u0301a") == [("\u0301", 0), ("a", 1)]


def test_wide_names_are_budgeted_in_columns() -> None:
    path = f"/{CJK}/{CJK}/{CJK}/{CJK}.txt"
    assert shorten(path, 21, flavor="posix") == f"/.../{CJK}.txt"
    result = shorten(path, 22, flavor="posix")
    assert result == f"/{CJK}/.../{CJK}.txt"
    assert display_width(result) == 22
    assert len(result) == 16


def test_combining_marks_do_not_use_the_budget() -> None:
    name = E_ACUTE * 6
    assert shorten(f"/a/{name}", 9, flavor="posix") == f"/a/{name}"


def test_a_cut_never_separates_a_mark_from_its_letter() -> None:
    result = squeeze(E_ACUTE * 10, 7, "...")
    assert result == E_ACUTE * 2 + "..." + E_ACUTE * 2
    assert not result.startswith("\u0301")


def test_a_wide_character_that_would_overflow_is_left_out() -> None:
    result = squeeze(CJK * 3, 8, "...")
    assert result == "\u65e5" + "..." + "\u8a9e"
    assert display_width(result) == 7


@pytest.mark.parametrize(
    "name",
    ["a.txt", ".bashrc", "..x", "a.", "...a", "a..b", "archive.tar.gz", "x", "", ".", "..", "a.b."],
)
def test_extension_agrees_with_os_path_splitext(name: str) -> None:
    assert extension(name) == os.path.splitext(name)[1]


@pytest.mark.parametrize(
    ("name", "budget", "expected"),
    [
        ("verylongfilename.py", 12, "veryl...e.py"),
        ("verylongfilename.py", 8, "v...e.py"),
        ("verylongfilename.py", 7, "ve...py"),
        ("verylongfilename.py", 4, "v..."),
        ("verylongfilename", 9, "ver...ame"),
        ("verylongfilename", 3, "ver"),
        ("report.final.version.pdf", 14, "report...n.pdf"),
        (".verylongdotfile", 9, ".ve...ile"),
    ],
)
def test_squeeze_rules(name: str, budget: int, expected: str) -> None:
    assert squeeze(name, budget, "...") == expected
    assert display_width(expected) <= budget


def test_a_long_extension_is_cut_like_any_other_text() -> None:
    assert squeeze("a.verylongextension", 9, "...") == "a.v...ion"

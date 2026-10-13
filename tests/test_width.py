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


@pytest.mark.parametrize(
    ("code", "width"), [(0x115F, 2), (0x1160, 0), (0x11A8, 0), (0x11FF, 0), (0x1200, 1)]
)
def test_hangul_medial_and_final_jamo_range_ends(code: int, width: int) -> None:
    assert char_width(chr(code)) == width


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


def test_columns_a_wide_end_cannot_use_go_to_the_start() -> None:
    result = squeeze(CJK * 3, 9, "...")
    assert result == CJK[:2] + "..." + CJK[2]
    assert display_width(result) == 9


@pytest.mark.parametrize(
    "name",
    [
        "a.txt",
        ".bashrc",
        "..x",
        "a.",
        "...a",
        "a..b",
        "archive.tar.gz",
        "x",
        "",
        ".",
        "..",
        "a.b.",
        "ab",
        "readme",
    ],
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


def test_a_name_that_fits_is_returned_whole() -> None:
    assert squeeze("abc", 3, "...") == "abc"
    assert squeeze(CJK, 6, "...") == CJK


def test_a_long_extension_is_cut_like_any_other_text() -> None:
    assert squeeze("a.verylongextension", 9, "...") == "a.v...ion"


def test_emoji_presentation_selector_makes_two_columns() -> None:
    heart = chr(0x2764) + chr(0xFE0F)
    assert display_width(heart) == 2
    assert display_width(chr(0x2764)) == 1
    assert clusters(heart + "a") == [(heart, 2), ("a", 1)]


def test_hangul_jamo_extended_b_medial_and_final_take_no_columns() -> None:
    assert char_width(chr(0xD7B0)) == 0
    assert char_width(chr(0xD7FB)) == 0
    assert char_width(chr(0xD7AF)) == 1


def test_a_wide_stem_keeps_its_last_character_before_the_extension() -> None:
    name = "".join(map(chr, [0x9577, 0x3044, 0x540D, 0x524D, 0x30D5, 0x30A1, 0x30A4, 0x30EB]))
    assert squeeze(name + ".txt", 12, "...") == name[:1] + "..." + name[-1] + ".txt"
    # Without room for both ends of the stem, the plain middle cut leaves no four dots.
    assert squeeze(name + ".txt", 9, "...") == name[:1] + "...txt"


def test_the_start_gets_its_first_character_when_it_fits() -> None:
    family = chr(0x1F468) + chr(0x200D) + chr(0x1F469)
    assert squeeze(family + ".txt", 7, "...") == family + "..."
    assert squeeze(family + ".txt", 6, "...") == "...txt"


def test_nothing_fits_gives_an_empty_cut() -> None:
    assert shorten("/a/" + CJK[0], 1, flavor="posix") == ""

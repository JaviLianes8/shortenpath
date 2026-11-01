"""Terminal display width of text, and cuts that never split a character from its marks."""

from __future__ import annotations

import unicodedata

_ZERO_WIDTH_CATEGORIES = frozenset({"Mn", "Me", "Cf"})
_SOFT_HYPHEN = "\u00ad"
_ZERO_WIDTH_JOINER = "\u200d"
_EMOJI_PRESENTATION = "\ufe0f"


def char_width(char: str) -> int:
    """Columns taken by one code point: 0, 1 or 2."""
    if char == _SOFT_HYPHEN:
        # A format character, but terminals and wcwidth() show it as a visible hyphen.
        return 1
    if unicodedata.category(char) in _ZERO_WIDTH_CATEGORIES:
        return 0
    if "\u1160" <= char <= "\u11ff" or "\ud7b0" <= char <= "\ud7ff":
        # Hangul medial vowels and final consonants (and their extension block) join the
        # syllable before them.
        return 0
    if unicodedata.east_asian_width(char) in ("W", "F"):
        return 2
    return 1


def display_width(text: str) -> int:
    """Return the number of terminal columns ``text`` takes.

    East Asian Wide and Fullwidth characters take two columns; combining marks, format
    characters and Hangul medial and final jamo take none; a character followed by the
    emoji presentation selector takes two; everything else takes one.

    This is a display convention, not terminal emulation. Controls take one column;
    joined emoji are counted as their parts. Widths use Python's Unicode database.
    Non-text input raises ``TypeError`` without quoting the input.

    >>> from shortenpath import display_width
    >>> display_width("a\u0301\u65e5")
    3
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    return sum(width for _, width in clusters(text))


def clusters(text: str) -> list[tuple[str, int]]:
    """Split ``text`` into cuttable units with their widths.

    A unit is a character plus every zero width character after it; a zero width joiner also
    pulls in the character it joins. A unit with the emoji presentation selector is drawn as
    an emoji, two columns wide.
    """
    units: list[tuple[str, int]] = []
    glue = False
    start = total = 0
    for index, char in enumerate(text):
        width = char_width(char)
        if index and (width == 0 or glue):
            if char == _EMOJI_PRESENTATION:
                total = max(total, 2)
            total += width
        else:
            if index:
                units.append((text[start:index], total))
            start, total = index, width
        glue = char == _ZERO_WIDTH_JOINER
    if text:
        units.append((text[start:], total))
    return units


def head(units: list[tuple[str, int]], budget: int) -> tuple[str, int]:
    """Longest run of ``units`` from the start that fits ``budget`` columns."""
    taken: list[str] = []
    used = 0
    for text, width in units:
        if used + width > budget:
            break
        taken.append(text)
        used += width
    return "".join(taken), used


def tail(units: list[tuple[str, int]], budget: int) -> tuple[str, int]:
    """Longest run of ``units`` from the end that fits ``budget`` columns."""
    taken: list[str] = []
    used = 0
    for text, width in reversed(units):
        if used + width > budget:
            break
        taken.append(text)
        used += width
    return "".join(reversed(taken)), used

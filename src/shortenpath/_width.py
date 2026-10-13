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
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, not {type(text).__name__}")
    return sum(width for _, width in clusters(text))


def clusters(text: str) -> list[tuple[str, int]]:
    """Split ``text`` into cuttable units with their widths.

    A unit is a character plus every zero width character after it; a zero width joiner also
    pulls in the character it joins. A unit with the emoji presentation selector is drawn as
    an emoji, two columns wide.
    """
    units: list[tuple[str, int]] = []
    glue = False
    for char in text:
        width = char_width(char)
        if units and (width == 0 or glue):
            last, last_width = units[-1]
            if char == _EMOJI_PRESENTATION:
                last_width = max(last_width, 2)
            units[-1] = (last + char, last_width + width)
        else:
            units.append((char, width))
        glue = char == _ZERO_WIDTH_JOINER
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

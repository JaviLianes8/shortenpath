"""Width-budgeted abbreviation of filesystem paths for display."""

from __future__ import annotations

import os
from bisect import bisect_right
from itertools import accumulate

from ._name import squeeze
from ._parts import Flavor, Parts, fold_home, resolve, split
from ._width import clusters, display_width, head

_PLACEHOLDER = "..."


def shorten(
    path: str | os.PathLike[str],
    width: int,
    *,
    flavor: Flavor = "native",
    home_tilde: bool = True,
    home: str | os.PathLike[str] | None = None,
    sep: str | None = None,
    placeholder: str = _PLACEHOLDER,
) -> str:
    """Return ``path`` shortened to fit ``width`` terminal columns.

    ``flavor`` picks the path rules (``"posix"``, ``"windows"`` or ``"native"`` for the
    running system); ``sep`` replaces them with a single custom separator. The home directory
    collapses to ``~`` when ``home_tilde`` is set. A path still too wide prefers its anchor
    and last name, keeping whole segments around ``placeholder`` when they fit. Smaller
    budgets can drop the anchor or cut the last name; its extension is kept only if it and
    the required stem characters fit. An anchor-only path can itself be cut.
    Display only: the filesystem is never read.

    ``width`` is a positive integer (not bool). String and integer subclasses use their
    built-in values without invoking overrides. Wrong types raise ``TypeError``;
    nonpositive width, empty separator/placeholder or unknown flavor raise ``ValueError``.
    ``home`` is ignored when ``home_tilde=False``. A context-sensitive emoji selector
    may require a final prefix cut at a cluster boundary to enforce the budget.

    >>> from shortenpath import shorten
    >>> shorten("/a/b/c/d/e/file", 11, flavor="posix", home_tilde=False)
    '/a/.../file'
    >>> shorten("/home/u/code.py", 40, flavor="posix", home="/home/u")
    '~/code.py'
    >>> shorten("filename.extension", 9, flavor="posix", home_tilde=False)
    'fil...ion'
    """
    text = _text(path, "path")
    if isinstance(width, bool) or not isinstance(width, int):
        raise TypeError("width must be int")
    width = int.__int__(width)
    if width < 1:
        raise ValueError("width must be at least 1")
    if not isinstance(home_tilde, bool):
        raise TypeError("home_tilde must be bool")
    if sep is not None:
        if not isinstance(sep, str):
            raise TypeError("sep must be str or None")
        sep = str.__str__(sep)
    if sep == "":
        raise ValueError("sep must be a non-empty string")
    if not isinstance(placeholder, str):
        raise TypeError("placeholder must be str")
    placeholder = str.__str__(placeholder)
    if not placeholder:
        raise ValueError("placeholder must be a non-empty string")
    rules = resolve(flavor)
    parts = split(text, rules, sep)
    if home_tilde:
        base = _home(home, rules, sep)
        if base:
            parts = fold_home(parts, split(base, rules, sep), rules, sep)
    text = parts.render()
    if display_width(text) <= width:
        return text
    result = _fit(parts, width, placeholder)
    # Selectors can widen the preceding character when separately measured pieces join.
    return result if display_width(result) <= width else head(clusters(result), width)[0]


def _text(value: object, label: str) -> str:
    if isinstance(value, os.PathLike):
        try:
            value = os.fspath(value)
        except TypeError:
            raise TypeError(f"{label} must be str or os.PathLike[str]") from None
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str or os.PathLike[str]")
    return str.__str__(value)


def _home(home: object, rules: str, sep: str | None) -> str:
    if home is not None:
        return _text(home, "home")
    if sep is not None or rules != resolve("native"):
        # The running user's home only means something for paths of the running system.
        return ""
    # Without a known home this gives back "~", which folds nothing that would change.
    return os.path.expanduser("~")


def _fit(parts: Parts, width: int, placeholder: str) -> str:
    names, seps = parts.names, parts.seps
    count = len(names)
    if count == 0:
        return squeeze(parts.render(), width, placeholder)
    if count > 1:
        best = _search(parts, width - display_width(parts.anchor) - display_width(placeholder))
        if best is not None:
            keep_head, keep_tail = best
            start = "".join(name + seps[i] for i, name in enumerate(names[:keep_head]))
            end = "".join(seps[i - 1] + names[i] for i in range(count - keep_tail, count))
            return parts.anchor + start + placeholder + end + parts.trailing
    # The whole last name is worth more than the anchor: after the placeholder and the
    # separator as written, then a single separator, then alone.
    before = seps[-1] if count > 1 else parts.root_sep
    for run in dict.fromkeys((before, before[-1:])):
        bare = placeholder + run + names[-1] + parts.trailing
        if run and display_width(bare) <= width:
            return bare
    for whole in (names[-1] + parts.trailing, names[-1]):
        if display_width(whole) <= width:
            return whole
    if count == 1:
        room = width - display_width(parts.anchor) - display_width(parts.trailing)
        if (parts.anchor or parts.trailing) and room > display_width(placeholder) + 1:
            return parts.anchor + squeeze(names[0], room, placeholder) + parts.trailing
    return squeeze(names[-1], width, placeholder)


def _search(parts: Parts, room: int) -> tuple[int, int] | None:
    """Most segments kept around the placeholder, then most at the head; None if none fit."""
    names, seps = parts.names, parts.seps
    count = len(names)
    # heads[h]: columns of the first h names, each with the separator after it.
    heads = [
        0,
        *accumulate(display_width(names[i]) + display_width(seps[i]) for i in range(count - 1)),
    ]
    # tails[t]: columns of the last t names, each with the separator before it.
    trail = display_width(parts.trailing)
    tails = [
        0,
        *accumulate(
            display_width(seps[count - 2 - t])
            + display_width(names[count - 1 - t])
            + (trail if t == 0 else 0)
            for t in range(count - 1)
        ),
    ]
    best: tuple[int, int] | None = None
    for keep_head in range(count - 1):
        keep_tail = min(bisect_right(tails, room - heads[keep_head]) - 1, count - 1 - keep_head)
        if keep_tail >= 1 and (best is None or keep_head + keep_tail >= sum(best)):
            best = (keep_head, keep_tail)
    return best

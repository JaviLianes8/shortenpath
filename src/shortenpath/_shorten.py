"""Width-budgeted abbreviation of filesystem paths for display."""

from __future__ import annotations

import os

_DEFAULT_PLACEHOLDER = "..."


def shorten(
    path: str,
    max_len: int,
    *,
    home_tilde: bool = True,
    home: str | None = None,
    sep: str = os.sep,
    placeholder: str = _DEFAULT_PLACEHOLDER,
) -> str:
    """Return ``path`` shortened to fit ``max_len`` display columns.

    The home directory collapses to ``~`` when ``home_tilde`` is set, and a path
    still too long has its middle replaced by ``placeholder`` while the leading and
    trailing segments stay readable. This is display-only and never touches disk.
    """
    if max_len <= 0:
        raise ValueError("max_len must be positive")
    if not sep:
        raise ValueError("sep must be a non-empty string")
    text = _apply_tilde(path, sep, home) if home_tilde else path
    if len(text) <= max_len:
        return text
    return _elide(text, max_len, sep, placeholder)


def _apply_tilde(path: str, sep: str, home: str | None) -> str:
    base = home if home is not None else os.path.expanduser("~")
    if not base:
        return path
    base = base.rstrip(sep)
    if not base:
        return path
    if path == base:
        return "~"
    prefix = base + sep
    if path.startswith(prefix):
        return "~" + sep + path[len(prefix) :]
    return path


def _elide(text: str, max_len: int, sep: str, placeholder: str) -> str:
    if len(text) > len(sep) and text.endswith(sep):
        stripped = text.rstrip(sep)
        if stripped:
            inner = _elide(stripped, max(max_len - len(sep), 1), sep, placeholder)
            return inner + sep
    anchor, segments = _split_anchor(text, sep)
    if len(segments) <= 1:
        return anchor + _truncate(
            segments[0] if segments else "", max_len - len(anchor), placeholder
        )
    last = segments[-1]
    best: str | None = None
    for keep in range(1, len(segments) - 1):
        head = sep.join(segments[:keep])
        candidate = f"{anchor}{head}{sep}{placeholder}{sep}{last}"
        if len(candidate) <= max_len:
            best = candidate
    if best is not None:
        return best
    dropped = f"{anchor}{placeholder}{sep}{last}"
    if len(dropped) <= max_len:
        return dropped
    return _truncate(last, max_len, placeholder)


def _split_anchor(text: str, sep: str) -> tuple[str, list[str]]:
    if text.startswith(sep):
        return sep, text[len(sep) :].split(sep)
    return "", text.split(sep)


def _truncate(name: str, budget: int, placeholder: str) -> str:
    if budget <= 0:
        return ""
    if len(name) <= budget:
        return name
    if budget <= len(placeholder):
        return name[:budget]
    return placeholder + name[-(budget - len(placeholder)) :]

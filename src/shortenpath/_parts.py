"""Split a path into its anchor and its named segments, and fold the home directory."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal

Flavor = Literal["native", "posix", "windows"]

_BACK = "\\"
_VERBATIM = _BACK * 2 + "?" + _BACK
_UNC_DEVICES = (_VERBATIM + "UNC" + _BACK, _BACK * 2 + ".\\UNC" + _BACK)
_POSIX_RUN = re.compile(r"/+")
_WINDOWS_RUN = re.compile(r"[\\/]+")
_BACK_RUN = re.compile(r"\\+")


@dataclass(frozen=True)
class Parts:
    """A path as anchor, names, the separator runs between names, and a trailing run.

    ``root_sep`` is the separator run that ends the anchor, empty when it ends in a name.
    """

    anchor: str
    names: tuple[str, ...]
    seps: tuple[str, ...]
    trailing: str
    root_sep: str = ""

    def render(self) -> str:
        pieces = [self.anchor]
        for index, name in enumerate(self.names):
            if index:
                pieces.append(self.seps[index - 1])
            pieces.append(name)
        pieces.append(self.trailing)
        return "".join(pieces)


def resolve(flavor: str) -> str:
    """Return ``"posix"`` or ``"windows"`` for a flavor name."""
    if flavor == "native":
        return "windows" if os.name == "nt" else "posix"
    if flavor in ("posix", "windows"):
        return flavor
    raise ValueError(f"flavor must be 'native', 'posix' or 'windows', not {flavor!r}")


def windows_splitroot(path: str) -> tuple[str, str, str]:
    """Split a Windows path into drive, root and tail, like ``ntpath.splitroot``.

    A path that starts exactly with ``\\\\?\\`` skips normalization in Windows, so only the
    backslash separates its parts and a forward slash is part of a name.
    """
    norm = path if path.startswith(_VERBATIM) else path.replace("/", _BACK)
    if norm[:1] == _BACK:
        if norm[1:2] != _BACK:
            return "", path[:1], path[1:]
        # UNC (\\server\share) or device (\\.\C:, \\?\UNC\server\share): two parts after it.
        # Microsoft documents \\.\UNC\ as a UNC device too; ntpath.splitroot does not.
        start = 8 if norm[:8].upper() in _UNC_DEVICES else 2
        first = norm.find(_BACK, start)
        second = norm.find(_BACK, first + 1) if first != -1 else -1
        if second == -1:
            return path, "", ""
        return path[:second], path[second : second + 1], path[second + 1 :]
    if norm[1:2] == ":":
        if norm[2:3] == _BACK:
            return path[:2], path[2:3], path[3:]
        return path[:2], "", path[2:]
    return "", "", path


def split(path: str, flavor: str, sep: str | None) -> Parts:
    """Split ``path`` into :class:`Parts` under ``flavor`` or a custom ``sep``."""
    drive = root = ""
    if sep is not None:
        run = re.compile(f"(?:{re.escape(sep)})+")
    elif flavor == "windows":
        drive, root, _ = windows_splitroot(path)
        run = _BACK_RUN if path.startswith(_VERBATIM) else _WINDOWS_RUN
    else:
        run = _POSIX_RUN
    rest = path[len(drive + root) :]
    lead = run.match(rest)
    root_sep = root + (lead.group() if lead else "")
    rest = rest[len(root_sep) - len(root) :]
    pieces = run.split(rest)
    gaps = run.findall(rest)
    if pieces[-1] == "" and gaps:
        trailing = gaps.pop()
        pieces.pop()
    else:
        trailing = ""
    names = tuple(pieces) if pieces != [""] else ()
    return Parts(drive + root_sep, names, tuple(gaps), trailing, root_sep)


def _anchor_key(anchor: str, flavor: str, sep: str | None) -> str:
    if sep is not None:
        return anchor and sep
    if flavor == "posix":
        # Two leading slashes are implementation defined; three or more mean one.
        return "//" if anchor == "//" else anchor[:1]
    if not anchor.startswith(_VERBATIM):
        anchor = anchor.replace("/", _BACK)
    # The anchor took in the separator run after the root; its length does not matter.
    stripped = anchor.rstrip(_BACK)
    return (stripped + _BACK if stripped != anchor else anchor).lower()


def fold_home(parts: Parts, home: Parts, flavor: str, sep: str | None) -> Parts:
    """Replace a leading ``home`` in ``parts`` with ``~``; ``parts`` unchanged otherwise."""
    count = len(home.names)
    if count == 0:
        return parts
    if _anchor_key(parts.anchor, flavor, sep) != _anchor_key(home.anchor, flavor, sep):
        return parts
    mine, theirs = parts.names[:count], home.names
    if sep is None and flavor == "windows":
        # Windows names compare without regard to case.
        mine = tuple(name.lower() for name in mine)
        theirs = tuple(name.lower() for name in theirs)
    if mine != theirs:
        return parts
    if len(parts.names) == count:
        return Parts("~", (), (), parts.trailing)
    root_sep = parts.seps[count - 1]
    return Parts("~" + root_sep, parts.names[count:], parts.seps[count:], parts.trailing, root_sep)

"""Cut a single name to a column budget, keeping its start and its extension."""

from __future__ import annotations

from ._width import clusters, display_width, head, tail


def extension(name: str) -> str:
    """The extension of ``name`` as ``os.path.splitext`` sees it, leading dots ignored."""
    dot = name.rfind(".")
    # No dot, or only dots before the last one (".bashrc", "..x"): no extension.
    if not name[: max(dot, 0)].strip("."):
        return ""
    return name[dot:]


def squeeze(name: str, budget: int, placeholder: str) -> str:
    """Return ``name`` cut in the middle to fit ``budget`` columns.

    The extension stays whole with the last character of the stem before it when that
    leaves room for the first one; otherwise the columns are shared between start and end,
    the start taking the odd one, and the start always gets its first character when it
    fits (the end takes every column when it does not). Without room for the placeholder
    the start of the name is kept alone, which is empty when not even its first character
    fits.
    """
    units = clusters(name)
    if sum(width for _, width in units) <= budget:
        return name
    room = budget - display_width(placeholder)
    if room <= 0:
        return head(units, budget)[0]
    end_budget = room // 2
    ext = extension(name)
    stem = clusters(name[: len(name) - len(ext)])
    if ext and len(stem) > 1:
        keep = display_width(ext) + stem[-1][1]
        if room >= keep + stem[0][1]:
            end_budget = max(keep, end_budget)
    # The start gets at least its first character; if even that cannot fit, the end takes all.
    first = units[0][1]
    end_budget = min(end_budget, room - first) if first <= room else room
    end, used = tail(units, end_budget)
    start, _ = head(units, room - used)
    return start + placeholder + end

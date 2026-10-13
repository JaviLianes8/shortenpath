"""Fuzzed paths against the standard library and against the stated rules."""

from __future__ import annotations

import ntpath
import posixpath
import random
import sys
from itertools import product

import pytest

from shortenpath import Flavor, display_width, shorten
from shortenpath._parts import split, windows_splitroot
from shortenpath._shorten import _search

B = "\\"
WIN_ALPHABET = [B, "/", "a", "?", ".", ":", "C", "UNC", "unc", " ", "\u65e5"]
POSIX_ALPHABET = ["/", "a", "bc", ".", B, "\u65e5", "e\u0301", "x.py"]


def _paths(alphabet: list[str], seed: int, count: int, longest: int = 12) -> list[str]:
    rng = random.Random(seed)
    return ["".join(rng.choices(alphabet, k=rng.randint(0, longest))) for _ in range(count)]


def _documented_difference(path: str) -> bool:
    # Exact \\?\ keeps "/" inside names, and \\.\UNC\ is a UNC device; see _parts.
    norm = path.replace("/", B)
    verbatim = path.startswith(B * 2 + "?" + B) and "/" in path
    return verbatim or norm[:8].upper() == B * 2 + "." + B + "UNC" + B


@pytest.mark.skipif(sys.version_info < (3, 12), reason="ntpath.splitroot is new in 3.12")
def test_windows_anchor_agrees_with_ntpath_splitroot() -> None:
    checked = 0
    for path in _paths(WIN_ALPHABET, 1, 40000, 10):
        if _documented_difference(path):
            continue
        assert windows_splitroot(path) == ntpath.splitroot(path), ascii(path)  # type: ignore[attr-defined,unused-ignore]
        checked += 1
    assert checked > 30000


def test_windows_anchor_agrees_with_ntpath_splitdrive() -> None:
    for path in _paths(WIN_ALPHABET, 2, 20000, 10):
        if not _documented_difference(path):
            assert windows_splitroot(path)[0] == ntpath.splitdrive(path)[0], ascii(path)


@pytest.mark.skipif(sys.version_info < (3, 12), reason="posixpath.splitroot is new in 3.12")
def test_posix_anchor_is_the_stdlib_root_plus_the_slashes_after_it() -> None:
    for path in _paths(POSIX_ALPHABET, 3, 20000):
        _, root, rest = posixpath.splitroot(path)  # type: ignore[attr-defined,unused-ignore]
        extra = rest[: len(rest) - len(rest.lstrip("/"))]
        assert split(path, "posix", None).anchor == root + extra


@pytest.mark.parametrize(
    ("flavor", "alphabet"), [("windows", WIN_ALPHABET), ("posix", POSIX_ALPHABET)]
)
def test_splitting_never_changes_the_text(flavor: Flavor, alphabet: list[str]) -> None:
    for path in _paths(alphabet, 4, 20000):
        assert split(path, flavor, None).render() == path
        assert split(path, flavor, "a").render() == path


@pytest.mark.parametrize(
    ("flavor", "alphabet"), [("windows", WIN_ALPHABET), ("posix", POSIX_ALPHABET)]
)
def test_properties_over_fuzzed_paths(flavor: Flavor, alphabet: list[str]) -> None:
    rng = random.Random(5)
    for path in _paths(alphabet, 6, 6000, 16):
        width = rng.randint(1, 30)
        out = shorten(path, width, flavor=flavor, home_tilde=False, placeholder="<>")
        assert display_width(out) <= width, (path, width, out)
        if display_width(path) <= width:
            assert out == path
            continue
        assert shorten(out, width, flavor=flavor, home_tilde=False) == out
        parts = split(path, flavor, None)
        if parts.names and display_width(parts.names[-1]) <= width:
            # A last name that fits alone is never cut.
            assert out.removesuffix(parts.trailing).endswith(parts.names[-1]), (path, width, out)
        if len(parts.names) < 2:
            continue
        last = parts.seps[-1] + parts.names[-1] + parts.trailing
        if display_width(parts.anchor + "<>" + last) <= width:
            # Anchor and last name stay whole; what is kept is a prefix and a suffix of the path.
            head, _, tail = out.partition("<>")
            assert head.startswith(parts.anchor) and tail.endswith(last), (path, width, out)
            assert path.startswith(head) and path.endswith(tail), (path, out)
        elif display_width("<>" + last) <= width:
            assert out == "<>" + last


def _brute(widths: list[tuple[int, int]], anchor: int, room: int) -> tuple[int, int] | None:
    count = len(widths)
    best: tuple[int, int] | None = None
    for keep_head, keep_tail in product(range(count), range(1, count)):
        if keep_head + keep_tail > count - 1:
            continue
        cost = anchor + sum(n + s for n, s in widths[:keep_head])
        cost += sum(widths[i][0] + widths[i - 1][1] for i in range(count - keep_tail, count))
        if cost <= room and (
            best is None or (keep_head + keep_tail, keep_head) > (sum(best), best[0])
        ):
            best = (keep_head, keep_tail)
    return best


def test_search_matches_a_brute_force_reading_of_the_rule() -> None:
    rng = random.Random(7)
    for _ in range(3000):
        names = ["x" * rng.randint(1, 6) for _ in range(rng.randint(2, 7))]
        seps = ["/" * rng.randint(1, 2) for _ in names[1:]]
        path = "/" + "".join(n + s for n, s in zip(names, [*seps, ""], strict=True))
        parts = split(path, "posix", None)
        room = rng.randint(0, 30)
        widths = [(len(n), len(s)) for n, s in zip(names, [*seps, ""], strict=True)]
        assert _search(parts, room) == _brute(widths, 0, room), (path, room)

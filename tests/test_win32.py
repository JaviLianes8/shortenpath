"""The Win32 PathCompactPathExW function as a reference, on Windows only.

Its documentation: https://learn.microsoft.com/en-us/windows/win32/api/shlwapi/nf-shlwapi-pathcompactpathexw
It counts characters, so the paths here are ASCII and characters equal columns.
"""

from __future__ import annotations

import random
import sys

import pytest

from shortenpath import shorten
from shortenpath._parts import split

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="needs shlwapi.dll")

B = "\\"


def compact(path: str, width: int) -> str:
    import ctypes

    buffer = ctypes.create_unicode_buffer(width + 1)
    # cchMax counts the terminating null, so width + 1 leaves width characters.
    assert ctypes.windll.shlwapi.PathCompactPathExW(buffer, path, width + 1, 0)  # type: ignore[attr-defined,unused-ignore]
    return buffer.value


def _paths() -> list[str]:
    rng = random.Random(11)
    prefixes = ["C:\\", "\\\\server\\share\\", "\\\\?\\C:\\", "\\", "", "C:/", "D:"]
    paths = []
    for _ in range(1500):
        names = ["".join(rng.choices("abcdefgh", k=rng.randint(1, 8))) for _ in range(5)]
        names = names[: rng.randint(1, 5)]
        names[-1] += rng.choice(["", ".txt", ".py"])
        paths.append(rng.choice(prefixes) + rng.choice([B, "/"]).join(names))
    return paths


def test_both_keep_a_path_that_fits() -> None:
    for path in _paths()[:300]:
        for width in (len(path) + 1, len(path) + 3):
            assert compact(path, width) == path == shorten(path, width, flavor="windows")
        assert shorten(path, len(path), flavor="windows") == path


def test_the_reference_compacts_a_path_exactly_as_long_as_the_budget() -> None:
    # Measured on Windows 11: one character of the budget is never used for a whole path.
    assert compact("abc/defgh", 9) == ".../defgh"
    assert shorten("abc/defgh", 9, flavor="windows") == "abc/defgh"


def test_the_file_name_is_whole_whenever_the_reference_keeps_it() -> None:
    rng = random.Random(12)
    seen = 0
    for path in _paths():
        width = rng.randint(1, len(path))
        name = split(path, "windows", None).names[-1:]
        if not name or len(path) <= width:
            continue
        if compact(path, width).endswith(name[0]):
            seen += 1
            assert shorten(path, width, flavor="windows").endswith(name[0]), (path, width)
    assert seen > 300


def test_the_anchor_is_kept_whole_or_dropped_whole() -> None:
    rng = random.Random(13)
    for path in _paths():
        width = rng.randint(1, len(path))
        anchor = split(path, "windows", None).anchor
        out = shorten(path, width, flavor="windows", home_tilde=False)
        # A cut anchor would still start with its first two characters.
        assert out.startswith(anchor) or not out.startswith(anchor[:2]), (path, width, out)


@pytest.mark.parametrize(
    ("path", "width", "reference", "ours"),
    [
        # The reference cuts inside the server name; the share is kept whole or dropped.
        ("\\\\server\\share\\dir\\sub\\file.txt", 18, "\\\\serv...\\file.txt", "...\\file.txt"),
        # The reference cuts inside a directory name; whole segments are kept here.
        ("C:\\path1\\path2\\sample.txt", 18, "C:\\p...\\sample.txt", "C:\\...\\sample.txt"),
        # The reference drops the extension when the name is cut; it is kept here.
        ("C:\\a\\b\\verylongfilename.py", 14, "...\\verylon...", "verylo...me.py"),
        # Both keep forward slashes as written.
        ("C:/a/b/c/d/e/file.txt", 18, "C:/a/b.../file.txt", "C:/a/.../file.txt"),
    ],
)
def test_documented_differences(path: str, width: int, reference: str, ours: str) -> None:
    assert compact(path, width) == reference
    assert shorten(path, width, flavor="windows") == ours

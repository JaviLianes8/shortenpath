from __future__ import annotations

import os
from pathlib import PurePosixPath

import pytest

from shortenpath import shorten


def px(path: str, width: int, **options: object) -> str:
    options.setdefault("home_tilde", False)
    return shorten(path, width, flavor="posix", **options)  # type: ignore[arg-type]


def test_short_path_is_returned_unchanged() -> None:
    assert px("/a/b/file", 32) == "/a/b/file"


def test_budget_boundary_keeps_path_at_exact_length() -> None:
    assert px("/a/b/file", 9) == "/a/b/file"
    assert px("/a/b/file", 8) == ".../file"


def test_middle_elision_keeps_root_and_last_name() -> None:
    assert px("/a/b/c/d/e/file", 11) == "/a/.../file"


def test_most_segments_kept_then_most_at_the_head() -> None:
    # Width 13 holds three names: two at the head beat two at the tail. Width 15 holds four.
    assert px("/a/b/c/d/e/file", 13) == "/a/b/.../file"
    assert px("/a/b/c/d/e/f/file", 15) == "/a/b/c/.../file"
    assert px("/aa/b/c/d/e/file", 13) == "/.../d/e/file"
    assert px("/aa/b/c/d/e/file", 14) == "/aa/b/.../file"


def test_a_longer_head_name_gives_way_to_more_tail_names() -> None:
    assert px("/verylongname/b/c/d/e/file", 16) == "/.../c/d/e/file"


def test_anchor_dropped_before_the_last_name() -> None:
    assert px("/aaaa/bbbb/file.txt", 13) == "/.../file.txt"
    assert px("/aaaa/bbbb/file.txt", 12) == ".../file.txt"


def test_relative_path_elides_without_an_anchor() -> None:
    assert px("a/b/c/d/file", 10) == "a/.../file"
    assert px("a/b/c/d/file", 8) == ".../file"


def test_last_name_is_cut_keeping_start_and_extension() -> None:
    assert px("/a/b/verylongfilename.py", 8) == "v...e.py"
    assert px("/a/b/verylongfilename.py", 12) == "veryl...e.py"


def test_single_name_keeps_its_anchor_while_there_is_room() -> None:
    assert px("/verylongfilename.py", 12) == "/very...e.py"
    assert px("/verylongfilename.py", 5) == "v...y"


def test_a_name_exactly_as_wide_as_the_budget_is_whole() -> None:
    assert px("/a/b/longname", 8) == "longname"


def test_a_relative_single_name_keeps_its_trailing_separator() -> None:
    assert px("verylongname/", 10) == "ver...ame/"


def test_the_last_resort_cut_drops_the_trailing_separator() -> None:
    assert px("/a/verylongname/", 6) == "ve...e"


def test_a_drive_relative_name_keeps_its_drive() -> None:
    out = shorten("C:verylongname", 13, flavor="windows", placeholder="\u2026")
    assert out == "C:veryl" + chr(0x2026) + "gname"


def test_width_below_the_placeholder_keeps_the_start_of_the_name() -> None:
    assert px("/a/b/longname", 2) == "lo"
    assert px("/a/b/longname", 3) == "lon"


def test_trailing_separator_is_preserved() -> None:
    assert px("/a/b/c/d/e/", 9) == "/a/.../e/"
    assert px("/verylongname/", 10) == "/ver...me/"


def test_runs_of_separators_are_kept_as_written() -> None:
    assert px("/a//b/c//d///file", 40) == "/a//b/c//d///file"
    assert px("/a//b/c//d///file", 13) == "/...///file"
    assert px("/a//b/c//d///file", 14) == "/a//...///file"
    assert px("/a//b/c//d///file", 16) == "/a//b/...///file"


def test_only_an_anchor_that_does_not_fit_is_cut_in_the_middle() -> None:
    assert shorten("//////////", 5, flavor="posix") == "/.../"


def test_custom_placeholder_and_its_width() -> None:
    assert px("/a/b/c/d/e/file", 9, placeholder="\u2026") == "/a/\u2026/file"
    assert px("/a/b/c/d/e/file", 10, placeholder="<>") == "/a/<>/file"


def test_custom_separator_splits_on_that_text_only() -> None:
    path = "C:\\a\\b\\c\\d\\report.txt"
    assert shorten(path, 18, home_tilde=False, sep="\\") == "...\\c\\d\\report.txt"
    assert shorten("a::b::c::d::e", 9, sep="::") == "a::...::e"
    assert shorten("a/b::c", 3, sep="::") == "c"


def test_path_like_objects_are_accepted() -> None:
    assert px(PurePosixPath("/a/b/c/d/e/file"), 11) == "/a/.../file"  # type: ignore[arg-type]


def test_native_flavor_follows_the_running_system() -> None:
    sep = "\\" if os.name == "nt" else "/"
    path = sep.join(["", "a", "b", "c", "d", "e", "file"])
    assert shorten(path, 11, home_tilde=False) == sep.join(["", "a", "...", "file"])


@pytest.mark.parametrize("width", [0, -1])
def test_width_below_one_is_rejected(width: int) -> None:
    with pytest.raises(ValueError, match="width must be at least 1"):
        px("/a/b", width)


@pytest.mark.parametrize("width", [1.5, "4", True, None])
def test_width_must_be_an_int(width: object) -> None:
    with pytest.raises(TypeError, match="width must be int"):
        px("/a/b", width)  # type: ignore[arg-type]


@pytest.mark.parametrize("path", [b"/a/b", 3, None])
def test_path_must_be_text(path: object) -> None:
    with pytest.raises(TypeError, match="path must be str or os"):
        px(path, 4)  # type: ignore[arg-type]


def test_bytes_path_like_is_rejected() -> None:
    class Raw:
        def __fspath__(self) -> bytes:
            return b"/a"

    with pytest.raises(TypeError, match="path must be str"):
        px(Raw(), 4)  # type: ignore[arg-type]


def test_home_must_be_text() -> None:
    with pytest.raises(TypeError, match="home must be str"):
        shorten("/a/b", 4, flavor="posix", home=b"/a")  # type: ignore[arg-type]


@pytest.mark.parametrize("sep", ["", 5])
def test_empty_or_non_text_separator_is_rejected(sep: object) -> None:
    with pytest.raises(ValueError, match="sep must be a non-empty string"):
        shorten("/a/b", 4, sep=sep)  # type: ignore[arg-type]


@pytest.mark.parametrize("placeholder", ["", None])
def test_empty_placeholder_is_rejected(placeholder: object) -> None:
    with pytest.raises(ValueError, match="placeholder must be a non-empty string"):
        px("/a/b", 4, placeholder=placeholder)


def test_unknown_flavor_is_rejected() -> None:
    with pytest.raises(ValueError, match="flavor must be"):
        shorten("/a/b", 4, flavor="mac")  # type: ignore[arg-type]

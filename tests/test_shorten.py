from __future__ import annotations

import pytest

from shortenpath import shorten


def test_short_path_is_returned_unchanged() -> None:
    assert shorten("/a/b/file", 32, home_tilde=False, sep="/") == "/a/b/file"


def test_home_collapses_to_tilde() -> None:
    result = shorten("/home/javi/code/app.py", 40, home="/home/javi", sep="/")
    assert result == "~/code/app.py"


def test_home_exactly_equal_becomes_tilde() -> None:
    assert shorten("/home/javi", 40, home="/home/javi", sep="/") == "~"


def test_middle_elision_keeps_first_and_last_segment() -> None:
    result = shorten("/a/b/c/d/e/file", 11, home_tilde=False, sep="/")
    assert result == "/a/.../file"


def test_middle_elision_grows_the_head_when_budget_allows() -> None:
    result = shorten("/home/javi/proj/sub/deep/file.py", 20, home="/home/javi", sep="/")
    assert result == "~/proj/.../file.py"
    assert len(result) <= 20


def test_very_small_budget_truncates_the_basename() -> None:
    result = shorten("/a/b/verylongfilename.py", 8, home_tilde=False, sep="/")
    assert len(result) <= 8
    assert result == "...me.py"


def test_basename_longer_than_budget_without_placeholder_room() -> None:
    result = shorten("/a/b/longname", 2, home_tilde=False, sep="/")
    assert result == "lo"


def test_custom_separator() -> None:
    result = shorten("C:\\a\\b\\c\\d\\report.txt", 18, home_tilde=False, sep="\\")
    assert result == "C:\\...\\report.txt"
    assert len(result) <= 18


def test_trailing_separator_is_preserved() -> None:
    result = shorten("/a/b/c/d/e/", 9, home_tilde=False, sep="/")
    assert result.endswith("/")
    assert len(result) <= 9
    assert result == "/a/.../e/"


def test_budget_boundary_keeps_path_at_exact_length() -> None:
    path = "/a/b/file"
    assert shorten(path, len(path), home_tilde=False, sep="/") == path


def test_non_positive_budget_is_rejected() -> None:
    with pytest.raises(ValueError):
        shorten("/a/b", 0, sep="/")


def test_empty_separator_is_rejected() -> None:
    with pytest.raises(ValueError):
        shorten("/a/b", 4, sep="")

"""Hand-written boundary cases for widths, home folding and path providers."""

from __future__ import annotations

import pytest

from shortenpath import display_width, shorten


@pytest.mark.parametrize(
    ("parts", "width"),
    [
        (["\U0001f441\ufe0f", "\U0001f5e8\ufe0f"], 4),
        (["\U0001f468", "\u2764\ufe0f", "\U0001f468"], 6),
        (["a\ufe0f", "b\ufe0f", "c\ufe0f"], 6),
        (["a", "b\ufe0f"], 3),
        (["a\ufe0f\ufe0f", "b\ufe0f\ufe0f"], 4),
    ],
)
def test_joined_components_each_receive_emoji_presentation(parts: list[str], width: int) -> None:
    text = "\u200d".join(parts)
    assert sum(display_width(part) for part in parts) == width
    assert display_width(text) == width
    assert shorten(text, width, flavor="posix", home_tilde=False) == text
    assert shorten(text, width - 1, flavor="posix", home_tilde=False) == (
        "..." if width > 4 else ""
    )


@pytest.mark.parametrize("slash", ["/", "\\"])
def test_windows_home_relative_to_current_drive_never_folds(slash: str) -> None:
    home = slash + "Users" + slash + "javi"
    path = home + slash + "report.txt"
    assert shorten(path, 100, flavor="windows", home=home) == path


@pytest.mark.parametrize(
    "anchor", ["C:\\", "\\\\srv\\share\\", "\\\\?\\C:\\", "\\\\.\\UNC\\srv\\share\\"]
)
def test_fully_qualified_windows_homes_still_fold(anchor: str) -> None:
    home = anchor + "Users\\javi"
    assert shorten(home + "\\report.txt", 100, flavor="windows", home=home) == "~\\report.txt"


@pytest.mark.parametrize("error_type", [RuntimeError, OSError])
@pytest.mark.parametrize("argument", ["path", "home"])
def test_path_provider_exceptions_propagate_unchanged(
    error_type: type[Exception], argument: str
) -> None:
    original = error_type("path provider failed")

    class BrokenPath:
        def __fspath__(self) -> str:
            raise original

    with pytest.raises(error_type) as caught:
        if argument == "path":
            shorten(BrokenPath(), 20)
        else:
            shorten("/home/u/file", 20, home=BrokenPath())
    assert caught.value is original


@pytest.mark.parametrize("sep", ["/", "::"])
def test_custom_windows_home_matching_is_case_sensitive(sep: str) -> None:
    path = sep + sep.join(["HOME", "u", "file"])
    home = sep + sep.join(["home", "u"])
    assert shorten(path, 80, flavor="windows", sep=sep, home=home) == path
    assert shorten(path, 80, flavor="windows", sep=sep, home=home.upper()) == path
    assert shorten(path, 80, flavor="windows", sep=sep, home=home.replace("home", "HOME")) == (
        "~" + sep + "file"
    )


@pytest.mark.parametrize(
    ("code", "width"),
    [(0xD7AF, 1), (0xD7B0, 0), (0xD7C7, 0), (0xD7FB, 0), (0xD7FC, 0), (0xD7FF, 0), (0xD800, 1)],
)
def test_extended_hangul_range_includes_unassigned_positions(code: int, width: int) -> None:
    char = chr(code)
    assert display_width(char) == width
    assert shorten("a" + char, 1, home_tilde=False) == ("a" + char if width == 0 else "a")

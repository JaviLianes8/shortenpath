"""Windows and POSIX path forms: the anchor is never cut, separators stay as written.

Forms from https://learn.microsoft.com/en-us/dotnet/standard/io/file-path-formats and the
POSIX.1-2024 base definitions 3.254 and 4.16; expected outputs are worked out by hand.
"""

from __future__ import annotations

import pytest

from shortenpath import shorten
from shortenpath._parts import split, windows_splitroot

B = "\\"


def win(path: str, width: int) -> str:
    return shorten(path.replace("|", B), width, flavor="windows", home_tilde=False).replace(B, "|")


@pytest.mark.parametrize(
    ("path", "anchor"),
    [
        ("C:|Documents|Newsletters|Summer2018.pdf", "C:|"),
        ("|Program Files|Custom Utilities|StringFinder.exe", "|"),
        ("2018|January.xlsx", ""),
        ("..|Publications|TravelBrochure.pdf", ""),
        ("C:Projects|apilibrary|apilibrary.sln", "C:"),
        ("||system07|C$|", "||system07|C$|"),
        ("||Server2|Share|Test|Foo.txt", "||Server2|Share|"),
        ("||.|C:|Test|Foo.txt", "||.|C:|"),
        ("||?|C:|Test|Foo.txt", "||?|C:|"),
        ("||.|Volume{b75e2c83-0000-0000-0000-602f00000000}|Test|Foo.txt", None),
        ("||.|UNC|Server|Share|Test|Foo.txt", "||.|UNC|Server|Share|"),
        ("||?|UNC|Server|Share|Test|Foo.txt", "||?|UNC|Server|Share|"),
        ("//server/share/dir/f", "//server/share/"),
        ("C:/x/y", "C:/"),
    ],
)
def test_the_anchor_of_each_documented_form(path: str, anchor: str | None) -> None:
    parts = split(path.replace("|", B), "windows", None)
    expected = path[: path.index("Test")] if anchor is None else anchor
    assert parts.anchor == expected.replace("|", B)
    assert parts.render() == path.replace("|", B)


def test_dot_unc_is_read_like_question_mark_unc() -> None:
    # The Microsoft page gives both ||.|UNC| and ||?|UNC| the server and share as volume;
    # ntpath.splitroot only singles out the second one.
    drive, root, rest = windows_splitroot("||.|unc|Server|Share|x".replace("|", B))
    assert (drive, root, rest) == ("||.|unc|Server|Share".replace("|", B), B, "x")


def test_unc_share_is_never_cut() -> None:
    path = "||server|share|dir|sub|file.txt"
    assert win(path, 30) == "||server|share|...|file.txt"
    assert win(path, 26) == "...|file.txt"


def test_device_prefix_and_volume_are_never_cut() -> None:
    assert win("||?|C:|x|y|z|file.txt", 19) == "||?|C:|...|file.txt"
    assert win("||?|C:|x|y|z|file.txt", 18) == "...|file.txt"
    assert win("||?|UNC|srv|sh|a|bb|f", 20) == "||?|UNC|srv|sh|...|f"


def test_drive_relative_path_keeps_its_drive() -> None:
    assert win("C:a|b|c|d|file", 12) == "C:a|...|file"
    assert win("C:a|b|c|d|file", 11) == "C:...|file"


def test_root_of_the_current_drive() -> None:
    assert win("|a|b|c|file", 9) == "|...|file"


def test_mixed_separators_are_both_separators_and_kept_as_written() -> None:
    assert win("C:/Users/x|AppData/Local\\Temp/a.txt", 24) == "C:/Users/x|.../a.txt"
    assert win("C:/a/b|c/d/e/file.txt", 19) == "C:/a/b|.../file.txt"


def test_verbatim_prefix_keeps_forward_slashes_inside_names() -> None:
    # Only a path starting exactly with \\?\ skips normalization, so "/" is not a separator.
    parts = split(B * 2 + "?\\C:\\a/b\\c", "windows", None)
    assert parts.anchor == B * 2 + "?\\C:\\"
    assert parts.names == ("a/b", "c")
    normalized = split("//?/C:/a/b/c", "windows", None)
    assert normalized.anchor == "//?/C:/"
    assert normalized.names == ("a", "b", "c")


def test_verbatim_prefix_forward_slash_stays_in_the_volume_name() -> None:
    parts = split("||?|C:/a|b".replace("|", B), "windows", None)
    assert parts.anchor == "||?|C:/a|".replace("|", B)
    assert parts.names == ("b",)


def test_the_last_name_keeps_the_separator_run_after_a_unc_share() -> None:
    path = "||srv|share|||verylongname.txt"
    assert win(path, 22) == "...|||verylongname.txt"
    assert win(path, 21) == "...|verylongname.txt"
    assert win(path, 16) == "verylongname.txt"


def test_incomplete_unc_is_all_anchor() -> None:
    parts = split(B * 2 + "server", "windows", None)
    assert parts.anchor == B * 2 + "server"
    assert parts.names == ()


def test_anchor_alone_wider_than_the_budget_is_cut_in_the_middle() -> None:
    volume = "||?|Volume{b75e2c83-0000-0000-0000-602f00000000}|"
    assert win(volume, 12) == "||?|V...00}|"


@pytest.mark.parametrize(
    ("path", "anchor", "names"),
    [
        ("/usr/lib", "/", ("usr", "lib")),
        ("//net/share", "//", ("net", "share")),
        ("///usr", "///", ("usr",)),
        ("usr/lib/", "", ("usr", "lib")),
        ("/", "/", ()),
        ("", "", ()),
        ("C:\\x\\y", "", ("C:\\x\\y",)),
    ],
)
def test_posix_paths(path: str, anchor: str, names: tuple[str, ...]) -> None:
    parts = split(path, "posix", None)
    assert (parts.anchor, parts.names) == (anchor, names)
    assert parts.render() == path


def test_posix_double_slash_stays_in_the_output() -> None:
    assert shorten("//net/a/b/c/file", 12, flavor="posix", home_tilde=False) == "//.../c/file"


def test_backslash_is_a_name_character_on_posix() -> None:
    assert shorten("/a/b\\c\\d/e", 9, flavor="posix", home_tilde=False) == "/a/.../e"

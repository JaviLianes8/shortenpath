"""Folding the home directory into ~ only where it really is the home directory."""

from __future__ import annotations

import os

import pytest

from shortenpath import Flavor, shorten

B = "\\"


def px(path: str, home: str | None, width: int = 80) -> str:
    return shorten(path, width, flavor="posix", home=home)


def win(path: str, home: str, width: int = 80) -> str:
    out = shorten(path.replace("|", B), width, flavor="windows", home=home.replace("|", B))
    return out.replace(B, "|")


def test_home_collapses_to_tilde() -> None:
    assert px("/home/javi/code/app.py", "/home/javi") == "~/code/app.py"


def test_home_itself_becomes_tilde_with_its_trailing_separator() -> None:
    assert px("/home/javi", "/home/javi") == "~"
    assert px("/home/javi/", "/home/javi") == "~/"


def test_home_given_with_a_trailing_separator() -> None:
    assert px("/home/javi/x", "/home/javi/") == "~/x"


def test_only_whole_components_match() -> None:
    assert px("/home/javier/x", "/home/javi") == "/home/javier/x"
    assert px("/home/jav", "/home/javi") == "/home/jav"


def test_posix_comparison_is_case_sensitive() -> None:
    assert px("/Home/Javi/x", "/home/javi") == "/Home/Javi/x"


def test_runs_of_slashes_in_either_side_still_match() -> None:
    assert px("/home//javi///x", "///home/javi") == "~///x"


def test_double_slash_root_is_a_different_root_on_posix() -> None:
    assert px("//home/javi/x", "/home/javi") == "//home/javi/x"


def test_a_relative_path_never_folds() -> None:
    assert px("home/javi/x", "/home/javi") == "home/javi/x"


@pytest.mark.parametrize("home", ["/", "", "///"])
def test_a_home_without_names_never_folds(home: str) -> None:
    assert px("/x/y", home) == "/x/y"


def test_windows_comparison_ignores_case_and_separator_kind() -> None:
    assert win("c:/users/JAVI/Documents|a.txt", "C:|Users|Javi") == "~/Documents|a.txt"
    assert win("C:|Users|Javi", "c:/users/javi/") == "~"


def test_windows_drive_root_as_home_never_folds() -> None:
    assert win("C:|x|y", "C:|") == "C:|x|y"


def test_windows_drive_relative_is_not_the_drive_root() -> None:
    assert win("C:Users|Javi|x", "C:|Users|Javi") == "C:Users|Javi|x"


def test_windows_unc_home() -> None:
    assert win("||srv|home|javi|a", "||SRV|home|javi") == "~|a"
    assert win("||srv|home|javi|a", "||srv|other|javi") == "||srv|home|javi|a"


def test_tilde_then_elision() -> None:
    path = "/home/javi/proj/sub/deep/file.py"
    assert px(path, "/home/javi", 18) == "~/proj/.../file.py"
    assert px(path, "/home/javi", 12) == ".../file.py"


def test_the_tilde_is_kept_like_an_anchor() -> None:
    assert px("/home/javi/a/b/c/d/f", "/home/javi", 7) == "~/.../f"


def test_home_tilde_off_leaves_home_alone() -> None:
    out = shorten("/home/javi/x", 80, flavor="posix", home="/home/javi", home_tilde=False)
    assert out == "/home/javi/x"


def test_default_home_is_the_running_user_for_native_paths() -> None:
    home = os.path.expanduser("~")
    flavor: Flavor = "windows" if os.name == "nt" else "posix"
    assert shorten(os.path.join(home, "x"), 200, flavor=flavor) == "~" + os.sep + "x"
    assert shorten(os.path.join(home, "x"), 200) == "~" + os.sep + "x"


def test_no_default_home_for_the_foreign_flavor_or_a_custom_separator() -> None:
    home = os.path.expanduser("~")
    foreign: Flavor = "posix" if os.name == "nt" else "windows"
    path = home + os.sep + "x"
    assert shorten(path, 200, flavor=foreign) == path
    assert shorten(path, 200, sep=os.sep) == path


def test_unknown_home_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os.path, "expanduser", lambda path: path)
    assert shorten(os.sep + "x", 200) == os.sep + "x"


def test_home_as_path_like() -> None:
    from pathlib import PurePosixPath

    out = shorten("/home/javi/x", 80, flavor="posix", home=PurePosixPath("/home/javi"))
    assert out == "~/x"

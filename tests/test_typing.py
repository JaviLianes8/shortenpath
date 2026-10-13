"""The public API is typed: mypy infers results and rejects bad calls."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

api = pytest.importorskip("mypy.api")

SRC = Path(__file__).resolve().parents[1] / "src"

SNIPPET = """
import pathlib
import shortenpath as s
reveal_type(s.shorten("/a/b", 10))
reveal_type(s.display_width("abc"))
s.shorten(b"/a/b", 10)
s.shorten("/a/b", "10")
s.shorten("/a/b", 10, flavor="mac")
s.shorten("/a/b", 10, sep=b"/")
s.display_width(b"abc")
s.shorten("/a/b", 10, "posix")
f: s.Flavor = "windows"
s.shorten(pathlib.PurePosixPath("/a/b"), 10, flavor=f, home=pathlib.Path("/a"))
s.shorten("/a/b", 10, home_tilde=False, home=None, sep="::", placeholder="~")
"""


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    cache = str(folder / "cache")
    out, err, _ = api.run(
        ["--strict", "--config-file", str(config), "--cache-dir", cache, str(target)]
    )
    return str(out) + str(err)


@pytest.mark.parametrize(("line", "expected"), [(4, r"(builtins\.)?str"), (5, r"(builtins\.)?int")])
def test_results_are_typed(mypy_output: str, line: int, expected: str) -> None:
    pattern = rf'snippet\.py:{line}: note: Revealed type is "{expected}"'
    assert re.search(pattern, mypy_output), mypy_output


@pytest.mark.parametrize("line", [6, 7, 8, 9, 10])
def test_wrong_calls_are_rejected(mypy_output: str, line: int) -> None:
    assert re.search(rf"snippet\.py:{line}: error: .*\[arg-type\]", mypy_output), mypy_output


def test_options_are_keyword_only(mypy_output: str) -> None:
    assert re.search(r"snippet\.py:11: error: Too many positional", mypy_output), mypy_output


def test_the_alias_and_good_calls_pass(mypy_output: str) -> None:
    for line in range(12, 15):
        assert not re.search(rf"snippet\.py:{line}: error", mypy_output), mypy_output

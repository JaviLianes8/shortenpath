"""Seeded hostile text and bounded work for long clusters and many segments."""

from __future__ import annotations

import random

import pytest

from shortenpath import display_width, shorten
from shortenpath._cli import main
from shortenpath._width import clusters


def test_a_selector_placeholder_cannot_overflow_the_final_budget() -> None:
    assert shorten("a/b/c/file", 1, sep="/", placeholder="\ufe0f") == ""
    assert shorten("a/b/c/file", 2, sep="/", placeholder="\ufe0f") == "f\ufe0f"


def test_seeded_unicode_options_always_fit_and_are_repeatable() -> None:
    rng = random.Random(10002026)
    alphabet = ["a", "/", "\\", "::", ".", "\u65e5", "\u0301", "\ufe0f", "\u200d", "\x00", "\ud800"]
    for _ in range(20000):
        text = "".join(rng.choices(alphabet, k=rng.randrange(50)))
        sep = rng.choice(["/", "::", "\ufe0f", "\u200d", "\u0301", ".*"])
        placeholder = rng.choice(alphabet)
        width = rng.randrange(1, 30)
        out = shorten(text, width, sep=sep, placeholder=placeholder, home_tilde=False)
        assert display_width(out) <= width, (ascii(text), width, ascii(out))
        assert shorten(out, width, sep=sep, placeholder=placeholder, home_tilde=False) == out


@pytest.mark.parametrize("unit", ["\u0301", "\ufe0f", "\u200da"])
def test_long_clusters_remain_whole_and_fit(unit: str) -> None:
    text = "a" + unit * 100000
    assert len(clusters(text)) == 1
    out = shorten(text + "zzz", 3, home_tilde=False)
    assert display_width(out) <= 3


def test_many_components_keep_the_documented_tie_break() -> None:
    text = "/" + "a/" * 20000 + "file"
    assert shorten(text, 13, flavor="posix", home_tilde=False) == "/a/b/.../file".replace("b", "a")


@pytest.mark.parametrize("option", ["--width", "--flavor", "--unknown"])
def test_cli_errors_do_not_quote_secrets_or_huge_values(
    capsys: pytest.CaptureFixture[str], option: str
) -> None:
    with pytest.raises(SystemExit) as caught:
        main([option, "private-value" * 10000, "x"])
    assert caught.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "private-value" not in captured.err
    assert len(captured.err) < 700

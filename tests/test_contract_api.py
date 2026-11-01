"""Stable signatures, literal choices, typed failures and public docstrings."""

from __future__ import annotations

import doctest
import inspect
from typing import get_args, get_type_hints

import pytest

import shortenpath as s


def test_flavor_is_the_three_string_literal_alias() -> None:
    assert get_args(s.Flavor) == ("native", "posix", "windows")


def test_public_namespace_has_only_the_declared_names() -> None:
    assert {name for name in vars(s) if not name.startswith("_")} == set(s.__all__)


def test_signatures_and_defaults_are_stable() -> None:
    params = inspect.signature(s.shorten).parameters
    assert list(params) == ["path", "width", "flavor", "home_tilde", "home", "sep", "placeholder"]
    for name in ("path", "width"):
        assert params[name].default is inspect.Parameter.empty
        assert params[name].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    defaults = {
        "flavor": "native",
        "home_tilde": True,
        "home": None,
        "sep": None,
        "placeholder": "...",
    }
    for name, default in defaults.items():
        assert params[name].default == default
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY
    assert list(inspect.signature(s.display_width).parameters) == ["text"]
    assert get_type_hints(s.shorten)["return"] is str
    assert get_type_hints(s.display_width) == {"text": str, "return": int}


@pytest.mark.parametrize("name", s.__all__)
def test_every_public_docstring_has_passing_examples(name: str) -> None:
    doc = inspect.getdoc(getattr(s, name))
    assert doc is not None and ">>>" in doc
    runner = doctest.DocTestRunner()
    runner.run(doctest.DocTestParser().get_doctest(doc, {}, name, None, 0))
    assert runner.tries >= 2 and runner.failures == 0


@pytest.mark.parametrize(
    ("options", "error", "message"),
    [
        ({"width": False}, TypeError, "width must be int"),
        ({"width": 0}, ValueError, "width must be at least 1"),
        ({"width": -(10**5000)}, ValueError, "width must be at least 1"),
        ({"home_tilde": 1}, TypeError, "home_tilde must be bool"),
        ({"home": b"secret"}, TypeError, "home must be str or os.PathLike[str]"),
        ({"flavor": object()}, TypeError, "flavor must be str"),
        ({"flavor": "secret" * 10000}, ValueError, "flavor must be 'native', 'posix' or 'windows'"),
        ({"sep": 5}, TypeError, "sep must be str or None"),
        ({"sep": ""}, ValueError, "sep must be a non-empty string"),
        ({"placeholder": None}, TypeError, "placeholder must be str"),
        ({"placeholder": ""}, ValueError, "placeholder must be a non-empty string"),
    ],
)
def test_errors_have_fixed_types_and_safe_messages(
    options: dict[str, object], error: type[Exception], message: str
) -> None:
    args: dict[str, object] = {"width": 10, **options}
    with pytest.raises(error) as caught:
        s.shorten("private/path", **args)  # type: ignore[arg-type]
    assert type(caught.value) is error
    assert str(caught.value) == message


def test_type_names_and_pathlike_return_errors_are_not_echoed() -> None:
    value = type("secret" * 10000, (), {})()
    with pytest.raises(TypeError, match=r"^text must be str$"):
        s.display_width(value)
    with pytest.raises(TypeError, match=r"^path must be str or os.PathLike\[str\]$"):
        s.shorten(value, 10)

    class BadPath:
        def __fspath__(self) -> str:
            raise TypeError("secret" * 10000)

    with pytest.raises(TypeError, match=r"^path must be str or os.PathLike\[str\]$"):
        s.shorten(BadPath(), 10)


def test_disabled_home_folding_does_not_read_home() -> None:
    class UnusedHome:
        def __fspath__(self) -> str:
            raise AssertionError("home was evaluated")

    assert s.shorten("/a", 10, home_tilde=False, home=UnusedHome()) == "/a"


def test_huge_positive_width_does_not_need_integer_string_conversion() -> None:
    assert s.shorten("/a", 10**5000, home_tilde=False) == "/a"

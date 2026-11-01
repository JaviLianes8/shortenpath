"""Built-in subclass values are used without invoking their overridden methods."""

from __future__ import annotations

from typing import cast

import pytest

from shortenpath import Flavor, display_width, shorten


class MisleadingWidth(int):
    def __lt__(self, other: object) -> bool:
        return False


class MisleadingSeparator(str):
    def __eq__(self, other: object) -> bool:
        return False


def _fail(*args: object, **kwargs: object) -> object:
    raise RuntimeError("private-value" * 10000)


# Hand-written hostile subclasses exercise every public argument boundary.
HostileInt = type(
    "HostileInt", (int,), dict.fromkeys(["__lt__", "__int__", "__index__", "__str__"], _fail)
)
HostileStr = type(
    "HostileStr",
    (str,),
    dict.fromkeys(
        [
            "__str__",
            "__iter__",
            "__len__",
            "__bool__",
            "__eq__",
            "__getitem__",
            "__hash__",
            "startswith",
            "replace",
            "lower",
            "__fspath__",
        ],
        _fail,
    ),
)


def test_integer_subclass_cannot_bypass_the_width_budget() -> None:
    assert shorten("abcdef", MisleadingWidth(1), home_tilde=False) == "a"


def test_integer_subclass_cannot_bypass_positive_width_validation() -> None:
    with pytest.raises(ValueError, match=r"^width must be at least 1$"):
        shorten("abcdef", MisleadingWidth(-1), home_tilde=False)


def test_separator_subclass_cannot_bypass_nonempty_validation() -> None:
    with pytest.raises(ValueError, match=r"^sep must be a non-empty string$"):
        shorten("abcdef", 2, sep=MisleadingSeparator(""), home_tilde=False)


def test_width_subclass_conversion_does_not_call_overrides() -> None:
    assert shorten("abcdef", HostileInt(1), home_tilde=False) == "a"
    with pytest.raises(ValueError, match=r"^width must be at least 1$"):
        shorten("abcdef", HostileInt(-1), home_tilde=False)


def test_display_width_uses_string_subclass_contents() -> None:
    assert display_width(HostileStr("a\u0301\u65e5")) == 3


@pytest.mark.parametrize("argument", ["path", "home", "flavor", "sep", "placeholder"])
def test_shortening_normalizes_each_string_argument(argument: str) -> None:
    values = {
        "path": "/home/u/a/b/c/file",
        "home": "/home/u",
        "flavor": "posix",
        "sep": "/",
        "placeholder": "...",
    }
    values[argument] = HostileStr(values[argument])
    assert (
        shorten(
            values["path"],
            10,
            home=values["home"],
            flavor=cast(Flavor, values["flavor"]),
            sep=values["sep"],
            placeholder=values["placeholder"],
        )
        == "~/.../file"
    )


@pytest.mark.parametrize("argument", ["path", "home"])
def test_path_provider_string_subclasses_are_normalized(argument: str) -> None:
    class TextPath:
        def __fspath__(self) -> str:
            return cast(str, HostileStr("/home/u"))

    if argument == "path":
        assert shorten(TextPath(), 80, flavor="posix", home_tilde=False) == "/home/u"
    else:
        assert shorten("/home/u/file", 80, flavor="posix", home=TextPath()) == "~/file"


@pytest.mark.parametrize("argument", ["sep", "placeholder", "flavor"])
def test_empty_string_subclasses_receive_fixed_value_errors(argument: str) -> None:
    options = {argument: HostileStr("")}
    with pytest.raises(ValueError) as caught:
        shorten("abcdef", 2, **options)
    expected = {
        "sep": "sep must be a non-empty string",
        "placeholder": "placeholder must be a non-empty string",
        "flavor": "flavor must be 'native', 'posix' or 'windows'",
    }
    assert str(caught.value) == expected[argument]

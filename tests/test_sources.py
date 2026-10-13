"""Facts read from the third-party sources fetched by scripts/fetch_sources.py.

The sources are not committed; these tests skip when tests/sources holds only the MANIFEST.
The expected anchors below are worked out by hand from the descriptions on those pages.
"""

from __future__ import annotations

import html
import re
import sys
import unicodedata
from pathlib import Path

import pytest

from shortenpath import shorten
from shortenpath._name import squeeze
from shortenpath._parts import split
from shortenpath._width import char_width

SOURCES = Path(__file__).resolve().parent / "sources"
B = "\\"


def _read(name: str) -> str:
    path = SOURCES / name
    if not path.is_file():
        pytest.skip(f"{name} not fetched; run scripts/fetch_sources.py")
    return path.read_text(encoding="utf-8")


def _plain(name: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", _read(name))).split())


DOTNET_ANCHORS = {
    "C:|Documents|Newsletters|Summer2018.pdf": "C:|",
    "|Program Files|Custom Utilities|StringFinder.exe": "|",
    "2018|January.xlsx": "",
    "..|Publications|TravelBrochure.pdf": "",
    "C:|Projects|apilibrary|apilibrary.sln": "C:|",
    "C:Projects|apilibrary|apilibrary.sln": "C:",
    "||system07|C$|": "||system07|C$|",
    "||Server2|Share|Test|Foo.txt": "||Server2|Share|",
    "||.|C:|Test|Foo.txt": "||.|C:|",
    "||?|C:|Test|Foo.txt": "||?|C:|",
    "||.|Volume{b75e2c83-0000-0000-0000-602f00000000}|Test|Foo.txt": (
        "||.|Volume{b75e2c83-0000-0000-0000-602f00000000}|"
    ),
    "||?|Volume{b75e2c83-0000-0000-0000-602f00000000}|Test|Foo.txt": (
        "||?|Volume{b75e2c83-0000-0000-0000-602f00000000}|"
    ),
    "||.|UNC|Server|Share|Test|Foo.txt": "||.|UNC|Server|Share|",
    "||?|UNC|Server|Share|Test|Foo.txt": "||?|UNC|Server|Share|",
}

WIN32_ANCHORS = {
    "C:tmp.txt": "C:",
    "C:tempdir|tmp.txt": "C:",
    "..|tmp.txt": "",
    "..|..|tmp.txt": "",
    "..|tempdir|tmp.txt": "",
    "C:..|tmp.txt": "C:",
}


def _check(paths: list[str], expected: dict[str, str]) -> None:
    assert sorted(path.replace(B, "|") for path in paths) == sorted(expected)
    for path in paths:
        parts = split(path, "windows", None)
        assert parts.anchor.replace(B, "|") == expected[path.replace(B, "|")], path
        assert parts.render() == path


def test_dotnet_path_format_examples() -> None:
    text = _read("file-path-formats.md")
    rows = re.findall(r"^\| `([^`]+)` \|", text, flags=re.MULTILINE)
    bullets = re.findall(r"^\s*- `([^`]+)`\s*$", text, flags=re.MULTILINE)
    _check(rows + bullets, DOTNET_ANCHORS)


def test_dotnet_rules_this_library_relies_on() -> None:
    text = " ".join(_read("file-path-formats.md").split())
    # Forward slashes are separators, except in a path that starts exactly with \\?\.
    assert "All forward slashes (`/`) are converted" in text
    assert "Unless the path starts exactly with `" + B * 2 + "?" + B + "`" in text
    # Both \\.\UNC\ and \\?\UNC\ take server and share as the volume.
    assert "For device UNCs, the server/share portion forms the volume" in text


def test_win32_relative_path_examples() -> None:
    text = _read("naming-a-file.md").replace(B * 2, B)
    examples = re.findall(r'^- "([^"]+)" (?:refers|specifies)', text, flags=re.MULTILINE)
    examples += re.findall(r'combine both example types, for example "([^"]+)"', text)
    _check(examples, WIN32_ANCHORS)


def test_win32_reserves_both_slashes() -> None:
    text = _read("naming-a-file.md")
    assert "- / (forward slash)" in text
    assert "- " + B * 2 + " (backslash)" in text


def test_compact_path_documented_example() -> None:
    text = " ".join(_read("nf-shlwapi-pathcompactpathexw.md").split())
    found = re.search(
        r'input file name is "([^"]+)" and <i>cchMax</i> is (\d+), '
        r'<b>PathCompactPathEx</b> will return "([^"]+)"',
        text,
    )
    assert found is not None
    name, cch, result = found.group(1), int(found.group(2)), found.group(3)
    assert "The '/' separator will be used instead of" in text
    # cchMax counts the terminating null; the cut here keeps the start and the end of the name.
    assert squeeze(name, cch - 1, "...") == "My ...ame"
    if sys.platform == "win32":
        from test_win32 import compact

        assert compact(name, cch - 1) == result


def test_posix_leading_slashes() -> None:
    text = _plain("posix-v1-chap04.html")
    assert "more than two leading <slash> characters shall be treated as a single <slash>" in text
    home = "/home/javi"
    assert shorten("///home/javi/x", 80, flavor="posix", home=home) == "~/x"
    assert shorten("//home/javi/x", 80, flavor="posix", home=home) == "//home/javi/x"


def test_posix_filename_and_home_definitions() -> None:
    text = _plain("posix-v1-chap03.html")
    assert "shall not contain the <NUL> or <slash> characters" in text
    assert "3.170 Home Directory The directory specified by the HOME environment variable" in text
    assert split("/a\\b/c", "posix", None).names == ("a\\b", "c")


def _east_asian_widths() -> dict[int, str]:
    table: dict[int, str] = {}
    text = _read(f"EastAsianWidth-{unicodedata.unidata_version}.txt")
    for line in text.splitlines():
        found = re.match(r"([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*(\w+)", line)
        if found:
            first = int(found.group(1), 16)
            last = int(found.group(2) or found.group(1), 16)
            for code in range(first, last + 1):
                table[code] = found.group(3)
    return table


def test_wide_and_fullwidth_take_two_columns_in_this_unicode_version() -> None:
    table = _east_asian_widths()
    counted = {"W": 0, "F": 0, "other": 0}
    for code, value in table.items():
        char = chr(code)
        category = unicodedata.category(char)
        if category in ("Cn", "Mn", "Me", "Cf", "Cs") or 0x1160 <= code <= 0x11FF:
            continue
        key = value if value in ("W", "F") else "other"
        counted[key] += 1
        assert char_width(char) == (2 if key != "other" else 1), (hex(code), value)
    assert counted["W"] > 90000 and counted["F"] > 90 and counted["other"] > 30000

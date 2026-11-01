# shortenpath guide

`shortenpath` creates display labels. It does not resolve paths, open files, expand
environment variables, collapse `.` or `..`, or check whether a path exists.

## Public API

Import `Flavor`, `display_width` and `shorten` from `shortenpath`. `__version__` contains
the release version. `Flavor` is `Literal["native", "posix", "windows"]`, a type alias,
not a parser or a class to instantiate.

```python
from shortenpath import Flavor, display_width, shorten

rules: Flavor = "posix"
print(shorten("/a/b/c/d/e/file", 11, flavor=rules, home_tilde=False))
print(display_width("a\u0301\u65e5"))
# /a/.../file
# 3
```

`shorten(path, width, *, flavor="native", home_tilde=True, home=None, sep=None,
placeholder="...") -> str` accepts `str` or `os.PathLike[str]` for the path and home.
The width is a positive `int`, excluding `bool`. The parameter names, keyword-only options,
defaults and three public exports are part of the 1.0 contract.
Accepted `str` and `int` subclasses are normalized to their built-in values before
validation and processing, without calling overridden conversion, comparison or iteration
methods. This includes strings returned by `__fspath__`; boolean widths remain invalid.

`display_width(text: str) -> int` returns a nonnegative column estimate. Empty text has
width zero; an empty path stays empty. There is no fixed maximum input length or width.

## Path rules and selection

`native` selects Windows rules on Windows and POSIX rules elsewhere; an explicit flavor
works on any operating system. POSIX splits only on `/`. Windows splits on both slashes,
preserves drive-relative and absolute forms, UNC server/share anchors and device prefixes.
An exact `\\?\` prefix makes `/` a name character. Runs and trailing separators are kept.
Custom `sep` is a nonempty literal string, including multi-character strings; it replaces
the flavor's path grammar and does not recognize URL schemes or drive prefixes.

Home folding compares whole components. POSIX comparisons are case sensitive; Windows
uses lowercase comparisons and treats either separator kind alike. Two leading POSIX
slashes are distinct from one; three or more compare as one. Relative homes and bare
roots do not fold. A Windows home must have both a drive/UNC/device volume and a root:
`\Users\javi` and `/Users/javi` are relative to the current drive and do not fold.
Custom separators use case-sensitive component comparisons and their own root grammar.
Without an explicit home, only native paths with no custom separator use
`os.path.expanduser("~")`. If the home is unknown, nothing folds.

After folding, a fitting path is returned unchanged. Otherwise the selection order is:

1. Anchor plus placeholder plus the last name, keeping as many whole names around the
   placeholder as fit. At least one name is omitted; ties keep more names at the start.
2. Placeholder plus the last separator run plus the last name and trailing separators.
   If needed, the separator run shrinks to its last character, including for custom separators.
3. Last name plus trailing separators, then last name alone.
4. For a single name, the anchor and trailing separators plus a middle cut if room permits.
5. A middle cut of the last name, without the anchor or trailing separators. An anchor-only
   path is itself cut as a name.

A middle cut shares the remaining budget between the start and end, preferring the start
for an odd column. It keeps the extension and last stem character when both those and
the first stem character fit. Leading dots alone are not an extension. If the placeholder
does not fit, only a fitting prefix remains; that prefix may be empty. The first cluster
is kept whenever it fits; otherwise the suffix may take all the remaining room.

## Width convention and limits

East Asian W/F code points take two columns. Mn/Me/Cf code points and Hangul medial/final
jamo take zero, except soft hyphen takes one. A variation selector U+FE0F raises its
joined component to at least two columns before the components are summed. Other code
points, including controls, take one.
The zero-width ranges U+1160 through U+11FF and U+D7B0 through U+D7FF are inclusive,
including their unassigned positions. Outside those ranges, unassigned code points follow
the same category and East Asian width rules as other code points.
The Unicode database bundled with Python determines categories and East Asian widths,
so newly assigned characters can measure differently across Python releases.

A cuttable cluster is a character followed by zero-width characters; a zero-width
joiner also pulls in the next character. Joined emoji widths are summed. This is not the
Unicode grapheme algorithm, terminal emulation or escape-sequence handling. Tabs and
newlines are preserved, not expanded. Sanitize untrusted text before displaying it in a
terminal. There is no guarantee that every terminal renders the same number of columns.

Separately measured pieces can change width when joined, especially when a separator or
placeholder starts with U+FE0F. The final output is remeasured. If it exceeds the budget,
only its longest fitting cluster-aligned prefix is returned, even if this drops the name.
The guarantee is always `display_width(result) <= width`.

Cluster assembly is linear in text length. Selecting whole segments takes O(n log n)
time and O(n) memory for n components, plus linear work in the input text and custom
separator length. Custom separator matching uses nonoverlapping literal occurrences.

## Errors and command line

| Condition | Exception |
| --- | --- |
| Path/home is neither text nor a text-returning path object | `TypeError` |
| Width is not an int, or is bool | `TypeError` |
| `home_tilde` is not bool, or flavor/placeholder is not str | `TypeError` |
| `sep` is neither str nor None | `TypeError` |
| Width below one, empty separator/placeholder, unknown flavor | `ValueError` |

Messages are fixed and do not quote values or type names. `home` is not read or validated
when `home_tilde=False`. Type errors from `__fspath__` receive a fixed message; other
exceptions from a user-supplied `__fspath__` propagate unchanged.

`shortenpath` and `python -m shortenpath` take paths as arguments or one per stdin line.
Use `--` before a path beginning with `-`. `-w` defaults to the terminal width (80 when
unavailable). `-f` chooses the flavor. `--home`, `--no-tilde`, `--sep`, `--placeholder`,
`--help` and `--version` are supported. Each output line is flushed immediately.
Invalid options exit 2 before stdin is read; success and a closed output pipe exit 0.
Stdin lines lose only their line endings; spaces and tabs remain part of each path.
Input decoding failures exit 2 with `shortenpath: cannot decode standard input`, without
quoting the input or printing a traceback. The stream's configured decoder is respected.
Unencodable output characters use replacement characters for the stream's encoding.

## Upgrading from 0.2.0

Install with `python -m pip install --upgrade shortenpath`. Names, signatures, default
values and ordinary path results are unchanged. Callers passing invalid option types
must now catch `TypeError`. Do not depend on old input-quoting error text. A selector
placeholder may produce a shorter result to honor the budget. Joined emoji selectors now
adjust each component, so some joined emoji require a larger budget. Current-drive-relative
Windows homes no longer fold. Built-in subclasses use their stored values. The
[CHANGELOG](https://github.com/JaviLianes8/shortenpath/blob/main/CHANGELOG.md) lists every change.

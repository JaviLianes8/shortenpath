# shortenpath

Shorten a filesystem path to fit a terminal column budget for prompts, status bars, tables
and logs. The home folder folds to `~`, the root and the file name stay, and whole folders
in the middle give way to `...`. Display only: the filesystem is never read.

## Install

```
pip install shortenpath
```

## Usage

```python
from shortenpath import shorten

path = "/home/javi/projects/shop/src/cart/checkout.py"
print(shorten(path, 60, flavor="posix", home="/home/javi"))
print(shorten(path, 30, flavor="posix", home="/home/javi"))
print(shorten(path, 22, flavor="posix", home="/home/javi"))
print(shorten(path, 14, flavor="posix", home="/home/javi"))
print(shorten(path, 9, flavor="posix", home="/home/javi"))
# ~/projects/shop/src/cart/checkout.py
# ~/.../src/cart/checkout.py
# ~/.../cart/checkout.py
# checkout.py
# ch...t.py
```

Windows paths keep their drive, UNC share or device prefix whole, and both `\` and `/`
separate folders (each kept as written). The home folder matches regardless of case.

```python
from shortenpath import shorten

print(shorten(r"C:\Users\javi\AppData\Local\Temp\report.pdf", 24, flavor="windows"))
print(shorten(r"\\fileserver\finance\2026\q3\budget.xlsx", 36, flavor="windows"))
print(shorten(r"\\?\C:\very\deep\tree\of\folders\notes.txt", 26, flavor="windows"))
print(
    shorten("C:/Users/javi/Downloads/tools/setup.exe", 26, flavor="windows", home=r"c:\users\javi")
)
# C:\Users\...\report.pdf
# \\fileserver\finance\...\budget.xlsx
# \\?\C:\very\...\notes.txt
# ~/Downloads/.../setup.exe
```

The budget is in terminal columns: East Asian wide characters take two, combining accents
none, and a cut never splits a letter from its accent.

```python
from shortenpath import display_width, shorten

path = "/srv/写真/2026/夏休み/海辺の夕焼け.jpg"
print(display_width(path), len(path))
print(shorten(path, 30, flavor="posix"))
print(shorten(path, 24, flavor="posix"))
# 38 27
# /srv/写真/.../海辺の夕焼け.jpg
# /.../海辺の夕焼け.jpg
```

Any separator and any placeholder:

```python
from shortenpath import shorten

print(shorten("docs::api::v2::internal::client", 20, sep="::"))
print(shorten("/var/log/nginx/access.log", 16, flavor="posix", placeholder="…"))
# docs::...::client
# /…/access.log
```

## The rules

`shorten(path, width, *, flavor="native", home_tilde=True, home=None, sep=None,
placeholder="...")` returns `path` itself when it fits, otherwise the first of these that
fits `width` columns:

1. The anchor, then as many whole folders as fit around the placeholder, then the last
   name: the form keeping the most names wins, and between equals the one keeping more at
   the start. The anchor is a POSIX root (`/`, `//`), a drive (`C:\`, `C:`), a UNC share
   (`\\server\share\`), a device path (`\\.\C:\`, `\\?\Volume{...}\`,
   `\\?\UNC\server\share\`) or `~`.
2. The placeholder, the separator and the last name: the whole name is worth more than the
   anchor. A run of separators that does not fit shrinks to one.
3. The last name alone, then the anchor with the name cut in the middle (a path with a
   single name and room for both).
4. The last name cut in the middle: its start, the placeholder, and its end, which keeps
   the extension and the stem character before it when there is room for them. With no
   room for the placeholder only the start of the name is kept, and when not even its first
   character fits the result is empty.

| Option | Meaning |
| --- | --- |
| `flavor` | `"posix"`, `"windows"` or `"native"` (the running system). `Flavor` is its type. |
| `home_tilde`, `home` | Fold the home folder to `~`. `home` defaults to the current user's for native paths. A relative home, or one that is only a root, never folds. |
| `sep` | A custom separator instead of the flavor's rules, for URLs or keys. |
| `placeholder` | What stands for the removed folders, `...` by default. |

Separator runs are kept as written. On Windows a path that starts exactly with `\\?\`
skips normalization, so there only `\` separates and `/` is part of a name.
`display_width(text)` gives the columns of any text: East Asian wide and fullwidth
characters and characters with the emoji presentation selector take two, combining marks,
format characters and Hangul medial and final jamo none, everything else (control
characters included) one. Emoji joined into one picture are counted as their parts, which
can only overestimate. Wrong types raise `TypeError`; a
width below one or an empty separator or placeholder raises `ValueError`.

Compared with the Win32 `PathCompactPathEx` function, this never cuts inside the
anchor or a folder name, keeps the extension of a cut name, counts columns instead of
characters, and returns a path exactly as long as the budget unchanged.

## Command line

```
$ shortenpath -w 24 -f posix --home /home/javi /home/javi/projects/shop/src/cart/checkout.py
~/.../cart/checkout.py
$ shortenpath -w 24 -f windows 'C:\Program Files\Common Files\system\ado\msado15.dll'
C:\...\ado\msado15.dll
```

Paths come from the arguments, or one per line from standard input, each written as soon
as it is read. `-w` defaults to the terminal width. Bad input exits with status 2.
`python -m shortenpath` works too.

## Why

Folding a path to `~` and trimming its middle to fit a column budget is a common need,
yet on PyPI the pieces live apart: `os.path.expanduser` only expands, and
`textwrap.shorten` cuts words from the end, not folders from the middle. Most snippets
that do it count characters, split on one separator and cut UNC shares in half. This one
reads Windows and POSIX path forms, counts columns, and has no dependencies.

## Development

`python scripts/fetch_sources.py` downloads the Microsoft, POSIX and Unicode texts the
tests check the rules against (listed with their hashes in `tests/sources/MANIFEST.txt`);
without them those tests skip. `SHORTENPATH_E2E=1 pytest` also builds the wheel and tests
the installed package. `scripts/check.ps1` runs the whole gate.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/

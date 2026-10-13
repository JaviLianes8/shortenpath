# shortenpath improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Path forms: POSIX roots, Windows drives, UNC, `\\?\` and `\\.\` device paths, mixed separators
- [x] Display width: wide and fullwidth characters count two columns, combining marks none
- [x] Home folding to `~` that respects component boundaries and Windows case rules
- [x] File name kept whole when it can be, extension kept when the name is cut
- [x] Deterministic elision search (most segments kept, then most head segments)
- [x] Typed API: `Flavor` alias, `display_width`, clean `TypeError` and `ValueError`
- [x] Command line tool (`shortenpath`, `python -m shortenpath`)
- [x] Contracts: fetched sources, stdlib and Win32 oracles, properties, typing, README, wheel e2e
- [ ] Mutation run (guards changed one at a time, each must fail the suite)
- [x] Docs: README, CHANGELOG, docstrings, packaging metadata
- [ ] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` (not on PyPI) ships `shorten(path, max_len, *, home_tilde, home, sep, placeholder)`.
Read as a user who puts paths in prompts, status bars, tables and logs:

- One separator only, `os.sep` by default. On Windows `C:/Users/x` is one segment; on Linux a
  Windows path from a log cannot be shortened unless the caller picks `sep="\\"`, and then
  `/` inside it is not a separator.
- The only root it knows is a leading separator. `\\server\share\dir\f` is elided into
  `\...\f`, losing the server and share; `\\?\C:\x\y\f` loses the device prefix and the drive.
- Length is `len()`. A path with CJK names or fullwidth characters takes twice the columns it
  is budgeted for; a name with combining accents is budgeted for columns it never uses, and a
  cut can separate a letter from its accent.
- Home folding compares raw strings: `C:\Users\Javi` does not fold `c:\users\javi\x` on
  Windows, and `home="C:\\"` folds every path on the drive into `~\...`.
- When the name does not fit it keeps only its end; the start of the name is lost first.
- No command line tool, README examples not executed, no wheel test, no ground truth in the
  tests.

## Sources (fetched 2026-10-13)

- File path formats on Windows systems, dotnet/docs at 3ad903a7:
  traditional DOS paths (`C:\`, `\dir` relative to the current drive, `C:dir` relative to the
  current directory of drive C), UNC paths (`\\server\share` is the volume), DOS device paths
  (`\\.\` and `\\?\`, the first segment after the prefix names the volume, `UNC\server\share`
  for network shares), forward slashes are separators except in a path that starts exactly
  with `\\?\`, which skips normalization.
- Naming Files, Paths, and Namespaces, MicrosoftDocs/win32 at ca8274de: backslash and forward
  slash are both reserved; the prefix of a path decides its namespace.
- PathCompactPathExW, MicrosoftDocs/sdk-api at 656e9656: replaces path components with an
  ellipsis to fit a character count, keeps `/` if the input used it, truncates a bare file
  name at the end. Probed live through `shlwapi.dll` on Windows 11: it counts characters, not
  columns, cuts inside the UNC server name (`\\serv...\file.txt`), cuts inside directory names (`C:\path1...\sample.txt`)
  and drops the extension when the name is cut (`...\verylon...`).
- POSIX.1-2024 base definitions 3.2, 3.42, 3.146, 3.170, 3.254, 3.256 and 4.16: a filename
  never contains a slash, runs of slashes equal one, exactly two leading slashes are
  implementation defined, three or more equal one; the home directory is `HOME`.
- Unicode UAX #11 and `EastAsianWidth.txt` for Unicode 13.0.0 to 17.0.0: classes W and F take
  two cells in East Asian contexts; terminals follow that, plus zero width for combining marks.
- The texts are third-party and not committed: `scripts/fetch_sources.py` fetches them into a
  gitignored folder checked against a tracked MANIFEST; the tests that read them skip when the
  folder is absent.

## Ranked improvements

1. **Path forms.** A `flavor` (`"posix"`, `"windows"`, `"native"`) decides the separators and
   the anchor. The anchor (drive, root, UNC server and share, device prefix and volume) is
   never cut. Windows takes `\` and `/` everywhere except after an exact `\\?\`. Runs of
   separators and the original separator characters are kept as written. The anchor split
   agrees with `ntpath.splitroot` and `posixpath.splitroot` where they exist.
2. **Display width.** `display_width(text)` counts W and F as two columns, combining marks,
   format characters and Hangul medial and final jamo as zero, everything else as one. The
   budget is in columns, cuts never split a base from its marks or a zero width joiner from
   the next character, and the result never exceeds the budget.
3. **Home folding.** Only on a component boundary, never for a home that is a bare anchor,
   case-insensitive and separator-insensitive on Windows, keeping the separator written in the
   path after `~`.
4. **Name and extension.** The last segment is kept whole whenever `.../name` fits; a name that
   cannot fit is cut in the middle, keeping its start and its extension.
5. **Deterministic elision.** Among all forms `anchor head/.../tail` that fit, keep the most
   segments, then the most head segments. One rule, `O(n log n)`, documented with examples.
6. **Typed API and failures.** `Flavor` literal alias, `width` in columns, `os.PathLike`
   accepted, `TypeError` for bytes and non-strings, `ValueError` for a width below one or an
   empty separator or placeholder.
7. **Command line tool.** `shortenpath [-w COLS] [--flavor] [--no-tilde] [--home] PATH...`,
   lines from stdin without paths, terminal width by default, exit 2 on bad input, quiet on a
   closed pipe.
8. **Contracts that bite.** Examples from the fetched Microsoft and POSIX texts, the width table
   of the running Unicode version, `splitroot` oracles over fuzzed paths, the live Win32
   function on Windows as a reference, properties over fuzzed paths (fits, deterministic,
   anchor and name kept when they fit), executed README, installed-wheel e2e, mutation run.
9. **Docs and packaging.** README with the rules and a table of forms, CHANGELOG 0.2.0,
   classifiers and keywords, console script.

Left out on purpose: resolving `.` and `..` or symlinks (display only, never touches disk),
grapheme clusters beyond marks and joiners (emoji sequences differ between terminals),
ambiguous width characters as two columns (terminal setting, not data), URL schemes.

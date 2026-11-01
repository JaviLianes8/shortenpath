# shortenpath 1.0.0 certification report

The 1.0.0 certification bar applied to shortenpath. On 2026-11-01,
`https://pypi.org/pypi/shortenpath/json` returned 0.2.0. Its installed Python modules
match `main` (45b7e87). Every behavior change is listed in the dated CHANGELOG section.

Progress:
- [x] Branch `release/1.0.0` created from `main` (0.2.0, 45b7e87)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: sources fetched live, reference programs run (item 7)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12); render check pending
- [ ] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [ ] Gates (item 15)
- [ ] PR and trace guard CLEAN; the independent reviewer (16), merge and publish (17) and the
      five QA lenses (19) follow

## Baseline and API review

At 78a5e86, format, lint and strict typing passed. Pytest: 213 passed, 9 skipped
(eight source-dependent tests and opt-in wheel e2e). No public runnable docstrings existed.
The three public names and their signatures/defaults remain unchanged. Wrong option types
now consistently raise TypeError; error messages do not echo values or type names.
Long combining runs previously copied a growing string repeatedly. A selector placeholder
could exceed the budget: `shorten("a/b/c/file", 1, sep="/", placeholder="\ufe0f")`
returned two-column text. Both defects have regression tests and fixes.

## Ground truth

All eleven URLs in `tests/sources/MANIFEST.txt` were fetched on 2026-11-01 and checked
against their SHA-256 and size. They include Microsoft path-format and Win32 API docs,
POSIX.1-2024 definitions and Unicode EastAsianWidth tables 13.0.0 through 17.0.0.
Copies remain outside the repository; the tests skip when absent and reject hash mismatches.
Microsoft path examples are parsed directly from the fetched pages. Expected anchors are
hand-derived from the documented grammar, not presented as upstream expected output.
The width convention beyond the fetched W/F properties is this library's stated policy.

The suite ran real `shlwapi.dll` PathCompactPathExW calls on Windows in this session,
including the fetched Microsoft example and four pinned differences. Standard-library
`ntpath` and `posixpath` are independent path-splitting oracles; a brute-force search
checks the segment-selection rule. Seeded hostile Unicode tests include custom selectors,
joiners, separators, controls, surrogates, 100,000-character clusters and 20,000 components.

Independent QA lenses and the independent review have not run for this release.

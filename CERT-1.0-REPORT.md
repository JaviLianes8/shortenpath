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
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG and strict render check (items 11, 12)
- [x] Packaging, e2e, every available Python (items 8, 10, 13, 14)
- [x] Gates (item 15)
- [x] PR #3 from `release/1.0.0` and trace guard CLEAN
- [x] QA round 1 fixes and regression checks (details below)
- [x] Independent reviewer (16) and all five QA lenses (19)
- [x] Release handoff (17); merge and publication remain separate owner actions

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
Copies remain outside the repository. Eight source tests were run with an absent source
folder and skipped cleanly; adding a newline to a copied source triggered its hash failure.
Microsoft path examples are parsed directly from the fetched pages. Expected anchors are
hand-derived from the documented grammar, not presented as upstream expected output.
The width convention beyond the fetched W/F properties is this library's stated policy.

The suite ran real `shlwapi.dll` PathCompactPathExW calls on Windows in this session,
including the fetched Microsoft example and four pinned differences. Standard-library
`ntpath` and `posixpath` are independent path-splitting oracles; a brute-force search
checks the segment-selection rule. Seeded hostile Unicode tests include custom selectors,
joiners, separators, controls, surrogates, 100,000-character clusters and 20,000 components.

All QA findings are fixed and independently rechecked. Final verdicts appear below.

## Independent reviewer scorecard

Review round 1: PASS at `8745294a81d288f3b860c0e2c5ff1f2a0935b258`, 2026-11-01.
Report: `../../scratch/shortenpath-cert/review-r1/REPORT.md` (relative to this checkout).
The following summarizes the review evidence. Item 17 passes the release handoff scope;
the reviewer explicitly leaves merge and publication pending with the owner.

| Item | Final result and evidence |
| --- | --- |
| 1 | PASS: three names, exact signatures/defaults pinned in `test_contract_api`; changes listed in CHANGELOG |
| 2 | PASS: exact `__all__` and public namespace checked; docs import only the public package |
| 3 | PASS: executable docstrings for all three exports, plus all README and GUIDE examples |
| 4 | PASS: `mypy --strict src tests`, runtime type-hint resolution and consumer inference/rejection tests; `py.typed` in the wheel |
| 5 | PASS: fixed TypeError/ValueError messages, hostile type names and large inputs covered; GUIDE error table |
| 6 | PASS: 304 tests cover public behavior, typing and CLI contracts; installed-consumer probes also pass |
| 7 | PASS: eleven fetched and hash-verified references, live Win32, stdlib and brute-force oracles |
| 8 | PASS: built wheel installed into disposable venvs, external API, console/module CLI, stdin and PyPI upgrade |
| 9 | PASS: fixed seeds for path oracles and Unicode properties, long-input tests and scaling measurements |
| 10 | PASS: complete suite on CPython 3.14.6, the only available supported interpreter; unavailable versions listed below |
| 11 | PASS: absolute README links, problem and verified alternatives, guide, changelog, exact badge, strict twine check |
| 12 | PASS: dated `1.0.0` CHANGELOG section, 2026-11-01 |
| 13 | PASS: version 1.0.0, Production/Stable, Python 3.10+, MIT, project URLs, keywords, no runtime dependencies |
| 14 | PASS: both archive member lists inspected; license and typing marker present, no fetched text or scratch files |
| 15 | PASS: all four gates exit 0 independently; strict typing also includes tests |
| 16 | PASS: fresh independent review executed the checklist; no outstanding findings |
| 17 | PASS (release handoff): PR #3 from `release/1.0.0` to `main`; merge and publication pending with the owner |
| 18 | PASS: 18 original mutations killed, four QA survivors fixed, and all 12 independent review mutations killed |
| 19 | PASS: all five QA lenses passed; current packaging and e2e rerun by the reviewer |

## Final QA verdicts

Report paths are relative to this checkout. All previous findings are closed.
Lens d retains its original reviewed commit; current packaging and e2e also pass review round 1.

| Lens | Rounds | Final verdict | Report path | Commit |
| --- | --- | --- | --- | --- |
| a: API and docs | 2 | PASS | `../../scratch/shortenpath-cert/lens-a-r2/REPORT.md` | `8745294a81d288f3b860c0e2c5ff1f2a0935b258` |
| b: Correctness and ground truth | 2 | PASS | `../../scratch/shortenpath-cert/lens-b-r2/REPORT.md` | `8745294a81d288f3b860c0e2c5ff1f2a0935b258` |
| c: Robustness | 2 | PASS | `../../scratch/shortenpath-cert/lens-c-r2/REPORT.md` | `8745294a81d288f3b860c0e2c5ff1f2a0935b258` |
| d: Packaging and e2e | 1 | PASS | `../../scratch/shortenpath-cert/lens-d-r1/REPORT.md` | `44b8c954ba2d3d495803dee1e62196a0101850e3` |
| e: Contract strength | 2 | PASS | `../../scratch/shortenpath-cert/lens-e-r2/REPORT.md` | `8745294a81d288f3b860c0e2c5ff1f2a0935b258` |

## Packaging baseline, upgrade and interpreters

Built with hatchling 1.33.0. The wheel built from the sdist has 13 files: eight package
files, metadata, entry points and the MIT license. The sdist has 38 files: source,
contract tests, source manifest, scripts, user docs, license and build metadata.
It excludes certification/improvement reports, downloaded third-party files and caches.
`python -m twine check --strict` passes for both artifacts.

The installed 0.2.0 modules match the main branch after newline normalization.
`test_upgrade` installs that actual PyPI release, records 3,000 seeded ordinary path
results across all three flavors, upgrades the same environment with the built wheel,
and checks identical results, the documented error-type changes, non-echoing messages,
selector overflow correction, installed CLI version and `pip check`.
The full sdist suite passed: 254 tests, no skips, in 28.94 seconds on CPython 3.14.6.
The extracted `src` directory was moved out of the import path and Python ran with `-I`
and pytest's `pythonpath` setting cleared. The imported library was in site-packages.
The external consumer asserts its import comes from site-packages. Console arguments,
module stdin, invalid-width status and a real closed stdout pipe are exercised.

Interpreter discovery used `py -0p`, PATH and standard installation locations.
CPython 3.14.6 is executable. The launcher's thirteen other entries point to missing
files: 3.10.19/22, 3.11.5/14/17, 3.12.12/15, 3.13.2/16 and 3.14.2/8 with their
free-threaded variants. Python 3.10, 3.11, 3.12, 3.13 and free-threaded Python could
not be run on this machine; they remain declared supported, not claimed tested here.

## Robustness

Seed 10002026 covers 20,000 Unicode cases; seeds 1 through 7 cover path and selection
oracles, and seeds 11 through 13 cover Win32 comparisons. All pass. Measurements up to
200,000 units support linear cluster assembly and O(n log n) selection, without guarantees.

## Mutation round

Each mutation changed one expression in a separate scratch copy of the library from
12794f6. Bytecode writing was disabled and no cached bytecode was copied. Its selected
contract test ran in a fresh process with pytest-timeout at 300 seconds and an outer
320-second limit, then the original source was restored. All 18 exited 1 with the
listed behavioral failure; no collection errors or equivalent mutants count as kills.

| ID | Deliberate bug | Contract that caught it (all killed) |
| --- | --- | --- |
| M01 | width zero accepted | `test_shorten.py::test_width_below_one_is_rejected` |
| M02 | bool width accepted | `test_shorten.py::test_width_must_be_an_int` |
| M03 | home folding forced | `test_home.py::test_home_tilde_off_leaves_home_alone` |
| M04 | joined width guard removed | `test_adversarial.py::test_a_selector_placeholder_cannot_overflow_the_final_budget` |
| M05 | tie keeps fewer head names | `test_shorten.py::test_most_segments_kept_then_most_at_the_head` |
| M06 | default placeholder changed | `test_contract_api.py::test_signatures_and_defaults_are_stable` |
| M07 | wide characters one column | `test_width.py::test_display_width` |
| M08 | combining marks consume width | `test_width.py::test_display_width` |
| M09 | soft hyphen invisible | `test_width.py::test_display_width` |
| M10 | final cluster dropped | `test_width.py::test_display_width` |
| M11 | selector fails to widen | `test_width.py::test_emoji_presentation_selector_makes_two_columns` |
| M12 | Windows drive comparison case sensitive | `test_home.py::test_windows_comparison_ignores_case_and_separator_kind` |
| M13 | relative home folds | `test_home.py::test_a_relative_home_never_folds` |
| M14 | extension ignored | `test_shorten.py::test_last_name_is_cut_keeping_start_and_extension` |
| M15 | wrong separator error type | `test_contract_api.py::test_errors_have_fixed_types_and_safe_messages` |
| M16 | CLI does not stream | `test_cli.py::test_stdin_lines_are_written_as_they_arrive` |
| M17 | CLI echoes invalid options | `test_adversarial.py::test_cli_errors_do_not_quote_secrets_or_huge_values` |
| M18 | closed stdout flushed at shutdown | `test_cli_pipe.py::test_closed_stdout_pipe_exits_successfully_without_stderr` |

## Preparation gates

On 2026-11-01, each command exited 0 on its own:
`ruff format --check .` (31 files), `ruff check .`, `mypy --strict src` (7 modules),
`mypy --strict src tests` (24 files), and `pytest` (254 passed, no skips, 34.74 seconds).
The pytest run enabled both wheel e2e and the real PyPI upgrade, with the fetched sources,
pytest-timeout at 300 seconds and an explicit scratch basetemp. The source and installed
suites were green after the mutation round. These preparation runs used source from 12794f6.

Artifact SHA-256 values (the certification report is excluded from both archives):
- Wheel: `65f6ab61b40fbf889d2f82f4407263c148a760cf6d8224dd65fcaf107e726a6e`
- Sdist: `f4673f9ff6a6e5682e4b2955c64f394d7d174d55a254d2f38a04081c16c05482`

The release script passes syntax parsing; its upload path was not invoked.
PR: https://github.com/JaviLianes8/shortenpath/pull/3, with trace guard CLEAN on 2026-11-01.

## QA lenses, round 1

Reviewed head: `44b8c954ba2d3d495803dee1e62196a0101850e3`, 2026-11-01.
Fix commit: `28100f2632270af0bd4c547814f48cd1d4218565`.
All eleven findings are addressed; none are disputed. The final QA table records their
independent rechecks. Lens d passed with no findings on the original reviewed head.

| Finding | Change and verification |
| --- | --- |
| A-001 | README, metadata and `shorten` docstring qualify preservation by budget; runnable small-budget example passes |
| A-002 | `display_width` docstring names soft hyphen and demonstrates its one-column width |
| B-001 | Presentation selectors adjust each joined component; all 1,468 freshly fetched Emoji 16 ZWJ sequences pass width and budget checks |
| B-002 | Windows home folding requires a volume and root; both slash spellings and qualified-home controls pass |
| C-001 | Linear prefix-link literal matcher replaces repeated regex searches; 3,000 seeded reference comparisons and near-match scaling pass |
| C-002 | Strict stdin decoding failures emit a fixed diagnostic and exit 2; subprocess and installed-console checks pass |
| C-003 | Built-in subclass values are normalized without overridden methods; validation and budget regressions cover all text arguments and path-provider results |
| E-01 | RuntimeError/OSError identity is pinned for path and home providers; lens e mutation M10 is killed |
| E-02 | Windows custom-separator homes have case-sensitive positive/negative controls; lens e mutation M35 is killed |
| E-03 | Inclusive Hangul ranges retain zero width at unassigned positions; public boundary tests kill lens e mutation M44 |
| E-04 | Exact stdin spaces and tabs, whitespace-only paths and both line endings are pinned; lens e mutation M52 is killed |

Behavior regressions were added before implementation changes. Against the reviewed source,
the final public regression cases produce 24 failures and 19 passes; the separate scaling
contract also fails. All four mutation baselines pass and all four mutants fail assertions.
Median near-match timings at 8,000/16,000/32,000/64,000 characters changed from
0.1249/0.4865/2.1934/7.7168 seconds to 0.0768/0.1482/0.2316/0.4379 seconds.
Timing evidence and reproduction scripts are outside the repository in `shortenpath-cert/fix-r1/`.
On CPython 3.14.6, `ruff format --check .`, `ruff check .`, `mypy --strict src` and
`mypy --strict src tests` exit 0. Pytest: 304 passed, no skips, with a 300-second timeout,
scratch basetemp, verified sources, installed wheel and PyPI 0.2.0 upgrade enabled.
Strict wheel/sdist description checks also pass. Interpreter availability is unchanged.

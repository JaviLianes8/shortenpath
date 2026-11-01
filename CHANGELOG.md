# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-01

### Stable

- `shorten`, `display_width` and the `Flavor` literal alias, with the same signatures,
  defaults and path-selection rules as 0.2.0. Python 3.10 and newer are supported.
- The `shortenpath` command and `python -m shortenpath`, including streaming stdin,
  terminal-width defaults and exit status 2 for invalid arguments.

### Changed

- Invalid argument errors no longer include input values or type names. CLI usage errors
  retain a fixed explanation for bad widths and empty options; other usage errors ask for
  `--help` without quoting the command line.
- Non-string `sep`, `placeholder` and `flavor` now raise `TypeError` instead of `ValueError`.
  Non-boolean `home_tilde` now raises `TypeError` instead of accepting truthy values.
  `home` remains ignored when home folding is disabled.
- Invalid `__fspath__` results and `TypeError` raised by `__fspath__` receive a fixed
  `TypeError` message. Other exceptions raised by user-supplied path objects still propagate.
- Closed-pipe handling disables the failed stdout stream instead of opening a null device.
  Its successful exit status is unchanged.

### Fixed

- Long combining-mark and zero-width-joiner runs are assembled in linear time instead
  of repeatedly copying the growing cluster.
- Emoji selectors at joined piece boundaries can no longer exceed the requested width:
  a final cluster-aligned prefix cut is applied when the joined result would overflow.
- The release script checks whether the version exists, allowing upgrades to an existing
  project. It requires a clean checkout, runs the gate and uses a fresh output directory.

### Added

- Runnable public docstrings, the GUIDE, verified source hashes, stronger contract and
  property tests, installed-wheel upgrade checks and explicit source-distribution contents.

## [0.2.0]

### Added

- `flavor` (`"posix"`, `"windows"`, `"native"`) and the `Flavor` type. Windows paths keep
  their drive, UNC share or device prefix (`\\.\`, `\\?\`, `\\?\UNC\`, `\\.\UNC\`) whole and
  take both `\` and `/` as separators, except after an exact `\\?\`.
- `display_width(text)`: terminal columns, with East Asian wide and fullwidth characters as
  two, combining marks as none and a character with the emoji presentation selector as two.
  The budget of `shorten` is now in columns.
- Command line tool `shortenpath` (also `python -m shortenpath`), streaming paths read from
  standard input line by line.
- `os.PathLike` paths and homes.

### Changed

- The second argument is now `width`, in terminal columns.
- Elision keeps the most whole names around the placeholder, then the most at the start,
  and keeps the whole last name before the anchor when only one of them fits, also for a
  path with a single name.
- A name that cannot fit is cut in the middle, keeping its start and its extension, and
  never between a letter and its combining marks.
- Separator runs are kept as written.
- `sep` is now optional and, when given, replaces the flavor's rules; the default home is
  only used for paths of the running system.
- The home folder folds only on whole names, never when it is relative or a bare root or
  drive, and without regard to case or separator kind on Windows.

### Fixed

- A UNC share or device prefix was cut into a lone separator.
- Wrong argument types failed deep inside; they now raise `TypeError`, and an empty
  `placeholder` raises `ValueError`.

## [0.1.0]

- First release: `shorten` collapses the home directory to `~` and middle-elides a
  path to fit a width budget, with a basename-truncation fallback and a configurable
  separator, home and placeholder.

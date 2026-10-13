# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

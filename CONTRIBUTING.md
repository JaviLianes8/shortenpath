# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/shortenpath/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Tests inject time, disk and network; they
  never touch the real thing.
- Run `python scripts/fetch_sources.py` once so the tests can check the rules against the
  Microsoft, POSIX and Unicode texts, then `scripts/check.ps1` (format, lint, types, tests)
  and make sure it passes. `SHORTENPATH_E2E=1` adds the installed-wheel test.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.

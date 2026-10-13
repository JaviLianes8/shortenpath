"""Run the command line tool with ``python -m shortenpath``."""

from __future__ import annotations

import sys

from shortenpath._cli import main

if __name__ == "__main__":
    sys.exit(main())

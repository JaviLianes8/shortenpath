"""Command line tool: shorten paths given as arguments or read one per line from stdin."""

from __future__ import annotations

import argparse
import errno
import io
import os
import shutil
import sys
from collections.abc import Sequence

from ._shorten import shorten


def _width(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"width must be a whole number, not {text!r}") from None
    if value < 1:
        raise argparse.ArgumentTypeError(f"width must be at least 1, not {value}")
    return value


def _parser() -> argparse.ArgumentParser:
    from . import __version__

    parser = argparse.ArgumentParser(
        prog="shortenpath",
        description="Shorten paths to fit a number of terminal columns, one per line. "
        "Without PATH arguments, paths are read one per line from standard input.",
        epilog="examples:\n  shortenpath -w 30 /usr/local/share/doc/python3/README.md\n"
        '  pwd | shortenpath -w 24\n  shortenpath -w 20 -- "-odd name"',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="*", metavar="PATH", help="paths to shorten")
    parser.add_argument(
        "-w",
        "--width",
        type=_width,
        metavar="COLS",
        help="column budget (default: the terminal width)",
    )
    parser.add_argument(
        "-f",
        "--flavor",
        choices=("native", "posix", "windows"),
        default="native",
        help="path rules (default: those of this system)",
    )
    parser.add_argument("--no-tilde", action="store_true", help="do not fold the home folder")
    parser.add_argument("--home", help="home folder to fold to ~ (default: the current user's)")
    parser.add_argument("--sep", help="a custom separator instead of the flavor's rules")
    parser.add_argument("--placeholder", default="...", help="text put where segments go")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _inputs(paths: list[str]) -> list[str]:
    if paths:
        return paths
    return [line.rstrip("\r\n") for line in sys.stdin]


def _write(lines: list[str]) -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        # A pipe on Windows may use a legacy code page; a name it cannot hold must not crash.
        sys.stdout.reconfigure(errors="replace")
    try:
        sys.stdout.write("".join(line + "\n" for line in lines))
        sys.stdout.flush()
    except OSError as error:
        # The reader went away (``| head``). Windows reports EINVAL rather than EPIPE.
        if not isinstance(error, BrokenPipeError) and error.errno != errno.EINVAL:
            raise
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for ``shortenpath`` and ``python -m shortenpath``; returns the exit code."""
    parser = _parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else list(argv))
    width = args.width if args.width is not None else shutil.get_terminal_size().columns
    try:
        lines = [
            shorten(
                path,
                width,
                flavor=args.flavor,
                home_tilde=not args.no_tilde,
                home=args.home,
                sep=args.sep,
                placeholder=args.placeholder,
            )
            for path in _inputs(args.paths)
        ]
    except ValueError as error:
        parser.error(str(error))
    _write(lines)
    return 0

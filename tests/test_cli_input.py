"""Subprocess contracts for stdin decoding and significant path whitespace."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


def _run(stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-m", "shortenpath", "-w", "80", "-f", "posix", "--no-tilde"],
        input=stdin,
        capture_output=True,
        env={
            **os.environ,
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
            "PYTHONIOENCODING": "utf-8:strict",
        },
        timeout=30,
    )


@pytest.mark.parametrize("payload", [b"\xff\n", b"valid\n\xf0\x28\x8c\x28\n"])
def test_malformed_stdin_exits_two_with_a_fixed_diagnostic(payload: bytes) -> None:
    result = _run(payload)
    assert result.returncode == 2
    assert result.stderr.replace(b"\r\n", b"\n") == b"shortenpath: cannot decode standard input\n"


@pytest.mark.parametrize("ending", [b"\n", b"\r\n"])
def test_stdin_preserves_spaces_and_tabs_including_whitespace_only_paths(ending: bytes) -> None:
    lines = [b"  /a/file \t", b" \t  ", b"\t/a/file  ", b""]
    payload = ending.join(lines) + ending
    result = _run(payload)
    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout.replace(b"\r\n", b"\n") == b"\n".join(lines) + b"\n"

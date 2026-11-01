"""A real pipe closing must leave no shutdown traceback or status 120."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_closed_stdout_pipe_exits_successfully_without_stderr() -> None:
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    process = subprocess.Popen(
        [sys.executable, "-m", "shortenpath", "-w", "10", "x" * 1000],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert process.stdout is not None and process.stderr is not None
    process.stdout.close()
    try:
        assert process.wait(timeout=30) == 0
        assert process.stderr.read() == b""
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        process.stderr.close()

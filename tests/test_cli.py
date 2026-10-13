"""The command line tool, driven in process and once as a real subprocess."""

from __future__ import annotations

import errno
import io
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from shortenpath._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> list[str]:
    assert main(list(argv)) == 0
    return capsys.readouterr().out.splitlines()


def _fails(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    with pytest.raises(SystemExit) as stop:
        main(list(argv))
    assert stop.value.code == 2
    return capsys.readouterr().err


def test_paths_are_shortened_in_order(capsys: pytest.CaptureFixture[str]) -> None:
    out = _run(capsys, "-w", "11", "-f", "posix", "/a/b/c/d/e/file", "/x", "/a/b/c/d/e/g")
    assert out == ["/a/.../file", "/x", "/a/b/.../g"]


def test_options_may_follow_paths(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(capsys, "/a/b/c/d/e/file", "--width", "11", "--flavor", "posix") == ["/a/.../file"]


def test_windows_flavor(capsys: pytest.CaptureFixture[str]) -> None:
    out = _run(capsys, "-w", "12", "-f", "windows", "C:/a/b/c/d/file.txt")
    assert out == [".../file.txt"]


def test_home_and_no_tilde(capsys: pytest.CaptureFixture[str]) -> None:
    args = ("-w", "40", "-f", "posix", "--home", "/home/javi", "/home/javi/x")
    assert _run(capsys, *args) == ["~/x"]
    assert _run(capsys, *args, "--no-tilde") == ["/home/javi/x"]


def test_custom_separator_and_placeholder(capsys: pytest.CaptureFixture[str]) -> None:
    out = _run(capsys, "-w", "8", "--sep", "::", "--placeholder", "~~", "a::b::c::d::e")
    assert out == ["a::~~::e"]


def test_paths_come_from_stdin_without_arguments(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("/a/b/c/d/e/file\r\n/x\n\n"))
    assert _run(capsys, "-w", "11", "-f", "posix") == ["/a/.../file", "/x", ""]


def test_width_defaults_to_the_terminal(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("shutil.get_terminal_size", lambda: os.terminal_size((11, 24)))
    assert _run(capsys, "-f", "posix", "/a/b/c/d/e/file") == ["/a/.../file"]


def test_a_dash_led_path_after_double_dash(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(capsys, "-w", "20", "--", "-odd name") == ["-odd name"]


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["-w", "0", "x"], "width must be at least 1, not 0"),
        (["-w", "-3", "x"], "width must be at least 1, not -3"),
        (["-w", "wide", "x"], "width must be a whole number, not 'wide'"),
        (["-f", "mac", "x"], "invalid choice: 'mac'"),
        (["-w", "5", "--sep", "", "x"], "sep must be a non-empty string"),
        (["-w", "5", "--placeholder", "", "x"], "placeholder must be a non-empty string"),
    ],
)
def test_bad_input_exits_two(
    capsys: pytest.CaptureFixture[str], argv: list[str], message: str
) -> None:
    assert message in _fails(capsys, *argv)


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    from shortenpath import __version__

    with pytest.raises(SystemExit) as stop:
        main(["--version"])
    assert stop.value.code == 0
    assert capsys.readouterr().out.strip() == f"shortenpath {__version__}"


def test_a_closed_pipe_is_quiet(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class Closed(io.StringIO):
        def __init__(self, error: OSError, sink: int) -> None:
            super().__init__()
            self.error, self.sink = error, sink

        def write(self, text: str) -> int:
            raise self.error

        def fileno(self) -> int:
            return self.sink

    for error in (BrokenPipeError(), OSError(errno.EINVAL, "Invalid argument")):
        with (tmp_path / "sink").open("w") as sink:
            monkeypatch.setattr(sys, "stdout", Closed(error, sink.fileno()))
            assert main(["-w", "9", "/a"]) == 0


def test_other_write_errors_are_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    class Full(io.StringIO):
        def write(self, text: str) -> int:
            raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(sys, "stdout", Full())
    with pytest.raises(OSError, match="No space"):
        main(["-w", "9", "/a"])


def test_python_dash_m_runs_the_tool() -> None:
    env = {**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "cp1252"}
    result = subprocess.run(
        [sys.executable, "-m", "shortenpath", "-w", "12", "-f", "posix", "/a/b/c/\u65e5\u672c.txt"],
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    # A legacy code page cannot hold the name; it is replaced instead of crashing.
    assert result.stdout.decode("cp1252").split() == [".../??.txt"]


def test_stdin_lines_are_written_as_they_arrive(monkeypatch: pytest.MonkeyPatch) -> None:
    out = io.StringIO()
    seen: list[str] = []

    def lines() -> Iterator[str]:
        yield "/a/b/c/d/e/file\n"
        seen.append(out.getvalue())
        yield "/x\n"

    class Stdin:
        def __iter__(self) -> Iterator[str]:
            return lines()

    monkeypatch.setattr(sys, "stdin", Stdin())
    monkeypatch.setattr(sys, "stdout", out)
    assert main(["-w", "11", "-f", "posix"]) == 0
    assert seen == ["/a/.../file\n"]
    assert out.getvalue() == "/a/.../file\n/x\n"


def test_bad_options_fail_before_reading_stdin(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    class Stdin:
        def __iter__(self) -> Iterator[str]:
            raise AssertionError("stdin was read")

    monkeypatch.setattr(sys, "stdin", Stdin())
    assert "placeholder must be" in _fails(capsys, "-w", "5", "--placeholder", "")

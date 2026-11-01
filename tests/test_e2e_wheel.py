"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with SHORTENPATH_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("SHORTENPATH_E2E") != "1", reason="set SHORTENPATH_E2E=1 to build"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources, pathlib
import shortenpath as s

assert "site-packages" in s.__file__, s.__file__
assert importlib.metadata.version("shortenpath") == s.__version__
assert importlib.resources.files("shortenpath").joinpath("py.typed").is_file()
assert sorted(s.__all__) == ["Flavor", "display_width", "shorten"]

assert s.shorten("/a/b/c/d/e/file", 11, flavor="posix") == "/a/.../file"
assert s.shorten("/home/u/x/y", 40, flavor="posix", home="/home/u") == "~/x/y"
unc = "\\\\srv\\share\\a\\b\\c\\f.txt"
assert s.shorten(unc, 22, flavor="windows") == "\\\\srv\\share\\...\\f.txt"
assert s.shorten(pathlib.PurePosixPath("/a/verylongname.py"), 10, flavor="posix") == "ver...e.py"
assert s.display_width("\u65e5\u672ca\u0301") == 5
emoji = "\U0001f441\ufe0f\u200d\U0001f5e8\ufe0f"
assert s.display_width(emoji) == 4
assert s.shorten(emoji, 3, home_tilde=False) == ""
assert s.shorten('/Users/u/file', 80, flavor='windows', home='/Users/u') == '/Users/u/file'
class Width(int):
    def __lt__(self, other):
        return False
assert s.shorten('abcdef', Width(1), home_tilde=False) == 'a'
for bad, error in ((b"/a", TypeError), (0, TypeError)):
    try:
        s.shorten(bad, 5)
    except error:
        pass
    else:
        raise AssertionError(bad)
try:
    s.shorten("/a", 0)
except ValueError:
    pass
else:
    raise AssertionError("width 0")
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None, stdin: bytes = b"") -> bytes:
    result = subprocess.run(
        [str(c) for c in cmd], cwd=cwd, input=stdin, capture_output=True, check=False, timeout=240
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


def test_installed_wheel_end_to_end(tmp_path: Path, artifacts: tuple[Path, Path]) -> None:
    wheel, sdist = artifacts
    names = zipfile.ZipFile(wheel).namelist()
    assert not [name for name in names if "sources" in name or name.startswith("tests/")]
    assert {"shortenpath/py.typed", "shortenpath/__main__.py", "shortenpath/_cli.py"} <= set(names)
    assert any(name.endswith(".dist-info/licenses/LICENSE") for name in names)
    assert all(name.startswith(("shortenpath/", "shortenpath-1.0.0.dist-info/")) for name in names)

    with tarfile.open(sdist) as archive:
        members = archive.getnames()
    data = [name for name in members if "/tests/sources/" in name]
    assert data == [name for name in data if name.endswith("/MANIFEST.txt")]
    assert "shortenpath-1.0.0/LICENSE" in members
    assert not any(
        "__pycache__" in name or "CERT-" in name or "IMPROVEMENTS" in name for name in members
    )

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    _run(python, "-m", "pip", "install", "-q", wheel)

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    assert _run(python, "-I", "-c", PROGRAM, cwd=work).decode().splitlines() == ["e2e ok"]

    script = bindir / ("shortenpath.exe" if sys.platform == "win32" else "shortenpath")
    out = _run(script, "-w", "11", "-f", "posix", "/a/b/c/d/e/file", "/x", cwd=work)
    assert out.decode().split() == ["/a/.../file", "/x"]
    out = _run(
        python,
        "-I",
        "-m",
        "shortenpath",
        "-w",
        "11",
        "-f",
        "posix",
        cwd=work,
        stdin=b"/a/b/c/d/e/g\n  /a/file \t\n \t \n",
    )
    assert out.decode().splitlines() == ["/a/b/.../g", "  /a/file \t", " \t "]
    bad = subprocess.run(
        [str(script), "-w", "0", "x"], cwd=work, capture_output=True, check=False, timeout=30
    )
    assert bad.returncode == 2
    assert b"width must be at least 1" in bad.stderr
    malformed = subprocess.run(
        [str(script), "-w", "20", "--no-tilde"],
        cwd=work,
        input=b"\xff\n",
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8:strict"},
        timeout=30,
    )
    assert malformed.returncode == 2
    assert malformed.stderr.replace(b"\r\n", b"\n") == (
        b"shortenpath: cannot decode standard input\n"
    )

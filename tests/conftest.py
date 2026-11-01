"""Shared built artifacts for installed-package tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from test_e2e_wheel import ROOT, _run


@pytest.fixture(scope="module")
def artifacts(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    supplied = os.environ.get("SHORTENPATH_WHEEL")
    if supplied:
        return Path(supplied), Path(os.environ["SHORTENPATH_SDIST"])
    tmp_path = tmp_path_factory.mktemp("artifacts")
    dist = tmp_path / "dist"
    _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    (wheel,) = dist.glob("shortenpath-*.whl")
    _run(sys.executable, "-m", "build", "--sdist", "--outdir", dist, ROOT)
    (sdist,) = dist.glob("shortenpath-*.tar.gz")
    return wheel, sdist

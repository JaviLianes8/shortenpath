"""The published 0.2.0 wheel upgrades in place with documented differences only."""

from __future__ import annotations

import json
import os
import sys
import venv
from pathlib import Path

import pytest
from test_e2e_wheel import _run

pytestmark = pytest.mark.skipif(
    os.environ.get("SHORTENPATH_E2E") != "1" or os.environ.get("SHORTENPATH_PYPI") != "1",
    reason="set SHORTENPATH_E2E=1 and SHORTENPATH_PYPI=1 to test the published upgrade",
)

SNAPSHOT = r"""
import json, random
import shortenpath as s
rng = random.Random(1000)
outputs = []
for flavor in ('posix', 'windows', 'native'):
    for _ in range(1000):
        names = [''.join(rng.choices('abc.\u65e5\u0301', k=rng.randrange(1,10)))
                 for _ in range(rng.randrange(1,10))]
        path = rng.choice(['/', 'C:\\', '\\\\srv\\share\\', '']) + '/'.join(names)
        outputs.append(s.shorten(path, rng.randrange(1,40), flavor=flavor, home_tilde=False))
errors = []
for options in ({'sep': 2}, {'placeholder': None}, {'flavor': 3}, {'home_tilde': 1}):
    try:
        s.shorten('/a', 20, **options)
    except Exception as error:
        errors.append(type(error).__name__)
    else:
        errors.append('accepted')
try:
    s.shorten('/a', 20, flavor='private-value')
except ValueError as error:
    message = str(error)
out = s.shorten('a/b/c/file', 1, sep='/', placeholder='\ufe0f')
print(json.dumps({'version':s.__version__, 'outputs':outputs, 'errors':errors,
                  'message':message, 'selector':s.display_width(out)}))
"""


def test_upgrade_from_pypi_keeps_outputs_and_changes_only_documented_errors(
    tmp_path: Path, artifacts: tuple[Path, Path]
) -> None:
    wheel, _ = artifacts
    env = tmp_path / "upgrade"
    venv.create(env, with_pip=True)
    scripts = env / ("Scripts" if sys.platform == "win32" else "bin")
    python = scripts / "python"
    _run(python, "-m", "pip", "install", "shortenpath==0.2.0")
    before = json.loads(_run(python, "-I", "-c", SNAPSHOT, cwd=tmp_path))
    assert before["version"] == "0.2.0"
    assert before["errors"] == ["ValueError", "ValueError", "ValueError", "accepted"]
    assert "private-value" in before["message"]
    assert before["selector"] == 2
    _run(python, "-m", "pip", "install", "--upgrade", wheel)
    after = json.loads(_run(python, "-I", "-c", SNAPSHOT, cwd=tmp_path))
    assert after["version"] == "1.0.0"
    assert after["outputs"] == before["outputs"]
    assert after["errors"] == ["TypeError"] * 4
    assert "private-value" not in after["message"]
    assert after["selector"] == 0
    assert b"No broken requirements" in _run(python, "-m", "pip", "check")
    script = scripts / ("shortenpath.exe" if sys.platform == "win32" else "shortenpath")
    assert _run(script, "--version", cwd=tmp_path).strip() == b"shortenpath 1.0.0"

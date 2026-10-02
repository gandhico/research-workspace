from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]


def test_julia_policy_smoke_matches_python_pd():
    if shutil.which("julia") is None:
        pytest.skip("Julia executable is not available")
    result = subprocess.run(
        [sys.executable, "runners/run_julia_policy_smoke.py"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
        timeout=45,
    )
    assert "python_u=" in result.stdout
    assert "julia_u=" in result.stdout
    assert "max_abs_diff=" in result.stdout

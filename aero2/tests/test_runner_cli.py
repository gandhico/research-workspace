"""Direct runner smoke tests.

The desktop app launches ``runners/run_control.py`` as a subprocess from the
project root. This test protects that app-compatible path and verifies the
runner works even before the package is installed editable.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aero2.config import capabilities


REPO = Path(__file__).resolve().parents[1]


def _julia_bridge_available() -> bool:
    return shutil.which("julia") is not None and importlib.util.find_spec("juliacall") is not None


def _run_control(*args: str):
    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "runners" / "run_control.py"),
            *args,
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    return result


def _run_benchmark(*args: str):
    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "runners" / "run_benchmark.py"),
            *args,
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    return result


def test_run_control_direct_script_offline_smoke():
    result = _run_control(
        "--model",
        "helicopter_2dof",
        "--mode",
        "offline",
        "--controller",
        "pd",
        "--application",
        "reference_tracking",
        "--duration",
        "0.2",
        "--hz",
        "200",
        "--dt",
        "0.005",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[helicopter_2dof | offline | pd | reference_tracking]" in result.stdout
    assert "mode=offline: implemented" in result.stdout
    assert "realized=200.0 Hz" in result.stdout


@pytest.mark.parametrize("controller", sorted(capabilities.CONTROLLERS))
def test_run_control_direct_script_primary_model_all_offline_controllers(controller):
    if controller == "julia_policy" and not _julia_bridge_available():
        pytest.skip("Julia bridge dependencies are not available")

    result = _run_control(
        "--model",
        "helicopter_2dof",
        "--mode",
        "offline",
        "--controller",
        controller,
        "--application",
        "reference_tracking",
        "--duration",
        "0.2",
        "--hz",
        "200",
        "--dt",
        "0.005",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"[helicopter_2dof | offline | {controller} | reference_tracking]" in result.stdout
    assert f"controller={controller}:" in result.stdout
    assert "realized=200.0 Hz" in result.stdout


def test_run_control_direct_script_julia_policy_offline_smoke():
    if not _julia_bridge_available():
        pytest.skip("Julia bridge dependencies are not available")

    result = _run_control(
        "--model",
        "helicopter_2dof",
        "--mode",
        "offline",
        "--controller",
        "julia_policy",
        "--application",
        "pitch_reference_tracking",
        "--duration",
        "0.2",
        "--hz",
        "200",
        "--dt",
        "0.005",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[helicopter_2dof | offline | julia_policy | pitch_reference_tracking]" in result.stdout
    assert "controller=julia_policy: julia_bridge_offline_validated" in result.stdout
    assert "realized=200.0 Hz" in result.stdout


@pytest.mark.parametrize("model", sorted(capabilities.MODELS))
def test_run_control_direct_script_all_offline_models_pd(model):
    result = _run_control(
        "--model",
        model,
        "--mode",
        "offline",
        "--controller",
        "pd",
        "--application",
        "reference_tracking",
        "--duration",
        "0.2",
        "--hz",
        "200",
        "--dt",
        "0.005",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"[{model} | offline | pd | reference_tracking]" in result.stdout
    assert f"model={model}:" in result.stdout
    assert "realized=200.0 Hz" in result.stdout


def test_run_benchmark_direct_script_saves_summary(tmp_path):
    result = _run_benchmark(
        "--model",
        "helicopter_2dof",
        "--duration",
        "0.2",
        "--dt",
        "0.005",
        "--save",
        "--out",
        str(tmp_path),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Offline benchmark | helicopter_2dof" in result.stdout
    assert "Saved CSV:" in result.stdout
    assert "Saved JSON:" in result.stdout
    assert list(tmp_path.glob("benchmark_helicopter_2dof_offline_*.csv"))
    assert list(tmp_path.glob("benchmark_helicopter_2dof_offline_*.json"))


@pytest.mark.parametrize("application", sorted(capabilities.APPLICATIONS))
def test_run_control_direct_script_all_applications_pd(application):
    result = _run_control(
        "--model",
        "helicopter_2dof",
        "--mode",
        "offline",
        "--controller",
        "pd",
        "--application",
        application,
        "--duration",
        "0.2",
        "--hz",
        "200",
        "--dt",
        "0.005",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"[helicopter_2dof | offline | pd | {application}]" in result.stdout
    assert f"application={application}:" in result.stdout

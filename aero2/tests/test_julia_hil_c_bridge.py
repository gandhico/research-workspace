from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]


def test_julia_hil_c_bridge_loads_and_discovers_library():
    if shutil.which("julia") is None:
        pytest.skip("Julia executable is not available")

    result = subprocess.run(
        [
            "julia",
            "--startup-file=no",
            "-e",
            (
                'include("julia/Aero2HilCBridge.jl"); '
                "using .Aero2HilCBridge; "
                'lib = Aero2HilCBridge.find_hil_library(); '
                'println(lib === nothing ? "hil_found=false" : "hil_found=true")'
            ),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
        timeout=45,
    )
    assert "hil_found=true" in result.stdout


def test_julia_hil_c_bridge_sensor_conversion_helpers():
    if shutil.which("julia") is None:
        pytest.skip("Julia executable is not available")

    result = subprocess.run(
        [
            "julia",
            "--startup-file=no",
            "-e",
            (
                'include("julia/Aero2HilCBridge.jl"); '
                "using .Aero2HilCBridge; "
                "raw=(analog=Float64[1.0, 2.0], "
                "encoders=Int32[0, 0, 1440, 2048], "
                "other=Float64[0.0, 0.1, -0.2, 0.0, 0.0, 9.8, 0.0, 0.0, 2880.0, 4096.0]); "
                "sample=Aero2HilCBridge.aero2_sensor_sample(raw); "
                'println(sample.theta); println(sample.psi); println(sample.pitch_rate); println(sample.yaw_rate)'
            ),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
        timeout=45,
    )
    values = [float(line) for line in result.stdout.strip().splitlines()]
    assert values == pytest.approx([3.141592653589793, 3.141592653589793, 6.283185307179586, 6.283185307179586])


def test_julia_hil_sensor_check_defaults_to_no_connect():
    if shutil.which("julia") is None:
        pytest.skip("Julia executable is not available")

    result = subprocess.run(
        [
            "julia",
            "--startup-file=no",
            "julia/aero2_hil_sensor_check.jl",
            "--duration",
            "0.01",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
        timeout=45,
    )
    assert "connect=false" in result.stdout
    assert "target=virtual" in result.stdout
    assert "card_identifier=0@tcpip://localhost:18950" in result.stdout
    assert "status=not_connected" in result.stdout

"""Offline closed-loop smoke for bridge 1: Python runner, Julia policy."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from aero2.applications import make_application
from aero2.benchmarking.metrics import tracking_metrics
from aero2.control import JuliaPolicyController
from aero2.execution.offline import OfflineBackend
from aero2.io import make_estimator
from aero2.models import make_model


def _run_julia(args: list[str], timeout: float) -> str:
    result = subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=True, timeout=timeout)
    return result.stdout.strip()


def resolve_julia_exe(julia_cmd: str, timeout: float) -> str:
    env_exe = os.environ.get("PYTHON_JULIACALL_EXE")
    if env_exe:
        return env_exe
    bindir = _run_julia([julia_cmd, "--startup-file=no", "-e", "print(Sys.BINDIR)"], timeout)
    exe = Path(bindir) / ("julia.exe" if os.name == "nt" else "julia")
    return str(exe)


def resolve_julia_project(julia_cmd: str, timeout: float) -> str:
    env_project = os.environ.get("PYTHON_JULIACALL_PROJECT")
    if env_project:
        return env_project
    active_project = _run_julia([julia_cmd, "--startup-file=no", "-e", "print(Base.active_project())"], timeout)
    return str(Path(active_project).parent)


def configure_juliacall(args) -> tuple[str, str]:
    julia_cmd = args.julia
    if shutil.which(julia_cmd) is None and not Path(julia_cmd).exists():
        raise RuntimeError(f"Julia executable not found: {julia_cmd!r}")
    julia_exe = args.julia_exe or resolve_julia_exe(julia_cmd, args.timeout)
    julia_project = args.julia_project or resolve_julia_project(julia_cmd, args.timeout)
    os.environ.setdefault("PYTHON_JULIACALL_EXE", julia_exe)
    os.environ.setdefault("PYTHON_JULIACALL_PROJECT", julia_project)
    return julia_exe, julia_project


def run_closed_loop(args) -> tuple[object, dict, dict]:
    model = make_model(args.model)
    backend = OfflineBackend(model, dt=float(args.dt), seed=args.seed)
    controller = JuliaPolicyController(
        module_path=REPO / "julia" / "aero2_policy_smoke.jl",
        function_name="Aero2PolicySmoke.pd_policy",
        voltage_limit=float(args.voltage_limit),
    )
    app = make_application(
        args.application,
        duration_s=float(args.duration),
        nominal_hz=float(args.hz),
    )
    estimator = make_estimator("passthrough")
    rec = app.run(backend, controller, estimator)
    metrics = tracking_metrics(rec)
    cfg = {
        "model_variant": args.model,
        "execution_mode": "offline",
        "controller": "julia_policy",
        "application": args.application,
        "duration_s": args.duration,
        "hz": args.hz,
        "dt": args.dt,
        "voltage_limit": args.voltage_limit,
        "seed": args.seed,
    }
    return rec, metrics, cfg


def save_record(rec, metrics: dict, cfg: dict) -> Path:
    out_dir = REPO / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = f"{cfg['model_variant']}_{cfg['execution_mode']}_{cfg['controller']}_{cfg['application']}_{stamp}"
    np.savez(
        out_dir / f"{tag}.npz",
        t=np.asarray(rec.t),
        x_est=np.asarray(rec.x_est),
        u=np.asarray(rec.u),
        ref=np.asarray(rec.ref),
        dt=np.asarray(rec.dt),
    )
    json_path = out_dir / f"{tag}.json"
    import json

    json_path.write_text(json.dumps({"config": cfg, "metrics": metrics}, indent=2))
    return json_path


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Run an offline Aero2 closed-loop smoke with a Julia policy controller.")
    p.add_argument("--model", default="helicopter_2dof")
    p.add_argument("--application", default="pitch_reference_tracking")
    p.add_argument("--duration", type=float, default=2.0)
    p.add_argument("--hz", type=float, default=200.0)
    p.add_argument("--dt", type=float, default=0.005)
    p.add_argument("--voltage-limit", type=float, default=24.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--julia", default="julia")
    p.add_argument("--julia-exe")
    p.add_argument("--julia-project")
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--save", action="store_true")
    args = p.parse_args(argv)

    julia_exe, julia_project = configure_juliacall(args)
    rec, metrics, cfg = run_closed_loop(args)

    print("[Aero2 Julia bridge offline smoke]")
    print(f"  julia_exe={julia_exe}")
    print(f"  julia_project={julia_project}")
    print(f"  samples={metrics['n']}  duration={metrics['duration_s']:.2f}s  realized={metrics['realized_hz']:.1f} Hz")
    print(f"  pitch RMS={metrics['pitch_rms']:.4f}  yaw RMS={metrics['yaw_rms']:.4f} rad")
    print(f"  pitch sat={metrics['pitch_sat_frac']:.3f}  yaw sat={metrics['yaw_sat_frac']:.3f}")
    print(f"  first_u={np.asarray(rec.u[0]).tolist()}  last_u={np.asarray(rec.u[-1]).tolist()}")
    if args.save:
        print(f"  saved -> {save_record(rec, metrics, cfg).relative_to(REPO)}")


if __name__ == "__main__":
    main()

"""run_control.py — close the loop for one (variant, mode, controller, application).

Thin CLI driven by flags or a YAML config (brief §12). Writes a standard record to
results/ and prints the realized loop rate + core Table-IV-style metrics.

Examples:
    python runners/run_control.py                    # helicopter, offline, PD, tracking
    python runners/run_control.py --model yaw_only --duration 20 --save
    python runners/run_control.py --config configs/experiments/helicopter_offline_pd_tracking.yaml
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from aero2.applications import make_application
from aero2.benchmarking.metrics import tracking_metrics
from aero2.config.capabilities import capability_notes
from aero2.control import make_controller
from aero2.execution.offline import OfflineBackend
from aero2.execution.virtual_twin import DEFAULT_QUANSER_PYTHON, VirtualTwinBackend
from aero2.execution.hardware import HardwareBackend
from aero2.io import make_estimator
from aero2.models import make_model


def add_controller_kwargs(cfg: dict) -> dict:
    cfg = dict(cfg)
    if cfg.get("controller") != "julia_policy":
        return cfg

    kwargs = dict(cfg.get("controller_kwargs", {}))
    module = cfg.get("julia_policy_module")
    function = cfg.get("julia_policy_function")
    julia = cfg.get("julia")
    if module:
        kwargs["module_path"] = module
    if function:
        kwargs["function_name"] = function
    if julia:
        kwargs["julia"] = julia
    cfg["controller_kwargs"] = kwargs
    return cfg


def build_backend(cfg, model):
    mode = cfg["execution_mode"]
    if mode == "offline":
        return OfflineBackend(
            model,
            dt=float(cfg.get("dt", 0.005)),
            quantize=bool(cfg.get("quantize", False)),
            measurement_noise=bool(cfg.get("measurement_noise", False)),
            emit_gyro=bool(cfg.get("emit_gyro", False)),
            seed=cfg.get("seed"),
        )
    if mode == "virtual_twin":
        return VirtualTwinBackend(
            aero_id=cfg.get("aero_id", "0"),
            frequency=float(cfg.get("hz", 200.0)),
            read_mode=int(cfg.get("read_mode", 1)),
            output_mode=cfg.get("output_mode", "mixed"),
            voltage_limit=float(cfg.get("voltage_limit", 15.0)),
            quanser_python=cfg.get("quanser_python", DEFAULT_QUANSER_PYTHON),
        )
    if mode == "hardware":
        return HardwareBackend(
            aero_id=cfg.get("aero_id", "0"),
            frequency=float(cfg.get("hz", 200.0)),
            read_mode=int(cfg.get("read_mode", 1)),
            output_mode=cfg.get("output_mode", "mixed"),
            voltage_limit=float(cfg.get("voltage_limit", 15.0)),
            quanser_python=cfg.get("quanser_python", DEFAULT_QUANSER_PYTHON),
        )
    raise NotImplementedError(
        f"execution_mode={mode!r} is scaffolded but not implemented; use 'offline' or 'virtual_twin'."
    )


def run(cfg: dict):
    model = make_model(cfg["model_variant"], **cfg.get("model_kwargs", {}))
    backend = build_backend(cfg, model)
    controller = make_controller(cfg["controller"], **cfg.get("controller_kwargs", {}))
    app = make_application(
        cfg["application"],
        duration_s=float(cfg.get("duration_s", 40.0)),
        nominal_hz=float(cfg.get("hz", 200.0)),
        **cfg.get("application_kwargs", {}),
    )
    estimator = make_estimator(cfg.get("estimator", "passthrough"))
    rec = app.run(backend, controller, estimator)
    return rec, tracking_metrics(rec)


def save_record(rec, metrics, cfg) -> Path:
    out_dir = REPO / cfg.get("out", "results")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = f"{cfg['model_variant']}_{cfg['execution_mode']}_{cfg['controller']}_{cfg['application']}_{stamp}"
    np.savez(
        out_dir / f"{tag}.npz",
        t=np.asarray(rec.t), x_est=np.asarray(rec.x_est),
        u=np.asarray(rec.u), ref=np.asarray(rec.ref), dt=np.asarray(rec.dt),
    )
    (out_dir / f"{tag}.json").write_text(json.dumps({"config": cfg, "metrics": metrics}, indent=2))
    return out_dir / f"{tag}.json"


def main(argv=None):
    p = argparse.ArgumentParser(description="Run one Aero2 closed-loop experiment.")
    p.add_argument("--config", help="YAML experiment config (overrides flags)")
    p.add_argument("--model", default="helicopter_2dof", dest="model_variant")
    p.add_argument("--mode", default="offline", dest="execution_mode")
    p.add_argument("--controller", default="pd")
    p.add_argument("--application", default="reference_tracking")
    p.add_argument("--estimator", default="passthrough", choices=["passthrough", "aero2"])
    p.add_argument("--duration", type=float, default=40.0, dest="duration_s")
    p.add_argument("--hz", type=float, default=200.0)
    p.add_argument("--dt", type=float, default=0.005)
    p.add_argument("--aero-id", default="0")
    p.add_argument("--read-mode", type=int, default=1)
    p.add_argument("--output-mode", choices=["direct", "mixed", "mixed-reversed"], default="mixed")
    p.add_argument("--voltage-limit", type=float, default=15.0)
    p.add_argument("--quanser-python", default=str(DEFAULT_QUANSER_PYTHON))
    p.add_argument("--julia-policy-module", help="Julia file to include when --controller julia_policy is selected.")
    p.add_argument("--julia-policy-function", default="Aero2PolicySmoke.pd_policy")
    p.add_argument("--julia", default="julia", help="Julia executable used by JuliaPolicyController.")
    p.add_argument("--save", action="store_true")
    args = p.parse_args(argv)

    if args.config:
        import yaml  # lazy: only needed for YAML configs
        cfg = yaml.safe_load(Path(args.config).read_text())
    else:
        cfg = {k: v for k, v in vars(args).items() if k not in ("config", "save")}
    cfg = add_controller_kwargs(cfg)
    # the gyro-rate estimator needs a synthesized gyro from the offline backend
    if cfg.get("estimator", "passthrough") == "aero2":
        cfg.setdefault("emit_gyro", True)

    rec, m = run(cfg)
    print(f"[{cfg['model_variant']} | {cfg['execution_mode']} | {cfg['controller']} | {cfg['application']}]")
    for note in capability_notes(
        cfg["model_variant"],
        cfg["execution_mode"],
        cfg["controller"],
        cfg["application"],
    ):
        print(f"  {note}")
    print(f"  samples={m['n']}  duration={m['duration_s']:.2f}s  realized={m['realized_hz']:.1f} Hz")
    print(f"  pitch RMS={m['pitch_rms']:.4f}  yaw RMS={m['yaw_rms']:.4f} rad")
    print(f"  tail pitch MAE={m['tail_pitch_mae']:.4f}  tail yaw MAE={m['tail_yaw_mae']:.4f} rad")
    print(f"  pitch sat={m['pitch_sat_frac']:.3f}  yaw sat={m['yaw_sat_frac']:.3f}")
    if args.save:
        print(f"  saved -> {save_record(rec, m, cfg).relative_to(REPO)}")


if __name__ == "__main__":
    main()

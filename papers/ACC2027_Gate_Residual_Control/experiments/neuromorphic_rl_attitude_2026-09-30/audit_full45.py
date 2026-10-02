"""Check completeness and interface invariants of the 45-s RL replays."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gra_control.platforms.drone import SPECS, _free_joint, torque_limits  # noqa: E402

MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    results = []
    errors = []
    for platform, slug in (("x2", "x2"), ("cf2-rotor", "cf2")):
        spec = SPECS[platform]
        model = mujoco.MjModel.from_xml_path(str(spec.model))
        _, body_id, _, _ = _free_joint(model)
        limits = torque_limits(platform, model.body_inertia[body_id].copy(), model, "model")
        root = HERE / "results" / f"full45_{slug}_cmg_envelope"
        manifest = json.loads((root / "manifest.json").read_text())
        if manifest["source_sha256"]["runner"] != sha(HERE / "run_rl.py"):
            errors.append(f"{platform}: runner hash mismatch")
        for mission in MISSIONS:
            folder = root / "eval" / mission
            summary = json.loads((folder / "summary.json").read_text())
            with np.load(folder / "full_rate_trace.npz") as archive:
                z = {k: archive[k] for k in archive.files}
            n = len(z["t"])
            checks = {
                "samples": n == 90000,
                "time_start": abs(z["t"][0]) < 1e-12,
                "time_end": abs(z["t"][-1] - 44.9995) < 1e-6,
                "mean_error": abs(np.mean(z["qerr_rad"]) - summary["qerr_true_mean_rad"]) < 1e-12,
                "finite": all(np.all(np.isfinite(v)) for v in z.values()),
                "activity_bound": np.all((z["activity"] >= -1e-12) & (z["activity"] <= 1 + 1e-12)),
                "residual_bound": np.all(np.abs(z["raw_residual"]) <= summary["beta"] * limits + 1e-10),
                "gate_identity": np.allclose(z["gated_residual"], z["raw_residual"] * z["output_gate"], atol=1e-12),
                "torque_box": np.all(np.abs(z["tau_command"]) <= limits + 1e-10),
                "source_model": summary["model_sha256"] == sha(spec.model),
            }
            checks = {name: bool(okay) for name, okay in checks.items()}
            bad = [name for name, okay in checks.items() if not okay]
            if bad:
                errors.append(f"{platform}/{mission}: {bad}")
            results.append({"platform": platform, "mission": mission, "samples": n,
                            "status": "pass" if not bad else "fail", "checks": checks})
    report = {"status": "pass" if not errors else "fail", "runs": len(results),
              "errors": errors, "results": results}
    out = HERE / "analysis" / "full45" / "audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"{report['status']}: {len(results)} runs; errors={errors}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

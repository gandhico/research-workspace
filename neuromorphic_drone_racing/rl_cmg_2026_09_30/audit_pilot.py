"""Read-only integrity audit of the five frozen final X2 pilot arms."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
MODES = ("mlp", "graded", "crossing", "reset_gate", "reset_spike")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    checked = []
    for mode in MODES:
        folder = HERE / "results" / f"final_x2_{mode}_seed1"
        manifest = json.loads((folder / "manifest.json").read_text())
        summary = json.loads((folder / "summary.json").read_text())
        assert summary["mode"] == mode and summary["seed"] == 1
        assert summary["observation"] == "reference"
        assert summary["bc_samples"] == 600
        assert summary["ppo_rollouts"] == 2
        assert sum(x["simulator_steps"] for x in summary["training"]) == 12000
        assert sha256(HERE / "results" / "race_world_x2.xml") == manifest["vehicle_xml_hash"]
        for filename, digest in manifest["source_hashes"].items():
            assert sha256(HERE / filename) == digest, f"source changed: {filename}, {mode}"
        for filename, digest in manifest["race_source_hashes"].items():
            assert sha256(HERE.parent / filename) == digest, f"race source changed: {filename}, {mode}"
        teacher = dict(np.load(folder / "teacher.npz"))
        evaluation = dict(np.load(folder / "eval.npz"))
        assert len(teacher["t"]) == 600 and int(teacher["gates"][-1]) == 4
        assert len(evaluation["t"]) == summary["eval_samples"]
        assert int(evaluation["gates"][-1]) == summary["eval_gates"]
        assert str(evaluation["done_reason"][-1]) == summary["eval_termination_reason"]
        for name, arr in evaluation.items():
            if arr.dtype.kind in "if":
                assert np.isfinite(arr).all(), f"nonfinite {mode}/{name}"
        assert np.max(np.abs(evaluation["action"])) <= 1.0 + 1e-8
        assert evaluation["activity"].min() >= -1e-8 and evaluation["activity"].max() <= 1.0 + 1e-8
        assert evaluation["gate"].min() >= -1e-8 and evaluation["gate"].max() <= 1.0 + 1e-8
        for k in range(2):
            train = dict(np.load(folder / f"train_{k:03d}.npz"))
            assert len(train["t"]) == 600
            assert len(train["episode_id"]) == 600
            assert train["episode_id"].min() == 0
        checked.append(dict(mode=mode, teacher_gates=4,
                            eval_gates=summary["eval_gates"],
                            eval_duration_s=summary["eval_samples"] * summary["policy_dt"],
                            ppo_simulator_steps=12000,
                            termination=summary["eval_termination_reason"]))
    out = HERE / "results" / "final_pilot_analysis" / "audit.json"
    out.write_text(json.dumps({"passed": len(checked), "expected": len(MODES), "runs": checked}, indent=2))
    print(f"Audit passed {len(checked)}/{len(MODES)} final runs: {out}")


if __name__ == "__main__":
    main()

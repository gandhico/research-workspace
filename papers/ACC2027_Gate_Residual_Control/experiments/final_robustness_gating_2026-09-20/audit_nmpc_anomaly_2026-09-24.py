"""Audit: why does NMPC regress on X2 Roll/Yaw360 (A5 anomaly) while every other family, including the
structurally similar MPC, improves there? NMPC is the only A5 family run with a --baseline-rate-hz hold (100 Hz,
reused from an old exploratory NMPC-only setting, PREREGISTRATION.md sec.14); every other family, MPC included,
updates every sim step (rate=0 default). `AdvancedBaseline.torque()` implements the hold generically (any family,
not NMPC-specific -- run_mujoco_nef_baselines.py:127-128,218-220): with the hold on, tau0 is a zero-order-hold
staircase updated every `every = round(1/(rate*dt))` steps while the CMG-PES residual updates every single step.

Two ablations, both X2 Roll+Yaw360 (the two anomalous, near-floor missions), classical + CMG-gated:
  (1) NMPC with the hold REMOVED (--baseline-rate-hz 0)   -- does the anomaly disappear?
  (2) MPC  with the SAME hold IMPOSED (--baseline-rate-hz 100) -- can the anomaly be induced elsewhere?
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_controllers_gated.py"
OUT = HERE / "results" / "audit_nmpc_anomaly_2026-09-24"

CASES = [
    ("nmpc_hold100_asrun", "nmpc", 100.0, ["--nmpc-dt", "0.06", "--nmpc-horizon", "5", "--nmpc-grid", "3",
                                            "--nmpc-predict", "policy", "--nmpc-offset-frac", "0.1", "--nmpc-rate-weight", "2.0"]),
    ("nmpc_no_hold", "nmpc", 0.0, ["--nmpc-dt", "0.06", "--nmpc-horizon", "5", "--nmpc-grid", "3",
                                    "--nmpc-predict", "policy", "--nmpc-offset-frac", "0.1", "--nmpc-rate-weight", "2.0"]),
    ("mpc_no_hold_asrun", "mpc", 0.0, ["--mpc-dt", "0.02", "--mpc-horizon", "120", "--mpc-q-rate", "0.0"]),
    ("mpc_100hz_hold", "mpc", 100.0, ["--mpc-dt", "0.02", "--mpc-horizon", "120", "--mpc-q-rate", "0.0"]),
]
MISSIONS = ("roll", "yaw360")


def run(tag, family, rate, extra, mission, controller):
    out = OUT / tag / mission / controller
    out.mkdir(parents=True, exist_ok=True)
    beta = 0.0 if controller == "classical" else 0.5
    cmd = [sys.executable, str(RUNNER), "--platform", "x2", "--controller", controller, "--mission", mission,
           "--duration", "45.0", "--dt", "0.0005", "--beta", str(beta), "--learning-rate", "0.0008",
           "--k-error", "8", "--k-rate", "0", "--actuator-scale", "1.0", "--seed", "1",
           "--baseline", family, "--bw-scale", "3.0", "--baseline-rate-hz", str(rate),
           "--rate-ff", "left-neg", "--no-model-ff",
           "--log-every", "10", "--no-neural-archive", "--output", str(out)] + extra
    if controller == "nengo-nef-pes":
        cmd += ["--output-gate", "torque-saturation-opposition", "--gate-load-threshold", "1.0",
                "--gate-epsilon-fraction", "0", "--gate-epsilon-nm", "1e-12"]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode:
        raise RuntimeError(f"{tag}/{mission}/{controller}: {done.stderr[-800:]}")
    s = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    return tag, mission, controller, s["metrics"]["qerr_true_mean_rad"]


if __name__ == "__main__":
    jobs = [(tag, fam, rate, extra, m, c) for tag, fam, rate, extra in CASES for m in MISSIONS
            for c in ("classical", "nengo-nef-pes")]
    print(f"running {len(jobs)} cells...", flush=True)
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda j: run(*j), jobs))

    by_key = {(t, m, c): e for t, m, c, e in results}
    print(f"\n{'case':22s}{'mission':10s}{'baseline[mrad]':>16s}{'+CMG[mrad]':>14s}{'delta[%]':>10s}")
    known = {("nmpc_hold100_asrun", "roll"): (0.345, 0.332, 3.8), ("nmpc_hold100_asrun", "yaw360"): (0.200, 0.317, -57.9),
             ("mpc_no_hold_asrun", "roll"): (0.410, 0.124, 69.7), ("mpc_no_hold_asrun", "yaw360"): (0.233, 0.134, 42.6)}
    for tag, _, _, _ in CASES:
        for m in MISSIONS:
            b = by_key[(tag, m, "classical")] * 1e3
            c = by_key[(tag, m, "nengo-nef-pes")] * 1e3
            d = 100 * (1 - c / b)
            note = ""
            if (tag, m) in known:
                kb, kc, kd = known[(tag, m)]
                note = f"  (A5 campaign had: {kb:.3f} -> {kc:.3f}, {kd:+.1f}%; reproduced here: {'OK' if abs(b-kb) < 0.01 and abs(c-kc) < 0.01 else 'DIFFERS'})"
            print(f"{tag:22s}{m:10s}{b:16.4f}{c:14.4f}{d:10.1f}{note}")

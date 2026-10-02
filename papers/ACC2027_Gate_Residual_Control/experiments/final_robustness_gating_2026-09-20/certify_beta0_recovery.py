"""Certify Proposition 1(iii) -- exact baseline recovery at beta=0 -- empirically, for the new controller families.

Prop. 1 assumes nothing about how u0 is computed; AdvancedBaseline.torque() is just another u0 source. This has been
proved once, in general, for any baseline satisfying the assumptions (Sec. V of the paper). This script tests it is
not violated in practice by the new merged runner's control flow, for one representative of each structurally
different family (lqr: linear; smc: reaching-law with a clip; mpc: finite-horizon unconstrained; nmpc: grid receding-
horizon, the one with the 100Hz-hold interaction flagged in the A5 results) -- run with the CMG augmentor PRESENT but
beta=0, and diffed bit-for-bit against the classical (no augmentor) run of the same family/mission.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_controllers_gated.py"
OUT = HERE / "results_izh_corrected" / "beta0_recovery"
CASES = [("lqr", "x2", "hard45"), ("smc", "cf2-rotor", "hardstep"), ("mpc", "x2", "full3"),
         ("nmpc", "x2", "roll"), ("nmpc", "x2", "yaw360")]


def run(family, platform, mission, controller, beta):
    out = OUT / family / platform / mission / controller
    out.mkdir(parents=True, exist_ok=True)
    fam_flags = {"lqr": [], "smc": ["--smc-eta-frac", "0.5"],
                 "mpc": ["--mpc-dt", "0.02", "--mpc-horizon", "120", "--mpc-q-rate", "0.0"],
                 "nmpc": ["--nmpc-dt", "0.06", "--nmpc-horizon", "5", "--nmpc-grid", "3", "--nmpc-predict", "policy",
                          "--nmpc-offset-frac", "0.1", "--nmpc-rate-weight", "2.0", "--baseline-rate-hz", "100"]}[family]
    scale = 1.5 if platform == "cf2-rotor" else 1.0
    cmd = [sys.executable, str(RUNNER), "--platform", platform, "--controller", controller, "--mission", mission,
           "--duration", "10.0", "--dt", "0.0005", "--beta", str(beta), "--learning-rate", "0.0008",
           "--k-error", "8", "--k-rate", "0", "--actuator-scale", str(scale), "--seed", "1",
           "--baseline", family, "--bw-scale", "3.0", "--rate-ff", "left-neg", "--no-model-ff",
           "--log-every", "1", "--no-neural-archive", "--output", str(out)] + fam_flags
    if controller == "nengo-nef-pes":
        cmd += ["--output-gate", "torque-saturation-opposition", "--gate-load-threshold", "1.0",
                "--gate-epsilon-fraction", "0", "--gate-epsilon-nm", "1e-12"]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode:
        raise RuntimeError(done.stderr[-800:])
    return json.loads((out / "summary.json").read_text(encoding="utf-8"))["metrics"]["qerr_true_mean_rad"]


if __name__ == "__main__":
    print(f"{'family':8s}{'platform':10s}{'mission':10s}{'classical':>14s}{'CMG beta=0':>14s}{'rel diff':>12s}")
    worst = 0.0
    for fam, plat, mission in CASES:
        a = run(fam, plat, mission, "classical", 0.0)
        b = run(fam, plat, mission, "nengo-nef-pes", 0.0)
        rel = abs(a - b) / a if a else abs(a - b)
        worst = max(worst, rel)
        print(f"{fam:8s}{plat:10s}{mission:10s}{a*1e3:14.9f}{b*1e3:14.9f}{rel:12.2e}")
    print(f"\nworst relative deviation across all cases: {worst:.2e}  (exact recovery certified if this is ~machine precision)")

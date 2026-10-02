"""Is the CF2 Izhikevich validation gap (3e-4) just the model's sensitivity to last-bit differences?

Runs the new runner with an initial-attitude perturbation far below any physical relevance (1e-12 and 1e-10 deg, i.e. ~1e-14 and
~1e-12 rad) and compares the 45-s mean error with the unperturbed run.  If a 1e-14 rad perturbation alone moves the mean by ~1e-4,
the archived-vs-new gap on CF2 is inside the model's own reproducibility floor.  Also runs one X2 perturbation for reference.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_izh_robustness.py"
ROOT = HERE / "results_validation_izh" / "sensitivity"


def run(platform, mission, beta, scale, eps):
    out = ROOT / f"{platform}_{mission}_b{beta}_eps{eps:g}"
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(RUNNER), "--platform", platform, "--controller", "nengo-izhikevich-pes", "--mission", mission,
           "--duration", "45.0", "--dt", "0.0005", "--beta", str(beta), "--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0",
           "--actuator-scale", str(scale), "--seed", "1", "--initial-angle-deg", repr(eps), "--log-every", "10",
           "--no-neural-archive", "--output", str(out)]
    if not (out / "summary.json").exists():
        done = subprocess.run(cmd, capture_output=True, text=True)
        if done.returncode:
            raise RuntimeError(done.stderr[-1000:])
    s = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    return s["metrics"]["qerr_true_mean_rad"]


if __name__ == "__main__":
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    jobs = [("cf2-rotor", "hard45", 0.2, 1.5, 0.0), ("cf2-rotor", "hard45", 0.2, 1.5, 1e-12), ("cf2-rotor", "hard45", 0.2, 1.5, 1e-10),
            ("x2", "hard45", 0.5, 1.0, 1e-12)]
    with ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(lambda j: run(*j), jobs))
    base = res[0]
    redirect = redirect_stdout(buf)
    redirect.__enter__()
    print("CF2 Hard45, beta 0.2, Izhikevich-PES: 45-s mean error [mrad] for initial-attitude perturbations")
    for j, r in zip(jobs[:3], res[:3]):
        print(f"  perturbation {j[4]:>8g} deg   mean {r * 1e3:.6f}   relative change vs unperturbed {abs(r - base) / base:.2e}")
    print("archived-runner value 8.070892  (new runner unperturbed 8.073354; gap 3.05e-04)")
    x2 = 9.816749e-3
    print(f"X2 Hard45, beta 0.5, perturbation 1e-12 deg: mean {res[3] * 1e3:.6f}  (unperturbed 9.816749)  relative change {abs(res[3] - x2) / x2:.2e}")
    redirect.__exit__(None, None, None)
    (ROOT / "sensitivity_result.txt").write_text(buf.getvalue(), encoding="utf-8")
    print(buf.getvalue())

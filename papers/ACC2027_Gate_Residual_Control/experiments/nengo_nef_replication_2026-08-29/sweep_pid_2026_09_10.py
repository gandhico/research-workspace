"""PID baseline for Table V: regression, tuning, matched set, stretch.

Phases (run in order; each is resumable -- a finished cell is skipped):

  regress  --ki-factor 0 on all 20 Table V cells. Every qerr_mean must equal
           the stored results/matched_45s value exactly, or the PID runner is
           not a faithful copy and nothing after this can be trusted.
  tune     PD+integral on all 10 classical cells for each factor in FACTORS.
           The tuning set IS the evaluation set, which favours the baseline:
           that is the conservative direction for this paper's claim.
  stretch  CMG-PES on top of the tuned PID, per platform. Answers: does the
           neural residual still help once integral action is present?

Flags match run_campaign.py exactly (dt, beta, learning rate, k_error,
k_rate, actuator scale, log_every).

Run:  python sweep_pid_2026_09_10.py --phase all
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
RUNNER = HERE / "run_mujoco_nef_pid.py"
CANON = HERE / "results" / "matched_45s"
ROOT = HERE / "results" / "pid_baseline_2026-09-10"

PLATFORMS = {"x2": 1.0, "cf2-rotor": 1.5}
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
FACTORS = (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0)
WORKERS = 8


def label(plat: str, mis: str, ctl: str) -> str:
    return f"{plat}_{mis}_{ctl}".replace("-", "_")


def run(plat: str, mis: str, ctl: str, factor: float, out: Path) -> dict:
    if (out / "summary.json").is_file():
        return json.loads((out / "summary.json").read_text())
    cmd = [PY, str(RUNNER),
           "--platform", plat, "--controller", ctl, "--mission", mis,
           "--duration", "45", "--dt", "0.0005",
           "--beta", "0.5", "--learning-rate", "0.0008",
           "--k-error", "8", "--k-rate", "0",
           "--actuator-scale", str(PLATFORMS[plat]),
           "--log-every", "10",
           "--ki-factor", repr(factor),
           "--no-neural-archive",
           "--output", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{out.name} failed:\n{r.stderr[-1200:]}")
    return json.loads((out / "summary.json").read_text())


def pool(jobs: list[tuple]) -> dict:
    """jobs: (key, plat, mis, ctl, factor, out). Returns {key: summary}."""
    got, t0 = {}, time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        fut = {ex.submit(run, *j[1:]): j[0] for j in jobs}
        for k, f in enumerate(as_completed(fut), 1):
            got[fut[f]] = f.result()
            print(f"  [{k:3d}/{len(jobs)}] {fut[f]}   "
                  f"({time.time() - t0:.0f}s)", flush=True)
    return got


# ===========================================================================
def phase_regress() -> bool:
    print("\n=== regress: --ki-factor 0 must reproduce Table V exactly ===")
    jobs = []
    for plat in PLATFORMS:
        for mis in MISSIONS:
            for ctl in ("classical", "nengo-nef-pes"):
                lab = label(plat, mis, ctl)
                jobs.append((lab, plat, mis, ctl, 0.0,
                             ROOT / "regress" / lab))
    got = pool(jobs)
    # PD must be bit-exact: it proves the patched torque law is faithful.
    # CMG is held to 1e-5 relative, not bit-exactness. A diagnostic on
    # 2026-09-10 showed the CANONICAL runner itself now differs from the
    # stored Table V CMG values by ~5e-7 relative (PD still exact), and that
    # the PID runner at ki=0 equals the canonical runner run today exactly.
    # So the stored CMG values are not reachable by any runner in this
    # environment; the comparison that isolates the integral term is against
    # today's CMG-on-PD, which phase_stretch uses.
    ok = True
    print(f"\n{'cell':34s}{'Table V stored':>22s}{'PID runner ki=0':>22s}  status")
    for lab in sorted(got):
        canon = json.loads((CANON / lab / "summary.json").read_text())
        a, b = canon["qerr_mean_rad"], got[lab]["qerr_mean_rad"]
        rel = abs(a - b) / a
        if "classical" in lab:
            good, tag = a == b, ("exact" if a == b else "PD MISMATCH")
        else:
            good, tag = rel < 1e-5, f"drift {rel:.1e}" + ("" if rel < 1e-5 else " TOO LARGE")
        ok &= good
        print(f"{lab:34s}{a:22.17f}{b:22.17f}  {tag}")
    print(f"\nregression {'PASSED: PD bit-exact, CMG within 1e-5' if ok else 'FAILED'}")
    return ok


def phase_tune() -> dict:
    print("\n=== tune: PID factor sweep on all 10 classical cells ===")
    jobs = []
    for f in FACTORS:
        for plat in PLATFORMS:
            for mis in MISSIONS:
                key = f"{plat}|{mis}|{f}"
                jobs.append((key, plat, mis, "classical", f,
                             ROOT / "tune" / f"ki{f:g}" / label(plat, mis, "classical")))
    got = pool(jobs)

    best = {}
    for plat in PLATFORMS:
        pd = {m: json.loads((CANON / label(plat, m, "classical") / "summary.json")
                            .read_text())["qerr_mean_rad"] for m in MISSIONS}
        print(f"\n{plat}: mean quaternion-angle error [rad]  "
              f"(PD row = Table V, ki=0)")
        print(f"{'factor':>8s}" + "".join(f"{m:>11s}" for m in MISSIONS)
              + f"{'mean':>11s}{'vs PD':>9s}{'sat max':>10s}")
        print(f"{'PD':>8s}" + "".join(f"{pd[m]:11.6f}" for m in MISSIONS)
              + f"{st.mean(pd.values()):11.6f}{'':>9s}")
        scores = {}
        for f in FACTORS:
            v = {m: got[f"{plat}|{m}|{f}"]["qerr_mean_rad"] for m in MISSIONS}
            sat = max(got[f"{plat}|{m}|{f}"]["saturation_fraction"] for m in MISSIONS)
            mean = st.mean(v.values())
            scores[f] = mean
            rel = 100 * (1 - mean / st.mean(pd.values()))
            print(f"{f:8g}" + "".join(f"{v[m]:11.6f}" for m in MISSIONS)
                  + f"{mean:11.6f}{rel:8.1f}%{sat:10.4f}")
        fb = min(scores, key=scores.get)
        edge = fb in (FACTORS[0], FACTORS[-1])
        best[plat] = fb
        print(f"  -> tuned factor {fb:g}"
              + ("   WARNING: optimum on grid edge, widen FACTORS" if edge else
                 "   (interior optimum)"))
    (ROOT / "tuned_factors.json").write_text(json.dumps(best, indent=2))
    return best


def phase_stretch(best: dict) -> None:
    print("\n=== stretch: CMG-PES on top of the tuned PID ===")
    jobs = []
    for plat, f in best.items():
        for mis in MISSIONS:
            key = f"{plat}|{mis}"
            jobs.append((key, plat, mis, "nengo-nef-pes", f,
                         ROOT / "stretch" / f"ki{f:g}" / label(plat, mis, "nengo_nef_pes")))
    got = pool(jobs)

    rows = []
    for plat, f in best.items():
        for mis in MISSIONS:
            c = lambda lab: json.loads((CANON / lab / "summary.json").read_text())
            pd = c(label(plat, mis, "classical"))["qerr_mean_rad"]
            # Today's CMG-on-PD (same environment as CMG-on-PID), so the two
            # differ only by the integral term. Table V's stored value is
            # kept alongside for traceability.
            cmg_stored = c(label(plat, mis, "nengo_nef_pes"))["qerr_mean_rad"]
            cmg = json.loads((ROOT / "regress" / label(plat, mis, "nengo_nef_pes")
                              / "summary.json").read_text())["qerr_mean_rad"]
            pid = json.loads((ROOT / "tune" / f"ki{f:g}" / label(plat, mis, "classical")
                              / "summary.json").read_text())["qerr_mean_rad"]
            pidcmg = got[f"{plat}|{mis}"]["qerr_mean_rad"]
            rows.append({
                "platform": plat, "mission": mis, "ki_factor": f,
                "PD": pd, "PID": pid, "CMG_on_PD": cmg, "CMG_on_PID": pidcmg,
                "PID_vs_PD_pct": 100 * (1 - pid / pd),
                "CMGonPD_vs_PD_pct": 100 * (1 - cmg / pd),
                "CMGonPID_vs_PID_pct": 100 * (1 - pidcmg / pid),
                "gap_closed_by_PID_pct": 100 * (pd - pid) / (pd - cmg),
            })
    with (ROOT / "pid_baseline_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"\n{'platform':10s}{'mission':10s}{'PD':>9s}{'PID':>9s}{'CMG|PD':>9s}"
          f"{'CMG|PID':>9s}{'PID/PD':>9s}{'CMG|PD':>9s}{'CMG|PID':>10s}{'gap':>8s}")
    print(f"{'':20s}{'[rad]':>9s}{'':>9s}{'':>9s}{'':>9s}"
          f"{'red.':>9s}{'vs PD':>9s}{'vs PID':>10s}{'closed':>8s}")
    for r in rows:
        print(f"{r['platform']:10s}{r['mission']:10s}{r['PD']:9.5f}{r['PID']:9.5f}"
              f"{r['CMG_on_PD']:9.5f}{r['CMG_on_PID']:9.5f}"
              f"{r['PID_vs_PD_pct']:8.1f}%{r['CMGonPD_vs_PD_pct']:8.1f}%"
              f"{r['CMGonPID_vs_PID_pct']:9.1f}%{r['gap_closed_by_PID_pct']:7.1f}%")
    print(f"\nwritten {ROOT / 'pid_baseline_summary.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("regress", "tune", "stretch", "all"),
                    default="all")
    a = ap.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    if a.phase in ("regress", "all"):
        if not phase_regress():
            sys.exit("stopping: the PID runner does not reproduce Table V")
    if a.phase in ("tune", "all"):
        best = phase_tune()
    else:
        best = json.loads((ROOT / "tuned_factors.json").read_text())
    if a.phase in ("stretch", "all"):
        phase_stretch(best)

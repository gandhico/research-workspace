"""Model-based baselines against PD+ff, with and without CMG-PES.

Same protocol as the PID study (sweep_pid_2026_09_10.py):

  tune     each family, classical only, --bw-scale over --grid on all ten
           Table V cells; the best single bw per (family, platform) by
           mission-mean error. Tuning on the evaluation set favours the
           baselines, the conservative direction for the CMG claim.
  stretch  CMG-PES on top of each family at its tuned bw.

Families
  pdff          PD + reference-rate feedforward (backstepping --no-model-ff,
                algebraically PD+ff: 1.1e-14 on X2 Roll). The strongest simple
                baseline; "CMG on tuned PD+ff" is the key comparison.
  lqr, backstepping, smc, mpc   aero2 formulations, 3-axis, with feedforward
  nmpc          aero2 grid-search NMPC, closed-loop prediction, 100 Hz ZOH,
                rate-error cost weight 0 (0.201 -> 0.160 rad on X2 Full3 3 s)

Noise
  --noise none       the Table V setting
  --noise realistic  Table VI "realistic" measurement noise (0.020 rad,
                     0.050 rad/s, seed 7). In a noise-free sim more gain keeps
                     helping until saturation; noise gives an interior optimum.

Every family runs with --rate-ff left-neg (the verified feedforward mode).
Resumable: a cell whose summary.json exists is skipped. Tree layout
  tune/<family>[_noise]/bw<g>/<cell>   stretch/<family>[_noise]/bw<g>/<cell>
matches the PD+ff runs already on disk, so they are reused.

Run:  python sweep_baselines_2026_09_10.py --phase all --families pdff lqr \\
          backstepping smc mpc --grid 0.75 1 1.5 2 3 4 6 8
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
RUNNER = HERE / "run_mujoco_nef_baselines.py"
RES = HERE / "results"
ROOT = RES / "baselines_2026-09-10"
FF_CSV = RES / "pid_baseline_2026-09-10" / "rate_ff_summary.csv"
PLATFORMS = {"x2": "1.0", "cf2-rotor": "1.5"}
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
WORKERS = 4   # 10 concurrent Nengo runs exhausted RAM on 2026-09-10

FAMILY_ARGS = {
    "pdff": ["--baseline", "backstepping", "--no-model-ff"],
    "lqr": ["--baseline", "lqr"],
    "backstepping": ["--baseline", "backstepping"],
    "smc": ["--baseline", "smc"],
    "mpc": ["--baseline", "mpc"],
    "nmpc": ["--baseline", "nmpc", "--baseline-rate-hz", "100",
             "--nmpc-rate-weight", "0"],
}
NOISE_ARGS = ["--attitude-noise-std", "0.02", "--rate-noise-std", "0.05", "--seed", "7"]


def lab(p, m, c):
    return f"{p}_{m}_{c}".replace("-", "_")


def tree(kind, fam, noisy):
    return ROOT / kind / (fam + ("_noise" if noisy else ""))


def run(fam, p, m, ctl, g, out, noisy):
    if not (out / "summary.json").is_file():
        cmd = [PY, str(RUNNER), "--platform", p, "--controller", ctl,
               "--mission", m, "--duration", "45", "--dt", "0.0005",
               "--beta", "0.5", "--learning-rate", "0.0008",
               "--k-error", "8", "--k-rate", "0",
               "--actuator-scale", PLATFORMS[p], "--log-every", "10",
               "--rate-ff", "left-neg", *FAMILY_ARGS[fam],
               "--bw-scale", repr(float(g)),
               *(NOISE_ARGS if noisy else []),
               "--no-neural-archive", "--output", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"{out}:\n{r.stderr[-1200:]}")
    return json.loads((out / "summary.json").read_text())


def pool(jobs):
    got, t0 = {}, time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        fut = {ex.submit(run, *j[1:]): j[0] for j in jobs}
        for k, f in enumerate(as_completed(fut), 1):
            got[fut[f]] = f.result()
            if k % 10 == 0 or k == len(jobs):
                print(f"  [{k:3d}/{len(jobs)}]  {time.time() - t0:.0f}s", flush=True)
    return got


def tuned_path(noisy):
    return ROOT / f"tuned_bw{'_noise' if noisy else ''}.json"


def load_tuned(noisy):
    p = tuned_path(noisy)
    return json.loads(p.read_text()) if p.is_file() else {}


def phase_tune(families, grid, noisy):
    tag = "realistic noise" if noisy else "noise-free"
    print(f"\n=== tune ({tag}): bandwidth sweep, classical only ===")
    jobs = [((fam, p, m, g), fam, p, m, "classical", g,
             tree("tune", fam, noisy) / f"bw{g:g}" / lab(p, m, "classical"), noisy)
            for fam in families for g in grid for p in PLATFORMS for m in MISSIONS]
    got = pool(jobs)
    best = load_tuned(noisy)
    for fam in families:
        for p in PLATFORMS:
            print(f"\n{fam} / {p} ({tag}): mean error [rad]")
            print(f"{'bw':>6s}" + "".join(f"{m:>10s}" for m in MISSIONS)
                  + f"{'mean':>10s}{'sat max':>9s}")
            scores = {}
            for g in grid:
                v = [got[(fam, p, m, g)]["qerr_mean_rad"] for m in MISSIONS]
                sat = max(got[(fam, p, m, g)]["saturation_fraction"] for m in MISSIONS)
                scores[g] = st.mean(v)
                print(f"{g:6g}" + "".join(f"{x:10.5f}" for x in v)
                      + f"{scores[g]:10.5f}{sat:9.4f}")
            gb = min(scores, key=scores.get)
            best[f"{fam}|{p}"] = gb
            print(f"  -> tuned bw {gb:g}" + ("   WARNING: grid edge"
                                            if gb in (grid[0], grid[-1]) else "   (interior)"))
    tuned_path(noisy).write_text(json.dumps(best, indent=2))
    return best


def phase_stretch(families, best, noisy):
    tag = "realistic noise" if noisy else "noise-free"
    print(f"\n=== stretch ({tag}): CMG-PES on top of each tuned family ===")
    jobs = [((fam, p, m), fam, p, m, "nengo-nef-pes", best[f"{fam}|{p}"],
             tree("stretch", fam, noisy) / f"bw{best[f'{fam}|{p}']:g}"
             / lab(p, m, "nengo_nef_pes"), noisy)
            for fam in families for p in PLATFORMS for m in MISSIONS]
    got = pool(jobs)
    ff = {(r["platform"], r["mission"]): r for r in csv.DictReader(FF_CSV.open())}
    rows = []
    for fam in families:
        for p in PLATFORMS:
            g = best[f"{fam}|{p}"]
            gff = best.get(f"pdff|{p}")
            for m in MISSIONS:
                alone = json.loads((tree("tune", fam, noisy) / f"bw{g:g}"
                                    / lab(p, m, "classical") / "summary.json").read_text())
                cmg = got[(fam, p, m)]
                pdff_t = (json.loads((tree("tune", "pdff", noisy) / f"bw{gff:g}"
                                      / lab(p, m, "classical") / "summary.json").read_text())
                          ["qerr_mean_rad"] if gff is not None else float("nan"))
                rows.append({
                    "noise": "realistic" if noisy else "none",
                    "family": fam, "platform": p, "mission": m, "bw": g,
                    "PD_TableV": float(ff[(p, m)]["PD"]),
                    "PDff_tuned": pdff_t,
                    "family_alone": alone["qerr_mean_rad"],
                    "CMG_on_family": cmg["qerr_mean_rad"],
                    "family_vs_PDff_tuned_pct": 100 * (1 - alone["qerr_mean_rad"] / pdff_t),
                    "CMG_vs_family_pct": 100 * (1 - cmg["qerr_mean_rad"] / alone["qerr_mean_rad"]),
                    "sat_family": alone["saturation_fraction"],
                    "sat_CMG": cmg["saturation_fraction"],
                    "residual_mean_Nm": cmg["residual_mean_Nm"],
                })
    out = ROOT / f"baselines_summary{'_noise' if noisy else ''}.csv"
    old = list(csv.DictReader(out.open())) if out.is_file() else []
    keep = [r for r in old if r["family"] not in families]
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(keep + rows)
    print(f"\n{'family':13s}{'cell':20s}{'bw':>5s}{'PD+ff*':>9s}{'family':>9s}{'CMG|fam':>9s}"
          f"{'fam vs ff*':>11s}{'CMG vs fam':>11s}{'sat':>7s}")
    for r in rows:
        print(f"{r['family']:13s}{r['platform'] + ' ' + r['mission']:20s}{r['bw']:5g}"
              f"{r['PDff_tuned']:9.5f}{r['family_alone']:9.5f}{r['CMG_on_family']:9.5f}"
              f"{r['family_vs_PDff_tuned_pct']:10.1f}%{r['CMG_vs_family_pct']:10.1f}%"
              f"{r['sat_CMG']:7.4f}")
    print(f"(PD+ff* = PD+ff at its own tuned bandwidth)\nwritten {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("tune", "stretch", "all"), default="all")
    ap.add_argument("--families", nargs="+", default=["pdff", "lqr", "backstepping", "smc", "mpc"],
                    choices=list(FAMILY_ARGS))
    ap.add_argument("--grid", nargs="+", type=float, default=[0.75, 1.0, 1.5, 2.0])
    ap.add_argument("--noise", choices=("none", "realistic"), default="none")
    a = ap.parse_args()
    noisy = a.noise == "realistic"
    ROOT.mkdir(parents=True, exist_ok=True)
    if a.phase in ("tune", "all"):
        best = phase_tune(a.families, a.grid, noisy)
    else:
        best = load_tuned(noisy)
    if a.phase in ("stretch", "all"):
        phase_stretch(a.families, best, noisy)

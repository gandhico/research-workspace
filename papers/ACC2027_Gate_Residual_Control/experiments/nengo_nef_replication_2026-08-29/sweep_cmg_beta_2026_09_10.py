"""Residual authority beta for CMG-PES on each tuned baseline family.

The first CMG-on-family runs used Table V's beta = 0.5 at every family's tuned
bandwidth (2-3x the PD's). That authority is far too large there: CMG diverged
on CF2 Hardstep under every family (~2.3 rad, saturation 0.84-0.92) and
doubled X2 Roll error under LQR, backstepping and MPC. The 6-DOF study already
showed the admissible beta is a property of the baseline-residual pair
(CF2 cascade 0.008, X2 0.05). So beta is swept per (family, platform).

SELECTION RULE -- fixed here before any of these results exist:
  admissible  every mission qerr < 1.0 rad and CMG saturation fraction < 0.5
  score       geometric mean over the five missions of
              (CMG-on-family error) / (family-alone error)
              -- equal weight per mission. The mission-mean used for the
              bandwidth tuning is dominated by Hardstep (~0.26 rad against
              <= 0.01 elsewhere), so it is not used to pick beta.
  choice      the admissible beta with the lowest score.
  verdict     score < 1: CMG helps this family at its best beta;
              score >= 1: CMG does not help it at any beta tested.
The Hardstep-dominated mission-mean choice is printed alongside, for
transparency, but does not decide anything.

beta = 0.5 reuses the stretch/ runs; lr stays 8e-4 throughout.

Run:  python sweep_cmg_beta_2026_09_10.py --families pdff lqr backstepping smc mpc
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics as st
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import sweep_baselines_2026_09_10 as SB

PY = sys.executable
BETAS = (0.5, 0.2, 0.1, 0.05, 0.02)
WORKERS = 2   # alongside the 2-worker disturbance test; 10 concurrent Nengo runs OOM-ed here


def cell_path(fam, p, m, g, b):
    if b == 0.5:
        return SB.tree("stretch", fam, False) / f"bw{g:g}" / SB.lab(p, m, "nengo_nef_pes")
    return SB.ROOT / "cmg_beta" / fam / f"bw{g:g}" / f"b{b:g}" / SB.lab(p, m, "nengo_nef_pes")


def run(fam, p, m, g, b):
    out = cell_path(fam, p, m, g, b)
    if not (out / "summary.json").is_file():
        cmd = [PY, str(SB.RUNNER), "--platform", p, "--controller", "nengo-nef-pes",
               "--mission", m, "--duration", "45", "--dt", "0.0005",
               "--beta", repr(float(b)), "--learning-rate", "0.0008",
               "--k-error", "8", "--k-rate", "0",
               "--actuator-scale", SB.PLATFORMS[p], "--log-every", "10",
               "--rate-ff", "left-neg", *SB.FAMILY_ARGS[fam],
               "--bw-scale", repr(float(g)), "--no-neural-archive",
               "--output", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"{out}:\n{r.stderr[-1200:]}")
    return json.loads((out / "summary.json").read_text())


def alone(fam, p, m, g):
    f = SB.tree("tune", fam, False) / f"bw{g:g}" / SB.lab(p, m, "classical") / "summary.json"
    return json.loads(f.read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", nargs="+", default=["pdff", "lqr", "backstepping", "smc", "mpc"])
    a = ap.parse_args()
    tuned = SB.load_tuned(False)

    jobs = [((fam, p, m, b), fam, p, m, tuned[f"{fam}|{p}"], b)
            for fam in a.families for p in SB.PLATFORMS for m in SB.MISSIONS for b in BETAS]
    got, t0 = {}, time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        fut = {ex.submit(run, *j[1:]): j[0] for j in jobs}
        for k, f in enumerate(as_completed(fut), 1):
            got[fut[f]] = f.result()
            if k % 20 == 0 or k == len(jobs):
                print(f"  [{k:3d}/{len(jobs)}]  {time.time() - t0:.0f}s", flush=True)

    rows, verdicts = [], []
    for fam in a.families:
        for p in SB.PLATFORMS:
            g = tuned[f"{fam}|{p}"]
            base = {m: alone(fam, p, m, g) for m in SB.MISSIONS}
            print(f"\n{fam} / {p}  (tuned bw {g:g})   error [rad], CMG vs family alone")
            print(f"{'beta':>6s}" + "".join(f"{m:>17s}" for m in SB.MISSIONS)
                  + f"{'geo-ratio':>11s}{'mean':>9s}  admissible")
            print(f"{'alone':>6s}" + "".join(f"{base[m]['qerr_mean_rad']:17.5f}" for m in SB.MISSIONS))
            scored = []
            for b in BETAS:
                c = {m: got[(fam, p, m, b)] for m in SB.MISSIONS}
                ratios = [c[m]["qerr_mean_rad"] / base[m]["qerr_mean_rad"] for m in SB.MISSIONS]
                geo = math.exp(st.mean(math.log(max(r, 1e-12)) for r in ratios))
                mean = st.mean(c[m]["qerr_mean_rad"] for m in SB.MISSIONS)
                ok = (max(c[m]["qerr_mean_rad"] for m in SB.MISSIONS) < 1.0
                      and max(c[m]["saturation_fraction"] for m in SB.MISSIONS) < 0.5)
                scored.append((geo, b, mean, ok))
                print(f"{b:6g}" + "".join(
                    f"{c[m]['qerr_mean_rad']:9.5f}{100 * (1 - r):+7.1f}%" for m, r in zip(SB.MISSIONS, ratios))
                    + f"{geo:11.3f}{mean:9.5f}  {'yes' if ok else 'NO'}")
            adm = [s for s in scored if s[3]]
            if not adm:
                verdicts.append((fam, p, None, None, "no admissible beta"))
                print("  -> no admissible beta")
                continue
            geo, b, _, _ = min(adm)
            bmean = min(adm, key=lambda s: s[2])[1]
            edge = b in (BETAS[0], BETAS[-1])
            v = "CMG helps" if geo < 1.0 else "CMG does not help"
            verdicts.append((fam, p, b, geo, v))
            print(f"  -> beta {b:g}, geo-ratio {geo:.3f}: {v}"
                  + ("   WARNING: grid edge" if edge else "")
                  + f"   [Hardstep-dominated mean would pick {bmean:g}]")
            for m in SB.MISSIONS:
                c = got[(fam, p, m, b)]
                rows.append({"family": fam, "platform": p, "mission": m, "bw": g, "beta": b,
                             "family_alone": base[m]["qerr_mean_rad"],
                             "CMG_on_family": c["qerr_mean_rad"],
                             "CMG_vs_family_pct": 100 * (1 - c["qerr_mean_rad"] / base[m]["qerr_mean_rad"]),
                             "sat_CMG": c["saturation_fraction"],
                             "residual_mean_Nm": c["residual_mean_Nm"]})

    out = SB.ROOT / "cmg_beta_summary.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("\n=== verdicts (pre-declared rule) ===")
    for fam, p, b, geo, v in verdicts:
        print(f"  {fam:13s}{p:11s}" + (f"beta {b:<6g} geo-ratio {geo:.3f}  " if b is not None else "")
              + v)
    print(f"written {out}")

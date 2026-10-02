"""Compile the 2026-09-10 6-DOF feedforward study into final tables.

Selection rules are fixed here, before the last results arrive, so the
reported configuration cannot be chosen after seeing it:

  baseline config  the (wn_att, wn_pos) that minimises
                   SCORE = pos err(waypoint_step) + pos err(circle_xy)
                           + pos err(full6_stress)
                   among stable runs (every mission pos < 1 m, att < 20 deg).
                   hover3d is excluded: every stable config holds it exactly.
  CMG beta         the beta that minimises the same SCORE for CMG on top of
                   the selected baseline.

Columns reported per platform and mission:
  canonical PD          the published 6-DOF baseline (no feedforward)
  canonical CMG         the published CMG-PES result on that baseline
  tuned PD + pos-ff     the selected classical configuration
  CMG on tuned          CMG-PES on the selected configuration, selected beta

Run:  python compile_ff6_report.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
O = HERE / "results" / "ff6_2026-09-10"
M = ("hover3d", "waypoint_step", "circle_xy", "full6_stress")
SCORED = M[1:]


def j(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.is_file() else None


def score(cells):
    if any(c is None for c in cells):
        return None
    pos = [c["pos_err_mean_m"] for c in cells]
    att = [np.degrees(c["qerr_mean_rad"]) for c in cells]
    if max(pos) >= 1.0 or max(att) >= 20.0:
        return float("inf")
    return sum(pos[1:])


def best_config(tune_dir):
    cand = []
    for d in sorted(tune_dir.iterdir()):
        s = score([j(d / m / "summary.json") for m in M])
        if s is not None:
            cand.append((s, d.name))
    cand.sort()
    return cand


def best_beta(pattern, betas):
    """pattern(beta, mission) -> summary path. hover3d included if present."""
    cand = []
    for b in betas:
        cells = [j(pattern(b, m)) for m in M]
        if cells[0] is None:                       # hover not run for this sweep
            cells[0] = {"pos_err_mean_m": 0.0, "qerr_mean_rad": 0.0}
        s = score(cells)
        if s is not None:
            cand.append((s, b))
    cand.sort()
    return cand


def fmt(c):
    return "—" if c is None else f"{c['pos_err_mean_m']:.4f} m / {np.degrees(c['qerr_mean_rad']):.2f}°"


def main():
    lines, rows = [], []

    # ---------------- X2 ----------------------------------------------------
    x2c = best_config(O / "x2_tune")
    x2cfg = x2c[0][1]
    x2b = best_beta(lambda b, m: O / "x2_beta20" / f"b{b}_{m}" / "summary.json",
                    ("0.1", "0.05", "0.02", "0.008"))
    # ---------------- CF2 ---------------------------------------------------
    cf2c = best_config(O / "cf2_tune")
    cf2cfg = cf2c[0][1]
    canon_cf2 = "a12_12_10_p2_2_2.4"

    def cf2_cmg(b, m):
        # CMG beta sweep at the *selected* CF2 configuration. At the canonical
        # 12/2 it lives in cf2/ (beta 0.008) and cf2_beta/; at any other
        # configuration in cf2_beta_sel/<config>/.
        if cf2cfg == canon_cf2:
            return (O / "cf2" / f"{m}_pes_fd" / "summary.json") if b == "0.008" \
                else (O / "cf2_beta" / f"b{b}_{m}" / "summary.json")
        return O / "cf2_beta_sel" / cf2cfg / f"b{b}_{m}" / "summary.json"

    cf2b = best_beta(cf2_cmg, ("0.002", "0.008", "0.02", "0.05"))

    for plat, cfg, cands, betas, canon_dir, cmg_path in (
        ("X2", x2cfg, x2c, x2b, "optionA",
         lambda b, m: O / "x2_beta20" / f"b{b}_{m}" / "summary.json"),
        ("CF2", cf2cfg, cf2c, cf2b, "optionA_cf2_tuned", cf2_cmg),
    ):
        tune = "x2_tune" if plat == "X2" else "cf2_tune"
        lines.append(f"\n## {plat}\n")
        lines.append(f"Selected baseline: `{cfg}` (score {cands[0][0]:.4f}); "
                     f"runner-up `{cands[1][1]}` ({cands[1][0]:.4f}).")
        if betas:
            lines.append(f"Selected CMG β = {betas[0][1]} (score {betas[0][0]:.4f}); "
                         + ", ".join(f"β={b}: {s:.4f}" for s, b in betas[1:]))
        else:
            lines.append("**CMG β not yet swept at the selected CF2 configuration.**")
        lines.append("")
        lines.append("| mission | canonical PD | canonical CMG | tuned PD + pos-ff | CMG on tuned |")
        lines.append("|---|---|---|---|---|")
        for m in M:
            cp = j(HERE / "results" / canon_dir / f"{m}_classical" / "summary.json")
            cc = j(HERE / "results" / canon_dir / f"{m}_pes" / "summary.json")
            tp = j(O / tune / cfg / m / "summary.json")
            tc = j(cmg_path(betas[0][1], m)) if betas else None
            lines.append(f"| {m} | {fmt(cp)} | {fmt(cc)} | {fmt(tp)} | {fmt(tc)} |")
            rows.append({"platform": plat, "mission": m, "config": cfg,
                         "beta": betas[0][1] if betas else "",
                         **{f"{k}_pos": (c["pos_err_mean_m"] if c else "")
                            for k, c in (("canonPD", cp), ("canonCMG", cc),
                                         ("tunedPD", tp), ("CMGtuned", tc))},
                         **{f"{k}_att_deg": (np.degrees(c["qerr_mean_rad"]) if c else "")
                            for k, c in (("canonPD", cp), ("canonCMG", cc),
                                         ("tunedPD", tp), ("CMGtuned", tc))}})

    out = O / "ff6_report.md"
    out.write_text("# 6-DOF feedforward study — compiled tables\n"
                   + "\n".join(lines) + "\n", encoding="utf-8")
    with (O / "ff6_report.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")   # Windows console is cp1252
    main()

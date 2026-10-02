"""v3 allocation screen (PLAN v3 addendum): tpa_r vs apa on already-seen CF2 step missions.

Rule (declared before running): choose the variant with the higher worst-case z_min over
{pid, st_pid, dual} x {hardstep, hardstep_b}; tie (within 0.05 m) -> lower geometric-mean error.
Pure tpa is also run and reported as the documented negative result.
"""
from __future__ import annotations

import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "results" / "quat_v3_2026-09-12" / "alloc_screen"
CONTROLLERS = ("pid", "st_pid", "dual")
MISSIONS = ("hardstep", "hardstep_b")
VARIANTS = ("tpa", "tpa_r", "apa")


def job(args):
    alloc, m, c = args
    sys.path.insert(0, str(HERE))
    from run_dual import run  # noqa: E402
    s = run("cf2-rotor", m, c, OUT / alloc / m / c, allocation=alloc)
    return alloc, m, c, s["qerr_mean_rad"], s["z_min_m"], s["alpha_min"], s["torque_scaled_fraction"]


def main():
    todo = [(a, m, c) for a in VARIANTS for m in MISSIONS for c in CONTROLLERS
            if not (OUT / a / m / c / "summary.json").exists()]
    with ProcessPoolExecutor(max_workers=4) as ex:
        for f in as_completed([ex.submit(job, t) for t in todo]):
            print("done", f.result(), flush=True)
    R = {}
    for a in VARIANTS:
        for m in MISSIONS:
            for c in CONTROLLERS:
                R[(a, m, c)] = json.loads((OUT / a / m / c / "summary.json").read_text(encoding="utf-8"))
    L = ["# v3 allocation screen (CF2, seen step missions)", "",
         "| variant | mission | controller | mean q-error [rad] | z_min [m] | alpha_min | torque scaled frac |",
         "|---|---|---|---|---|---|---|"]
    for (a, m, c), s in R.items():
        L.append(f"| {a} | {m} | {c} | {s['qerr_mean_rad']:.4f} | {s['z_min_m']:.3f} | {s['alpha_min']:.3f} | "
                 f"{s['torque_scaled_fraction']:.4f} |")
    score = {}
    for a in ("tpa_r", "apa"):
        zs = [R[(a, m, c)]["z_min_m"] for m in MISSIONS for c in CONTROLLERS]
        g = math.exp(sum(math.log(R[(a, m, c)]["qerr_mean_rad"]) for m in MISSIONS for c in CONTROLLERS) / 6)
        score[a] = (min(zs), g)
    za, ga = score["tpa_r"]
    zb, gb = score["apa"]
    if abs(za - zb) <= 0.05:
        chosen = "tpa_r" if ga <= gb else "apa"
        why = f"tie on worst-case z_min ({za:.3f} vs {zb:.3f}); lower geo-mean error ({ga:.4f} vs {gb:.4f})"
    else:
        chosen = "tpa_r" if za > zb else "apa"
        why = f"higher worst-case z_min ({za:.3f} vs {zb:.3f})"
    L += ["", f"**Selected: `{chosen}`** ({why}).",
          f"Worst-case z_min / geo-mean error: tpa_r {za:.3f} m / {ga:.4f} rad; apa {zb:.3f} m / {gb:.4f} rad."]
    (OUT / "SCREEN.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (OUT / "selected.json").write_text(json.dumps({"allocation": chosen, "reason": why, "score": score}, indent=1),
                                       encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()

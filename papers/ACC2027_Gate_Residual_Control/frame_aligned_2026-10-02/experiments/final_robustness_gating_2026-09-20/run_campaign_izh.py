"""Amendment A3 (PREREGISTRATION.md section 10, A3.1 in section 11): Izhikevich-PES under the CMG-PES protocol, reduced grid.

  python run_campaign_izh.py all        # 33 cases, <= 4 workers, resumable (valid outputs are skipped)
  python run_campaign_izh.py nominal | noise | dist

Same runner arithmetic as every CMG-PES result (run_izh_robustness.py = sealed runner + one controller choice), same baseline
(PD+ff rho = 3), same true-attitude metric, same exact-saturation output gate, same noise/disturbance definitions and seeds.
"""
from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import run_campaign as rc

HERE = Path(__file__).resolve().parent
rc.RUNNER = HERE / "run_izh_robustness.py"          # the sealed runner is untouched
CTRL = "nengo-izhikevich-pes"
BETA_GATED = {"x2": 0.5, "cf2-rotor": 0.2}          # the CMG choices (Table I)
PROTOCOL = "izh_a3"


def _tag(beta):
    return {0.5: "b0p5", 0.2: "b0p2", 0.05: "b0p05"}[beta]


def case(platform, mission, beta, gated, *, campaign="nominal", seed=1, level=None, dist_mult=None):
    att, rate = (rc.NOISE_LEVELS[level][:2] if level else (0.0, 0.0))
    return rc.Case(protocol=PROTOCOL, campaign=campaign, platform=platform, mission=mission,
                   label=f"izh_pes_{'gated' if gated else 'ungated'}_{_tag(beta)}", controller=CTRL, beta=beta, seed=seed,
                   output_gate=rc.GATE_OUTPUT if gated else "none", gate_load_threshold=1.0,
                   attitude_noise_std=att, rate_noise_std=rate, noise_level=level or "none",
                   disturbance_torque=(rc.DISTURBANCE_NM[platform] * dist_mult) if dist_mult else 0.0,
                   disturbance_schedule="intermittent" if dist_mult else "continuous",
                   disturbance_level=f"x{dist_mult:g}" if dist_mult else "none",
                   save_neural_archive=(campaign == "nominal" and mission in ("hard45", "hardstep")) or bool(dist_mult))


def nominal():
    out = []
    for plat, beta in BETA_GATED.items():                      # 5 + 5 gated
        out += [case(plat, m, beta, True) for m in rc.MISSIONS]
    out += [case("x2", "hardstep", 0.5, False),                 # 3 ungated Hardstep cells (new runner)
            case("cf2-rotor", "hardstep", 0.05, False), case("cf2-rotor", "hardstep", 0.2, False)]
    return out


def noise():
    return [case(plat, m, beta, True, campaign="noise", seed=s, level="realistic")
            for plat, beta in BETA_GATED.items() for m in ("roll", "hard45", "hardstep") for s in (1, 2, 3)]


def dist():
    return [case(plat, "hover", beta, True, campaign="dist", dist_mult=1.0) for plat, beta in BETA_GATED.items()]


STAGES = {"nominal": nominal, "noise": noise, "dist": dist, "all": lambda: nominal() + noise() + dist()}

if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    cs = STAGES[stage]()
    root = rc.DEFAULT_RESULTS
    print(f"{len(cs)} A3 cases ({stage}); results {root / PROTOCOL}", flush=True)
    rows, fails, t0 = [], [], time.time()
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(rc.run_case, c, root, 45.0, 5e-4, False): c for c in cs}
        for n, f in enumerate(as_completed(futs), 1):
            c = futs[f]
            try:
                r = f.result()
                rows.append(rc.flatten(c, r))
                print(f"[{n:2d}/{len(cs)}] {r['status']:13s} {time.time() - t0:6.0f}s  {c.case_id}", flush=True)
            except Exception as exc:
                fails.append((c.case_id, str(exc)[:500]))
                print(f"[{n:2d}/{len(cs)}] FAILED        {c.case_id}: {str(exc)[:300]}", flush=True)
    rc.write_csv(root / f"results_izh_a3_{stage}.csv", rows)
    print(f"done in {time.time() - t0:.0f}s; {len(rows)} ok, {len(fails)} failed", flush=True)
    for cid, err in fails:
        print("FAILED", cid, err)

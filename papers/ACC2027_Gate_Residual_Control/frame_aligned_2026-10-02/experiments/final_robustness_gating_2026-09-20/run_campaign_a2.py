"""Amendment A2 (PREREGISTRATION.md section 9).  Uses the sealed driver's machinery with the A2 runner copy.

  python run_campaign_a2.py dev                 # 4 variants x CF2 Hardstep x moderate noise x seeds 1,2   (development)
  python run_campaign_a2.py nominal <variant>   # noise-free five-mission CF2 run of a safe variant       (selection input)
  python run_campaign_a2.py confirm <variant>   # held-out: CF2/X2 Hardstep, moderate seeds 3-5 + realistic seeds 1-10, and
                                                # all nominal cells (both platforms)                         (confirmation)
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import run_campaign as rc

HERE = Path(__file__).resolve().parent
rc.RUNNER = HERE / "run_a2_robustness.py"          # the sealed runner is untouched

ROTOR = "torque-saturation-opposition+rotor-flag"
STARVE = "torque-saturation-opposition+thrust-starvation"
VARIANTS = {   # label -> (beta, gate)
    "rotorflag": (0.5, ROTOR),
    "starvation": (0.5, STARVE),
    "gated_b02": (0.2, rc.GATE_OUTPUT),
    "gated_b01": (0.1, rc.GATE_OUTPUT),
}
MISSIONS = rc.MISSIONS


def case(variant, platform, mission, *, seed=1, level=None, campaign="a2", dist_mult=None):
    beta, gate = VARIANTS[variant]
    att, rate = (rc.NOISE_LEVELS[level][:2] if level else (0.0, 0.0))
    return rc.Case(protocol="development_only" if campaign == "a2_dev" else "confirmatory_a2", campaign=campaign,
                   platform=platform, mission=mission, label=f"cmg_pes_{variant}", controller="nengo-nef-pes",
                   beta=beta, seed=seed, output_gate=gate, attitude_noise_std=att, rate_noise_std=rate,
                   noise_level=level or "none", gate_load_threshold=1.0,
                   disturbance_torque=(rc.DISTURBANCE_NM[platform] * dist_mult) if dist_mult else 0.0,
                   disturbance_schedule="intermittent" if dist_mult else "continuous",
                   disturbance_level=f"x{dist_mult:g}" if dist_mult else "none",
                   save_neural_archive=bool(dist_mult == 1.0))


def baseline(platform, mission, *, seed=1, level=None, campaign="a2"):
    att, rate = (rc.NOISE_LEVELS[level][:2] if level else (0.0, 0.0))
    return rc.Case(protocol="development_only" if campaign == "a2_dev" else "confirmatory_a2", campaign=campaign,
                   platform=platform, mission=mission, label="pdff_rho3", controller="classical", seed=seed,
                   attitude_noise_std=att, rate_noise_std=rate, noise_level=level or "none")


def cases(stage, variant=None):
    if stage == "dev":
        return [case(v, "cf2-rotor", "hardstep", seed=s, level="moderate", campaign="a2_dev")
                for v in VARIANTS for s in (1, 2)]
    if stage == "nominal":
        return [case(variant, "cf2-rotor", m, campaign="a2_nominal") for m in MISSIONS]
    if stage == "confirm":
        out = []
        # beta variants are per-airframe authorities: X2 keeps beta = 0.5, confirmation is CF2 only (PREREGISTRATION §9 addendum)
        for plat in (("cf2-rotor",) if variant in ("gated_b02", "gated_b01") else rc.PLATFORMS):
            for level, seeds in (("moderate", range(3, 6)), ("realistic", range(1, 11))):
                for s in seeds:
                    out.append(case(variant, plat, "hardstep", seed=s, level=level, campaign="a2_confirm"))
            for m in MISSIONS:
                out.append(case(variant, plat, m, campaign="a2_confirm_nominal"))
        return out
    if stage == "noise_rest":            # tables: the rest of the noise grid for the selected CF2 configuration
        out = []
        for level, seeds in (("moderate", range(1, 6)), ("realistic", range(1, 11))):
            for m in ("roll", "full3", "hard45", "yaw360"):
                for s in seeds:
                    out.append(case(variant, "cf2-rotor", m, seed=s, level=level, campaign="a2_noise"))
        return out
    if stage == "disturbance":           # tables: hover bursts at 0.5x / 1x / 2x
        return [case(variant, "cf2-rotor", "hover", campaign="a2_dist", dist_mult=mu) for mu in (0.5, 1.0, 2.0)]
    raise SystemExit(f"unknown stage {stage}")


if __name__ == "__main__":
    stage = sys.argv[1]
    variant = sys.argv[2] if len(sys.argv) > 2 else None
    cs = cases(stage, variant)
    root = rc.DEFAULT_RESULTS
    print(f"{len(cs)} A2 cases ({stage} {variant or ''})", flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(rc.run_case, c, root, 45.0, 5e-4, False): c for c in cs}
        for f in as_completed(futs):
            c = futs[f]
            r = f.result()
            print(f"{r['status']:10s} {c.case_id}", flush=True)
            rows.append(rc.flatten(c, r))
    rc.write_csv(root / f"results_a2_{stage}{'_' + variant if variant else ''}.csv", rows)

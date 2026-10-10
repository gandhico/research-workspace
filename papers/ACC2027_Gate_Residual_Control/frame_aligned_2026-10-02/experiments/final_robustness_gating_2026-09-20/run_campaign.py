"""Resumable final ACC robustness / saturation-gating campaigns (v2, 2026-09-20).

Extends Codex's first driver.  Everything here is frozen in PREREGISTRATION.md BEFORE any
campaign result is looked at; only the validation gate (run_validation.py) precedes it.

Confirmatory campaigns (baseline: PD + desired-rate feedforward at rho = 3, shared by all arms)
    nominal       5 missions x 2 platforms; arms: classical, CMG at the table beta, CMG gated at
                  beta = 0.5, and (CF2 only) CMG ungated at beta = 0.5
    disturbance   Hover, intermittent torque bursts at 0.5x / 1x / 2x the paper amplitude
    noise         5 missions x 2 platforms x paired seeds at two synthetic noise levels
    hardstep      alias of the Hardstep rows of ``nominal`` (kept for convenience)

Exploratory campaign
    hardstep-development   X2-ONLY screen of gate variants.  It cannot be reported as
                           confirmatory.  A variant is promoted only under the rule in
                           PREREGISTRATION.md section 5.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_final_robustness.py"
DEFAULT_RESULTS = HERE / "results"
PYTHON = sys.executable
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ACTUATOR_SCALE = {"x2": 1.0, "cf2-rotor": 1.5}
# beta used by the paper's tuned-baseline block (audited from master_table.csv, beta_sel)
BETA_TABLE = {"x2": 0.5, "cf2-rotor": 0.05}
BETA_CANONICAL = 0.5                       # Table I value, used by the gated arm on both airframes
DISTURBANCE_NM = {"x2": 0.15, "cf2-rotor": 0.00015}      # paper amplitudes d_b
DISTURBANCE_MULT = (0.5, 1.0, 2.0)
NOISE_LEVELS = {                            # name -> (attitude std [rad], rate std [rad/s], seeds)
    "moderate": (0.010, 0.025, 5),
    "realistic": (0.020, 0.050, 10),
}
DEV_THRESHOLDS = (1.0, 0.975, 0.95, 0.90)
GATE_OUTPUT = "torque-saturation-opposition"
GATE_FREEZE = "torque-saturation-opposition-freeze-pes"


@dataclass(frozen=True)
class Case:
    protocol: str
    campaign: str
    platform: str
    mission: str
    label: str
    controller: str
    beta: float = 0.0
    seed: int = 1
    output_gate: str = "none"
    gate_load_threshold: float = 1.0
    attitude_noise_std: float = 0.0
    rate_noise_std: float = 0.0
    noise_level: str = "none"
    disturbance_torque: float = 0.0
    disturbance_schedule: str = "continuous"
    disturbance_level: str = "none"
    save_neural_archive: bool = False

    @property
    def tag(self) -> str:
        parts = []
        if self.noise_level != "none":
            parts.append(f"noise_{self.noise_level}")
        if self.disturbance_level != "none":
            parts.append(f"dist_{self.disturbance_level}")
        if self.output_gate != "none":
            parts.append(f"load_{self.gate_load_threshold:g}")
        return "__".join(parts) if parts else "nominal"

    @property
    def case_id(self) -> str:
        return "__".join(
            [self.protocol, self.campaign, self.platform, self.mission, self.label,
             self.tag, f"seed{self.seed:03d}"]
        ).replace("-", "_")


def _hash_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _arms(platform: str, include_ungated_canonical: bool) -> list[tuple[str, str, float, str]]:
    """(label, controller, beta, gate) for the standard arms on one platform."""
    arms = [
        ("pdff_rho3", "classical", 0.0, "none"),
        ("cmg_pes_table", "nengo-nef-pes", BETA_TABLE[platform], "none"),
        ("cmg_pes_gated", "nengo-nef-pes", BETA_CANONICAL, GATE_OUTPUT),
    ]
    if include_ungated_canonical and platform == "cf2-rotor":
        arms.append(("cmg_pes_b05_ungated", "nengo-nef-pes", BETA_CANONICAL, "none"))
    return arms


def nominal_cases() -> list[Case]:
    out = []
    for platform in PLATFORMS:
        for mission in MISSIONS:
            for label, controller, beta, gate in _arms(platform, True):
                out.append(Case(
                    protocol="confirmatory", campaign="nominal", platform=platform, mission=mission,
                    label=label, controller=controller, beta=beta, output_gate=gate,
                    save_neural_archive=(controller != "classical" and mission in ("hard45", "hardstep")),
                ))
    return out


def hardstep_cases() -> list[Case]:
    return [c for c in nominal_cases() if c.mission == "hardstep"]


def disturbance_cases() -> list[Case]:
    out = []
    for platform in PLATFORMS:
        for mult in DISTURBANCE_MULT:
            for label, controller, beta, gate in _arms(platform, True):
                out.append(Case(
                    protocol="confirmatory", campaign="disturbance", platform=platform, mission="hover",
                    label=label, controller=controller, beta=beta, output_gate=gate,
                    disturbance_torque=DISTURBANCE_NM[platform] * mult,
                    disturbance_schedule="intermittent", disturbance_level=f"x{mult:g}",
                    save_neural_archive=(controller != "classical" and mult == 1.0),
                ))
    return out


def noise_cases() -> list[Case]:
    out = []
    for level, (att, rate, n_seeds) in NOISE_LEVELS.items():
        for platform in PLATFORMS:
            for mission in MISSIONS:
                for seed in range(1, n_seeds + 1):
                    for label, controller, beta, gate in _arms(platform, False):
                        out.append(Case(
                            protocol="confirmatory", campaign="noise", platform=platform, mission=mission,
                            label=label, controller=controller, beta=beta, output_gate=gate, seed=seed,
                            attitude_noise_std=att, rate_noise_std=rate, noise_level=level,
                        ))
    return out


def development_cases() -> list[Case]:
    """X2-only exploratory screen.  The exact-saturation output gate at threshold 1.0 is the
    confirmatory arm and is NOT repeated here."""
    out = []
    for thr in DEV_THRESHOLDS:
        for gate, tag in ((GATE_OUTPUT, "gate"), (GATE_FREEZE, "gate_freeze")):
            if gate == GATE_OUTPUT and thr == 1.0:
                continue
            out.append(Case(
                protocol="development_only", campaign="hardstep_variant_screen", platform="x2",
                mission="hardstep", label=f"cmg_pes_{tag}", controller="nengo-nef-pes",
                beta=BETA_CANONICAL, output_gate=gate, gate_load_threshold=thr,
            ))
    return out


CAMPAIGNS = {
    "nominal": nominal_cases,
    "hardstep": hardstep_cases,
    "disturbance": disturbance_cases,
    "noise": noise_cases,
    "hardstep-development": development_cases,
}


def select_cases(name: str) -> list[Case]:
    if name == "definitive":
        return nominal_cases() + disturbance_cases() + noise_cases()
    if name == "all":
        return nominal_cases() + development_cases() + disturbance_cases() + noise_cases()
    return CAMPAIGNS[name]()


def output_dir(root: Path, c: Case) -> Path:
    return root / c.protocol / c.campaign / c.platform / c.mission / c.label / c.tag / f"seed_{c.seed:03d}"


def command(c: Case, out: Path, duration: float, dt: float) -> list[str]:
    cmd = [
        PYTHON, str(RUNNER),
        "--platform", c.platform, "--controller", c.controller, "--mission", c.mission,
        "--duration", repr(duration), "--dt", repr(dt),
        "--beta", repr(c.beta if c.controller != "classical" else 0.0),
        "--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0",
        "--actuator-scale", repr(ACTUATOR_SCALE[c.platform]),
        "--seed", str(c.seed),
        "--attitude-noise-std", repr(c.attitude_noise_std),
        "--rate-noise-std", repr(c.rate_noise_std),
        "--disturbance-torque", repr(c.disturbance_torque),
        "--disturbance-schedule", c.disturbance_schedule,
        "--disturbance-warmup", "5", "--disturbance-on", "5", "--disturbance-off", "5",
        "--disturbance-ramp", "0.25",
        "--output-gate", c.output_gate, "--gate-load-threshold", repr(c.gate_load_threshold),
        "--gate-epsilon-fraction", "0", "--gate-epsilon-nm", "1e-12",
        "--log-every", "10", "--output", str(out),
    ]
    if not c.save_neural_archive:
        cmd.append("--no-neural-archive")
    return cmd


def _existing_valid(out: Path) -> bool:
    try:
        s = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        m = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    return bool(s.get("run_id") and s.get("run_id") == m.get("run_id"))


def run_case(c: Case, root: Path, duration: float, dt: float, rerun: bool) -> dict[str, Any]:
    out = output_dir(root, c)
    if not rerun and _existing_valid(out):
        return {"case_id": c.case_id, "status": "skipped_valid", "output": str(out),
                "summary": json.loads((out / "summary.json").read_text(encoding="utf-8"))}
    out.mkdir(parents=True, exist_ok=True)
    cmd = command(c, out, duration, dt)
    t0 = time.time()
    done = subprocess.run(cmd, capture_output=True, text=True)
    (out / "run.log").write_text(
        "$ " + subprocess.list2cmdline(cmd) + "\n\nSTDOUT\n" + done.stdout + "\nSTDERR\n" + done.stderr,
        encoding="utf-8")
    if done.returncode != 0:
        raise RuntimeError(f"{c.case_id} failed ({done.returncode}):\n" + done.stderr[-2000:])
    return {"case_id": c.case_id, "status": "completed", "elapsed_s": time.time() - t0,
            "output": str(out),
            "summary": json.loads((out / "summary.json").read_text(encoding="utf-8"))}


def flatten(c: Case, r: dict[str, Any]) -> dict[str, Any]:
    s = r["summary"]
    m, a = s["metrics"], s["actuation"]
    hs = s.get("hardstep") or {}
    ph = s["disturbance_phase_metrics_true_state"]
    return {
        "case_id": c.case_id, "protocol": c.protocol, "campaign": c.campaign, "platform": c.platform,
        "mission": c.mission, "label": c.label, "controller": c.controller, "beta": c.beta,
        "seed": c.seed, "noise_level": c.noise_level, "disturbance_level": c.disturbance_level,
        "output_gate": c.output_gate, "gate_load_threshold": c.gate_load_threshold,
        "qerr_true_mean_rad": m["qerr_true_mean_rad"],
        "qerr_feedback_mean_rad": m["qerr_feedback_mean_rad"],
        "qerr_true_max_rad": m["qerr_true_max_rad"],
        "residual_normalized_rms": m["realized_residual_normalized_rms"],
        "gate_blocked_fraction": s["output_gate"]["blocked_fraction_any_axis"],
        "torque_box_sat_fraction": a["torque_box_saturation_fraction_any_axis"],
        "rotor_sat_fraction": a["rotor_saturation_fraction_any_rotor"],
        "hardstep_slew_mean_rad": hs.get("slew_mean_rad"),
        "hardstep_settled_mean_rad": hs.get("settled_mean_rad"),
        "hardstep_settling_time_5deg_s": hs.get("settling_time_5deg_s_mean"),
        "disturbance_active_mean_rad": ph["active"]["mean_rad"],
        "disturbance_quiet_mean_rad": ph["quiet"]["mean_rad"],
        "run_id": s["run_id"], "configuration_sha256": s["configuration_sha256"],
        "output": r["output"], "status": r["status"],
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--campaign", choices=(*CAMPAIGNS, "definitive", "all"), default="definitive")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--duration", type=float, default=45.0)
    p.add_argument("--dt", type=float, default=5e-4)
    p.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--rerun", action="store_true")
    args = p.parse_args()
    if args.workers < 1 or args.workers > 4:
        raise SystemExit("--workers must be 1..4 (standing practice: at most 4 parallel CMG runs)")

    cases = select_cases(args.campaign)
    root = args.results_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    plan = {
        "schema": 2, "campaign_selection": args.campaign, "duration_s": args.duration, "dt_s": args.dt,
        "frozen_baseline": "PD + desired-rate feedforward, rho=3",
        "beta_table": BETA_TABLE, "beta_canonical": BETA_CANONICAL,
        "disturbance_nm": DISTURBANCE_NM, "disturbance_mult": DISTURBANCE_MULT,
        "noise_levels": NOISE_LEVELS, "dev_thresholds": DEV_THRESHOLDS,
        "n_cases": len(cases),
        "cases": [{**asdict(c), "case_id": c.case_id, "output": str(output_dir(root, c))} for c in cases],
    }
    plan["plan_sha256"] = _hash_json(plan)
    (root / f"campaign_plan_{args.campaign}.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"{len(cases)} cases; plan {plan['plan_sha256'][:16]}; results {root}", flush=True)
    if args.dry_run:
        return

    done: dict[str, dict[str, Any]] = {}
    fails: list[dict[str, str]] = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_case, c, root, args.duration, args.dt, args.rerun): c for c in cases}
        for n, f in enumerate(as_completed(futs), 1):
            c = futs[f]
            try:
                done[c.case_id] = f.result()
                print(f"[{n:3d}/{len(cases)}] {done[c.case_id]['status']:13s} {c.case_id}", flush=True)
            except Exception as exc:  # keep the other independent runs
                fails.append({"case_id": c.case_id, "error": str(exc)})
                print(f"[{n:3d}/{len(cases)}] FAILED        {c.case_id}: {exc}", flush=True)

    rows = [flatten(c, done[c.case_id]) for c in cases if c.case_id in done]
    write_csv(root / f"results_{args.campaign}.csv", rows)
    (root / f"status_{args.campaign}.json").write_text(json.dumps({
        "plan_sha256": plan["plan_sha256"], "requested": len(cases), "completed_or_resumed": len(done),
        "failed": len(fails), "elapsed_s": time.time() - t0, "failures": fails}, indent=2) + "\n", encoding="utf-8")
    if fails:
        raise SystemExit(f"{len(fails)} cases failed; see status_{args.campaign}.json")


if __name__ == "__main__":
    main()

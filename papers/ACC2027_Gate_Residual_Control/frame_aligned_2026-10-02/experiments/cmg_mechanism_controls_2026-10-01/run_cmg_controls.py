"""Run one CMG mechanism-control case on the frozen final PD+ff runner.

Same pattern as neuron_basis_decisive_2026-09-24/run_neuron_basis.py: the audited
final robustness runner supplies plant, rho=3 PD+desired-rate feedforward,
allocation, output gate, metrics and telemetry; only the six-feature residual
basis is replaced.

Controllers
-----------
classical                 unaugmented baseline
cmg                       canonical Nengo CMG (archived code path); --cmg-readout-gain
                          and --cmg-adaptive select readout gain G and conductance switch chi
cmg-numpy, lpf-logistic, constant-rest, latch-replay, constant-one-nengo-order
                          NumPy bases with Nengo PES ordering (cmg_control_adapters.py)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FINAL = REPO / "experiments" / "final_robustness_gating_2026-09-20"
UPSTREAM = REPO / "experiments" / "nengo_nef_replication_2026-08-29"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(UPSTREAM))
sys.path.insert(0, str(FINAL))
sys.path.insert(0, str(HERE))

import nengo_cmg  # noqa: E402
import run_izh_robustness as final_runner  # noqa: E402
from cmg_control_adapters import BASES, NengoOrderBasisAdapter, cmg_rest_activity  # noqa: E402

CONTROLLERS = ("classical", "cmg", *BASES)
SCHEDULE = HERE / "analysis" / "phase0" / "cmg_latch_schedule.json"
_ORIGINAL_CMG = nengo_cmg.CoupledMembraneGate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _json_dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _configured_cmg(gate_gain: float, adaptive: bool):
    """CoupledMembraneGate with a chosen readout gain G and conductance switch chi."""

    class ConfiguredCMG(_ORIGINAL_CMG):
        def __init__(self, adaptive=True, **kwargs):  # the augmentor always passes adaptive=True
            kwargs["gate_gain"] = gate_gain
            super().__init__(adaptive=forced_adaptive, **kwargs)

    forced_adaptive = adaptive
    return ConfiguredCMG


def _latch_times(platform: str, mission: str) -> list[float | None]:
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    return schedule["latch_time_s"][platform][mission]


def _variant(args) -> dict[str, Any]:
    if args.controller == "classical":
        return {"kind": "none", "description": "unaugmented baseline"}
    if args.controller == "cmg":
        return {"kind": "nengo-cmg", "readout_gain_G": args.cmg_readout_gain,
                "adaptive_conductance_chi": int(args.cmg_adaptive),
                "description": "canonical Nengo CMG neuron (nengo_cmg.py) with configured G and chi"}
    meta = {"kind": "numpy-basis-nengo-pes-order", "basis": args.controller,
            "pes_ordering": "W_k uses (y*_{k-1}-s_{k-1}) a_{k-1}^T, as Nengo CMG",
            "rest_activity": args.rest_activity}
    if args.controller == "latch-replay":
        meta["latch_times_s"] = _latch_times(args.platform, args.replay_mission or args.mission)
        meta["latch_schedule_source"] = str(SCHEDULE.relative_to(REPO)).replace("\\", "/")
    return meta


def run(args):
    requested = args.controller
    if args.rest_activity is None:
        args.rest_activity = cmg_rest_activity(args.dt)
    inner = {"classical": "classical", "cmg": "nengo-nef-pes"}.get(requested, "nengo-izhikevich-pes")

    original_adapter = final_runner.IzhikevichPESAdapter
    if requested in BASES:
        latch = _latch_times(args.platform, args.replay_mission or args.mission) if requested == "latch-replay" else None

        def factory(limits, dt, beta, learning_rate, seed):
            return NengoOrderBasisAdapter(requested, limits, dt, beta, learning_rate, seed,
                                          latch_times_s=latch, rest_activity=args.rest_activity,
                                          adaptive=bool(args.cmg_adaptive))

        final_runner.IzhikevichPESAdapter = factory
    if requested == "cmg":
        nengo_cmg.CoupledMembraneGate = _configured_cmg(args.cmg_readout_gain, bool(args.cmg_adaptive))
    args.controller = inner
    try:
        summary = final_runner.run(args)
    finally:
        final_runner.IzhikevichPESAdapter = original_adapter
        nengo_cmg.CoupledMembraneGate = _ORIGINAL_CMG
        args.controller = requested

    variant = _variant(args)
    summary["schema"] = 3
    summary["experiment"] = "cmg_mechanism_controls_2026-10-01"
    summary["controller"] = requested
    summary["controller_backend"] = variant["description"] if "description" in variant else variant["kind"]
    summary["residual_basis"] = variant
    summary["comparison_contract"] = {
        "baseline": "rho=3 PD + desired-rate feedforward",
        "paired_channels": 6,
        "decoder_initialization": "[I3,-I3]",
        "teacher": "clip(-k_error*e_q-k_rate*omega,-1,1)",
        "decoder_update": "PES (Nengo one-step ordering) + identical leak and projection",
        "residual": "beta*torque_limit*clip(Wa,-1,1)",
        "output_gate": args.output_gate,
        "only_intended_difference": "paired-current-to-activity mapping",
    }
    sources = {
        "wrapper": Path(__file__).resolve(),
        "adapters": HERE / "cmg_control_adapters.py",
        "final_runner": FINAL / "run_izh_robustness.py",
        "cmg_augmentor": UPSTREAM / "nengo_cmg.py",
    }
    if requested == "latch-replay":
        sources["latch_schedule"] = SCHEDULE
    source_hashes = {k: _sha256(p) for k, p in sources.items()}
    config = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items() if k != "output"}
    config["residual_basis"] = variant
    config_hash = _hash_json(config)
    summary["configuration_sha256"] = config_hash
    summary["run_id"] = _hash_json({"configuration_sha256": config_hash, "source_sha256": source_hashes})[:20]
    _json_dump(args.output / "summary.json", summary)

    manifest_path = args.output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "schema": 3, "experiment": summary["experiment"], "controller": requested,
        "residual_basis": variant, "configuration": config, "configuration_sha256": config_hash,
        "run_id": summary["run_id"], "source_sha256": source_hashes,
        "output_sha256": {n: _sha256(args.output / n) for n in
                          ("trace.csv", "summary.json", "neural_trace_full_rate.npz", "neural_trace_schema.json")
                          if (args.output / n).exists()},
    })
    _json_dump(manifest_path, manifest)
    return summary


def make_parser():
    parser = final_runner.make_parser()
    action = next(a for a in parser._actions if a.dest == "controller")
    action.choices = CONTROLLERS
    parser.add_argument("--cmg-readout-gain", type=float, default=1.0e5, help="CMG readout gain G in a=clip(G r,0,1)")
    parser.add_argument("--cmg-adaptive", type=int, choices=(0, 1), default=1, help="conductance switch chi")
    parser.add_argument("--rest-activity", type=float, default=None,
                        help="a_rest for constant-rest/latch-replay (default: computed CMG resting readout)")
    parser.add_argument("--replay-mission", default=None, help="latch schedule source mission (default: same)")
    return parser


if __name__ == "__main__":
    parsed = make_parser().parse_args()
    final_runner._validate(parsed)
    if parsed.cmg_readout_gain <= 0.0:
        raise SystemExit("--cmg-readout-gain must be positive")
    print(json.dumps(run(parsed), indent=2))

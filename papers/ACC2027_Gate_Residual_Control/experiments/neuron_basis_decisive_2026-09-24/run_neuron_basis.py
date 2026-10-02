"""Run one final-baseline neuron-family or no-neuron residual experiment.

This wrapper deliberately reuses the audited final robustness runner so the
plant, rho=3 PD+desired-rate-feedforward baseline, allocation, output gate,
metrics, and telemetry schema are identical to the manuscript-facing runs.
It injects only the selected six-feature residual adapter and then records the
actual controller identity and wrapper provenance in the saved metadata.
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

import run_izh_robustness as final_runner  # noqa: E402
from family_basis_adapter import FamilyPESAdapter, NoNeuronPESAdapter  # noqa: E402


CONTROLLERS = (
    "classical",
    "cmg",
    "lif",
    "alif",
    "lifrate",
    "izhikevich",
    "constant-one",
    "paired-current",
)
FAMILIES = {"lif", "alif", "lifrate", "izhikevich"}
NO_NEURON = {"constant-one", "paired-current"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _json_dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _adapter_factory(args):
    requested = args.controller

    def factory(limits, dt, beta, learning_rate, seed):
        if requested in FAMILIES:
            return FamilyPESAdapter(
                requested,
                limits,
                dt,
                beta,
                learning_rate,
                seed,
                current_bias=args.family_current_bias,
                current_gain=args.family_current_gain,
                feature_tau=args.family_feature_tau,
                feature_scale=args.family_feature_scale,
                native_current_scale=args.family_native_current_scale,
                learning_normalization=args.family_learning_normalization,
            )
        return NoNeuronPESAdapter(
            requested,
            limits,
            dt,
            beta,
            learning_rate,
            seed,
            current_bias=(
                0.75 if args.family_current_bias is None else args.family_current_bias
            ),
            current_gain=(
                1.25 if args.family_current_gain is None else args.family_current_gain
            ),
        )

    return factory


def _variant_metadata(args) -> dict[str, Any]:
    if args.controller == "classical":
        return {"kind": "none", "description": "unaugmented baseline"}
    if args.controller == "cmg":
        return {
            "kind": "continuous-neuron",
            "family": "cmg",
            "description": "canonical coupled membrane-gate Nengo neuron",
        }
    if args.controller in FAMILIES:
        return {
            "kind": "nengo-neuron",
            "family": args.controller,
            "current_bias": args.family_current_bias,
            "current_gain": args.family_current_gain,
            "feature_tau_s": args.family_feature_tau,
            "feature_scale_override": args.family_feature_scale,
            "native_current_scale_override": args.family_native_current_scale,
            "pes_normalization": args.family_learning_normalization,
            "description": "natural output, calibrated and low-pass filtered before PES",
        }
    return {
        "kind": "analytic-no-neuron-basis",
        "basis": args.controller,
        "current_bias": 0.75 if args.family_current_bias is None else args.family_current_bias,
        "current_gain": 1.25 if args.family_current_gain is None else args.family_current_gain,
        "description": (
            "six constant unit activities"
            if args.controller == "constant-one"
            else "paired encoded current divided by its maximum"
        ),
    }


def run(args):
    requested = args.controller
    inner_controller = {
        "classical": "classical",
        "cmg": "nengo-nef-pes",
    }.get(requested, "nengo-izhikevich-pes")

    original_adapter = final_runner.IzhikevichPESAdapter
    if requested in FAMILIES or requested in NO_NEURON:
        final_runner.IzhikevichPESAdapter = _adapter_factory(args)
    args.controller = inner_controller
    try:
        summary = final_runner.run(args)
    finally:
        final_runner.IzhikevichPESAdapter = original_adapter
        args.controller = requested

    variant = _variant_metadata(args)
    summary["schema"] = 3
    summary["experiment"] = "neuron_basis_decisive_2026-09-24"
    summary["controller"] = requested
    summary["controller_backend"] = variant["description"]
    summary["residual_basis"] = variant
    summary["comparison_contract"] = {
        "baseline": "rho=3 PD + desired-rate feedforward",
        "paired_channels": 6,
        "decoder_initialization": "[I3,-I3]",
        "teacher": "clip(-k_error*e_q-k_rate*omega,-1,1)",
        "decoder_update": "PES + identical leak and projection",
        "residual": "beta*torque_limit*clip(Wa,-1,1)",
        "output_gate": args.output_gate,
        "only_intended_difference": "paired-current-to-activity mapping",
    }

    source_paths = {
        "wrapper": Path(__file__).resolve(),
        "adapter": HERE / "family_basis_adapter.py",
        "final_runner": FINAL / "run_izh_robustness.py",
        "family_augmentor": UPSTREAM / "nengo_neuron_family.py",
        "cmg_augmentor": UPSTREAM / "nengo_cmg.py",
        "feature_calibration": UPSTREAM / "feature_calibration.json",
    }
    source_hashes = {name: _sha256(path) for name, path in source_paths.items()}
    config = {
        key: (str(value) if isinstance(value, Path) else value)
        for key, value in vars(args).items()
        if key != "output"
    }
    config["residual_basis"] = variant
    config_hash = _hash_json(config)
    run_id = _hash_json(
        {"configuration_sha256": config_hash, "source_sha256": source_hashes}
    )[:20]
    summary["configuration_sha256"] = config_hash
    summary["run_id"] = run_id

    summary_path = args.output / "summary.json"
    _json_dump(summary_path, summary)
    manifest_path = args.output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema"] = 3
    manifest["experiment"] = summary["experiment"]
    manifest["controller"] = requested
    manifest["residual_basis"] = variant
    manifest["configuration"] = config
    manifest["configuration_sha256"] = config_hash
    manifest["run_id"] = run_id
    manifest["source_sha256"] = source_hashes
    manifest["output_sha256"] = {
        name: _sha256(args.output / name)
        for name in (
            "trace.csv",
            "summary.json",
            "neural_trace_full_rate.npz",
            "neural_trace_schema.json",
        )
        if (args.output / name).exists()
    }
    _json_dump(manifest_path, manifest)
    return summary


def make_parser():
    parser = final_runner.make_parser()
    controller_action = next(
        action for action in parser._actions if action.dest == "controller"
    )
    controller_action.choices = CONTROLLERS
    parser.add_argument("--family-current-bias", type=float, default=None)
    parser.add_argument("--family-current-gain", type=float, default=None)
    parser.add_argument("--family-feature-tau", type=float, default=None)
    parser.add_argument("--family-feature-scale", type=float, default=None)
    parser.add_argument("--family-native-current-scale", type=float, default=None)
    parser.add_argument(
        "--family-learning-normalization",
        choices=("exact", "archived"),
        default="exact",
        help=(
            "exact gives every normalized decoder the requested direct eta; "
            "archived reproduces the older one-scale-factor implementation"
        ),
    )
    return parser


def _validate(args):
    final_runner._validate(args)
    for name in ("family_feature_tau", "family_feature_scale", "family_native_current_scale"):
        value = getattr(args, name)
        if value is not None and value <= 0.0:
            raise SystemExit(f"--{name.replace('_', '-')} must be positive")


if __name__ == "__main__":
    parsed = make_parser().parse_args()
    _validate(parsed)
    result = run(parsed)
    print(json.dumps(result, indent=2))

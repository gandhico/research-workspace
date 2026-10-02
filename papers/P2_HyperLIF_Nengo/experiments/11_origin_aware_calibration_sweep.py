"""Run priority tuning candidates across the Core-Nengo app smoke suite.

This experiment consumes ``11_full_tuning_candidate_matrix.csv`` and evaluates
the priority-1, core-parameter candidates from stages 0--2. The goal is to find
which HyperLIF / Adaptive HyperLIF settings are broadly usable across Nengo
apps, not merely good on one metric.

Outputs:

- ``12_origin_aware_calibration_sweep.csv``: one row per app x candidate.
- ``12_origin_aware_calibration_summary.csv``: one row per candidate with a
  multi-app robustness score.
- ``12_origin_aware_calibration_sweep.txt``: readable log.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import numpy as np

from _common import CSV_DIR, ensure_results, write_log
from simulation.metrics import write_rows

import nengo


STAGES = {"0_anchor", "1_origin_threshold", "2_origin_aware_calibration"}
INPUT_MATRIX = CSV_DIR / "11_full_tuning_candidate_matrix.csv"
OUTPUT_ROWS = CSV_DIR / "12_origin_aware_calibration_sweep.csv"
OUTPUT_SUMMARY = CSV_DIR / "12_origin_aware_calibration_summary.csv"


@dataclass(frozen=True)
class CandidateVariant:
    name: str
    family: str
    event_threshold: float | str
    make: object
    origin_policy: str = "baseline"
    v_reset: float | str = ""
    min_voltage: float | str = ""


def _load_core_sweep() -> ModuleType:
    path = Path(__file__).resolve().with_name("09_core_nengo_capability_sweep.py")
    spec = importlib.util.spec_from_file_location("core_nengo_capability_sweep", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_candidates() -> list[dict[str, str]]:
    with INPUT_MATRIX.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _as_float(value: str, default: float) -> float:
    value = str(value).strip()
    if not value or value.lower() == "native":
        return default
    return float(value)


def _as_event_threshold(value: str) -> float | str:
    value = str(value).strip()
    if value.lower() == "native":
        return "native"
    return float(value)


def _range(value: str, default: tuple[float, float]) -> tuple[float, float]:
    value = str(value).strip()
    if not value:
        return default
    if ".." not in value:
        x = float(value)
        return x, x
    lo, hi = value.split("..", 1)
    return float(lo), float(hi)


def _selected_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = []
    seen = set()
    for row in rows:
        key = row["candidate_id"]
        if key in seen:
            continue
        seen.add(key)
        if row["stage"] not in STAGES:
            continue
        if row["priority"] != "1":
            continue
        if row["implementation"] != "core_params":
            continue
        if row["family"] not in {"lif", "hyperlif", "adaptive"}:
            continue
        selected.append(row)
    return selected


def _make_ensemble_factory(candidate: dict[str, str]):
    max_lo, max_hi = _range(candidate["ensemble_max_rates"], (40.0, 120.0))
    int_lo, int_hi = _range(candidate["ensemble_intercepts"], (-0.5, 0.5))

    def ensemble(n_neurons: int, dimensions: int, neuron_type, seed: int):
        return nengo.Ensemble(
            n_neurons,
            dimensions,
            neuron_type=neuron_type,
            seed=seed,
            max_rates=nengo.dists.Uniform(max_lo, max_hi),
            intercepts=nengo.dists.Uniform(int_lo, int_hi),
        )

    return ensemble


def _make_variant(candidate: dict[str, str], core) -> CandidateVariant:
    family = candidate["family"]
    event_threshold = _as_event_threshold(candidate["theta_event"])

    if family == "lif":
        return CandidateVariant(
            name=candidate["candidate_id"],
            family="lif",
            event_threshold="native",
            make=lambda: nengo.LIF(),
            origin_policy="none",
            v_reset="",
            min_voltage="",
        )

    common = dict(
        event_threshold=float(event_threshold),
        v_reset=_as_float(candidate["v_reset"], 0.0),
        min_voltage=_as_float(candidate["min_voltage"], 0.0),
        alpha=_as_float(candidate["alpha"], 100.0),
        tau_r=_as_float(candidate["tau_r"], 0.002),
        gamma=_as_float(candidate["gamma"], 0.2),
        rate_to_current=_as_float(candidate["rate_to_current"], 80.0),
    )
    if family == "hyperlif":
        common["reset_gain"] = _as_float(candidate["reset_gain"], 100.0)
        maker = lambda common=common: core.FastReadoutHyperLIFNengo(**common)
    elif family == "adaptive":
        common["base_gain"] = _as_float(candidate["base_gain"], 20.0)
        common["gain_scaling"] = _as_float(candidate["gain_scaling"], 80.0)
        maker = lambda common=common: core.FastReadoutAdaptiveHyperLIFNengo(**common)
    else:  # pragma: no cover - guarded by selection.
        raise ValueError(f"Unsupported family: {family}")

    return CandidateVariant(
        name=candidate["candidate_id"],
        family=family,
        event_threshold=event_threshold,
        make=maker,
        origin_policy=candidate["origin_policy"],
        v_reset=candidate["v_reset"],
        min_voltage=candidate["min_voltage"],
    )


def _metric_penalty(row: dict[str, object], lif_by_app: dict[str, float]) -> float:
    app = str(row["app"])
    value = float(row["metric_value"])

    if not np.isfinite(value):
        return 1.0e6
    if app == "working_memory":
        return value / 0.30
    if app == "oscillator":
        lif_amp = max(lif_by_app.get(app, 0.5), 1.0e-6)
        return abs(value - lif_amp) / lif_amp
    denom = max(lif_by_app.get(app, value), 1.0e-6)
    return value / denom


def _summarize(rows: list[dict[str, object]], candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    lif_by_app = {
        str(row["app"]): float(row["metric_value"])
        for row in rows
        if row["candidate_id"] == "T001" and row["status"] == "ok"
    }

    rows_by_candidate: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        rows_by_candidate.setdefault(str(row["candidate_id"]), []).append(row)

    candidate_meta = {row["candidate_id"]: row for row in candidates}
    summary: list[dict[str, object]] = []
    for candidate_id, app_rows in rows_by_candidate.items():
        penalties = [_metric_penalty(row, lif_by_app) for row in app_rows if row["status"] == "ok"]
        fail_count = sum(1 for row in app_rows if row["status"] != "ok")
        bad_app_count = sum(1 for p in penalties if p > 2.0)
        mean_event_rate = float(np.nanmean([float(row["event_rate_hz"]) for row in app_rows]))
        robust_score = float(np.mean(penalties) + 10.0 * fail_count + 0.5 * bad_app_count)
        meta = candidate_meta[candidate_id]
        out = {
            "rank": 0,
            "candidate_id": candidate_id,
            "candidate": meta["candidate"],
            "family": meta["family"],
            "stage": meta["stage"],
            "theta_event": meta["theta_event"],
            "origin_policy": meta["origin_policy"],
            "v_reset": meta["v_reset"],
            "min_voltage": meta["min_voltage"],
            "rate_to_current": meta["rate_to_current"],
            "robust_score": robust_score,
            "mean_penalty": float(np.mean(penalties)),
            "bad_app_count": bad_app_count,
            "fail_count": fail_count,
            "mean_event_rate_hz": mean_event_rate,
        }
        for row in app_rows:
            app = str(row["app"])
            out[f"{app}_metric"] = row["metric_value"]
            out[f"{app}_event_rate_hz"] = row["event_rate_hz"]
            out[f"{app}_penalty"] = _metric_penalty(row, lif_by_app)
        summary.append(out)

    summary.sort(key=lambda row: (float(row["robust_score"]), int(row["bad_app_count"])))
    for rank, row in enumerate(summary, start=1):
        row["rank"] = rank
    return summary


def main() -> None:
    ensure_results()
    if not INPUT_MATRIX.exists():
        raise FileNotFoundError(
            f"{INPUT_MATRIX} does not exist. Run experiments/10_full_tuning_setup.py first."
        )

    all_candidates = _read_candidates()
    candidates = _selected_candidates(all_candidates)
    core = _load_core_sweep()

    rows: list[dict[str, object]] = []
    lines = [
        "Origin-aware calibration candidate sweep",
        f"Candidates: {len(candidates)}",
        f"Apps per candidate: {len(core.APPS)}",
        "",
    ]

    for candidate in candidates:
        core.ensemble = _make_ensemble_factory(candidate)
        variant = _make_variant(candidate, core)
        lines.append(f"{candidate['candidate_id']} | {candidate['candidate']} | {candidate['family']}")
        for app in core.APPS:
            row = core.run_app(app, variant)
            row.update(
                {
                    "candidate_id": candidate["candidate_id"],
                    "candidate": candidate["candidate"],
                    "stage": candidate["stage"],
                    "priority": candidate["priority"],
                    "origin_policy": candidate["origin_policy"],
                    "v_reset": candidate["v_reset"],
                    "min_voltage": candidate["min_voltage"],
                    "rate_to_current": candidate["rate_to_current"],
                    "reset_gain": candidate["reset_gain"],
                    "base_gain": candidate["base_gain"],
                    "gain_scaling": candidate["gain_scaling"],
                    "alpha": candidate["alpha"],
                    "tau_r": candidate["tau_r"],
                    "gamma": candidate["gamma"],
                    "ensemble_max_rates": candidate["ensemble_max_rates"],
                    "ensemble_intercepts": candidate["ensemble_intercepts"],
                    "synapse": candidate["synapse"],
                }
            )
            rows.append(row)
            lines.append(
                f"  {row['app']:24s} status={row['status']} "
                f"{row['metric_name']}={row['metric_value']} "
                f"event_rate_hz={row['event_rate_hz']}"
            )

    preferred = [
        "candidate_id",
        "candidate",
        "stage",
        "priority",
        "app",
        "variant",
        "family",
        "event_threshold",
        "origin_policy",
        "v_reset",
        "min_voltage",
        "rate_to_current",
        "reset_gain",
        "base_gain",
        "gain_scaling",
        "alpha",
        "tau_r",
        "gamma",
        "ensemble_max_rates",
        "ensemble_intercepts",
        "synapse",
        "status",
        "metric_name",
        "metric_value",
        "event_rate_hz",
        "held_value",
        "oscillator_std",
        "early_error_rmse",
        "late_error_rmse",
    ]
    all_keys = preferred + sorted({key for row in rows for key in row if key not in preferred})
    write_rows(OUTPUT_ROWS, [{key: row.get(key, "") for key in all_keys} for row in rows])

    summary = _summarize(rows, candidates)
    summary_keys = list(summary[0].keys()) if summary else []
    write_rows(OUTPUT_SUMMARY, [{key: row.get(key, "") for key in summary_keys} for row in summary])

    lines.extend(["", "Top candidates by robustness score:"])
    for row in summary[:10]:
        lines.append(
            f"  #{row['rank']:02d} {row['candidate_id']} | {row['candidate']} | "
            f"score={row['robust_score']:.3f} | bad_apps={row['bad_app_count']} | "
            f"mean_event_rate={row['mean_event_rate_hz']:.2f}"
        )
    write_log("12_origin_aware_calibration_sweep.txt", "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

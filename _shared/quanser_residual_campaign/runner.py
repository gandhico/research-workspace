"""Command-line runner for offline baseline vs HyperLIF residual benchmarks."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from .io_utils import write_csv, write_json
from .metrics import compare, summarize
from .platforms import get_platform_config
from .plotting import plot_comparison
from .simulation import simulate


def run_benchmark(
    platform: str,
    output_dir: Path,
    duration: float = 20.0,
    make_plots: bool = True,
) -> dict[str, Any]:
    config = get_platform_config(platform)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"{config.key}_{timestamp}"
    csv_dir = run_dir / "csv"
    fig_dir = run_dir / "figures"

    baseline = simulate(config, mode="baseline", duration=duration)
    residual = simulate(config, mode="residual", duration=duration)

    baseline_csv = csv_dir / f"{config.key}_baseline.csv"
    residual_csv = csv_dir / f"{config.key}_hyperlif_residual.csv"
    write_csv(baseline_csv, config, baseline)
    write_csv(residual_csv, config, residual)

    baseline_summary = summarize(config, baseline)
    residual_summary = summarize(config, residual)
    comparison = compare(baseline_summary, residual_summary)

    figure_path = None
    if make_plots:
        figure_path = fig_dir / f"{config.key}_baseline_vs_hyperlif_residual.png"
        plot_comparison(config, baseline, residual, figure_path)

    payload: dict[str, Any] = {
        "platform": config.key,
        "label": config.label,
        "description": config.description,
        "baseline_controller": config.baseline_name,
        "residual_controller": "baseline plus bounded Adaptive HyperLIF gate-state residual",
        "state_labels": list(config.state_labels),
        "control_labels": list(config.control_labels),
        "target_state_indices": list(config.target_state_indices),
        "safety_limits": config.safety_limits,
        "baseline": baseline_summary,
        "hyperlif_residual": residual_summary,
        "comparison": comparison,
        "artifacts": {
            "baseline_csv": str(baseline_csv),
            "residual_csv": str(residual_csv),
            "figure": str(figure_path) if figure_path is not None else None,
        },
        "interpretation_note": (
            "Offline simulation is a reproducibility and controller-wiring check. "
            "It should not be reported as hardware evidence until repeated on the physical platform."
        ),
    }
    summary_path = run_dir / "summary.json"
    write_json(summary_path, payload)
    payload["artifacts"]["summary_json"] = str(summary_path)
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Quanser baseline vs HyperLIF residual offline benchmark.")
    parser.add_argument("--platform", required=True, help="qcar, servo_pendulum, aero2, or qdrone")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--no-plots", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    payload = run_benchmark(
        platform=args.platform,
        output_dir=args.output_dir,
        duration=args.duration,
        make_plots=not args.no_plots,
    )
    comparison = payload["comparison"]
    print(f"Platform: {payload['label']}")
    print(f"Summary: {payload['artifacts']['summary_json']}")
    print(f"Baseline CSV: {payload['artifacts']['baseline_csv']}")
    print(f"Residual CSV: {payload['artifacts']['residual_csv']}")
    if payload["artifacts"]["figure"]:
        print(f"Figure: {payload['artifacts']['figure']}")
    print(
        "RMS error delta (%): "
        f"{float(comparison['rms_error_delta_percent']):+.2f}; "
        "control effort delta (%): "
        f"{float(comparison['control_effort_delta_percent']):+.2f}"
    )


if __name__ == "__main__":
    main()


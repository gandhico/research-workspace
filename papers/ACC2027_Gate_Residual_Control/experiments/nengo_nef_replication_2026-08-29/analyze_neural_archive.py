"""Validate, summarize, export, and plot a full-rate CMG/PES Nengo archive.

The tool is platform-neutral: it accepts archives produced by the MuJoCo
runner or by the Quanser 3DOF Hover Nengo GUI/HIL runner.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _schema_for(archive: Path) -> dict:
    candidate = archive.parent / "neural_trace_schema.json"
    return json.loads(candidate.read_text(encoding="utf-8")) if candidate.exists() else {}


def _labels(schema: dict, count: int, kind: str) -> list[str]:
    values = schema.get(kind, [])
    return [str(v) for v in values] if len(values) == count else [str(i) for i in range(count)]


def _flatten_columns(name: str, values: np.ndarray):
    if values.ndim == 1:
        return [(name, values)]
    flat = values.reshape(values.shape[0], -1)
    trailing = values.shape[1:]
    columns = []
    for j in range(flat.shape[1]):
        index = np.unravel_index(j, trailing)
        suffix = ",".join(str(i) for i in index)
        columns.append((f"{name}[{suffix}]", flat[:, j]))
    return columns


def export_csv(path: Path, arrays: dict[str, np.ndarray]) -> None:
    columns = []
    for name, values in arrays.items():
        columns.extend(_flatten_columns(name, values))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([name for name, _ in columns])
        for row in zip(*(values for _, values in columns)):
            writer.writerow(row)


def _plot_lines(ax, t, values, labels, *, linestyle="-", alpha=1.0):
    values = np.asarray(values)
    if values.ndim == 1:
        values = values[:, None]
    for i in range(values.shape[1]):
        ax.plot(t, values[:, i], linestyle=linestyle, alpha=alpha, lw=1.05, label=labels[i])


def make_figure(arrays: dict[str, np.ndarray], schema: dict, prefix: Path) -> None:
    # Hover names the controlled axis explicitly; MuJoCo uses the shorter
    # canonical names.  Normalize aliases only for plotting and preserve the
    # original archive keys in statistics/exports.
    target = arrays.get("target", arrays.get("target_ypr"))
    residual = arrays.get("residual_torque", arrays.get("residual_torque_ypr"))
    if target is None or residual is None:
        raise ValueError("archive must contain target[/_ypr] and residual_torque[/_ypr]")
    t = arrays["t"]
    stride = max(1, int(np.ceil(len(t) / 12000)))
    s = slice(None, None, stride)
    ts = t[s]
    unit_labels = _labels(schema, arrays["voltage"].shape[1], "unit_order")
    axis_labels = _labels(schema, target.shape[1], "axis_order")

    fig, axes = plt.subplots(4, 2, figsize=(15, 13), sharex=True, constrained_layout=True)
    ax = axes.ravel()

    _plot_lines(ax[0], ts, arrays["voltage"][s], unit_labels)
    ax[0].set_title("CMG membrane potential $v$")

    _plot_lines(ax[1], ts, arrays["gate"][s], unit_labels)
    _plot_lines(ax[1], ts, arrays["gate_target"][s], unit_labels, linestyle="--", alpha=0.55)
    ax[1].set_title("Gate $r$ (solid) and instantaneous target $r_\\infty$ (dashed)")

    _plot_lines(ax[2], ts, arrays["current"][s], unit_labels)
    ax[2].set_title("Paired input currents $J$")

    _plot_lines(ax[3], ts, arrays["conductance"][s], unit_labels)
    ax[3].set_title("Effective conductance $g(J)r^2$")

    _plot_lines(ax[4], ts, arrays["decoded_clipped"][s], axis_labels)
    _plot_lines(ax[4], ts, target[s], axis_labels, linestyle="--", alpha=0.65)
    ax[4].set_title("Clipped decoded residual (solid) and PES target (dashed)")

    _plot_lines(ax[5], ts, arrays["pes_error"][s], axis_labels)
    ax[5].axhline(0.0, color="black", lw=0.7)
    ax[5].set_title("PES error = clipped decoder - target")

    weights = arrays["weights"]
    row_norms = np.linalg.norm(weights, axis=2)
    _plot_lines(ax[6], ts, row_norms[s], axis_labels)
    ax[6].set_title("Online decoder row norms $\\|W_i\\|_2$")

    update_norms = np.linalg.norm(arrays["weight_delta"], axis=2)
    _plot_lines(ax[7], ts, update_norms[s], axis_labels)
    ax[7].set_title("Per-neural-step decoder update norms $\\|\\Delta W_i\\|_2$")

    for panel in ax:
        panel.grid(True, alpha=0.25)
        panel.set_xlabel("time [s]")
        panel.legend(loc="best", fontsize=7, ncol=2)
    fig.suptitle(f"Full-rate Nengo CMG/PES diagnostics ({schema.get('sample_rate_hz', 'unknown')} Hz)")
    fig.savefig(prefix.with_suffix(".png"), dpi=220)
    fig.savefig(prefix.with_suffix(".pdf"))
    plt.close(fig)

    fig, axes = plt.subplots(4, 2, figsize=(15, 13), sharex=True, constrained_layout=True)
    ax = axes.ravel()
    equation_panels = (
        ("activity", "Decoder activity $a=\\mathrm{clip}(k_r r,0,1)$", unit_labels),
        ("effective_threshold", "Effective threshold $v_{th}-\\gamma r$", unit_labels),
        ("gate_argument", "Sigmoid argument $\\alpha(v-v_{th}+\\gamma r)$", unit_labels),
        ("conductance_gain", "Current-dependent conductance gain", unit_labels),
        ("membrane_lambda", "Membrane decay rate $\\lambda$", unit_labels),
        ("membrane_drive", "Membrane drive term", unit_labels),
    )
    for panel, (name, title, labels) in zip(ax[:6], equation_panels):
        _plot_lines(panel, ts, arrays[name][s], labels)
        panel.set_title(title)
    _plot_lines(ax[6], ts, arrays["decoded_raw"][s], axis_labels)
    _plot_lines(ax[6], ts, arrays["decoded_clipped"][s], axis_labels, linestyle="--", alpha=0.7)
    ax[6].set_title("Raw decoder (solid) and safety-clipped decoder (dashed)")
    _plot_lines(ax[7], ts, residual[s], axis_labels)
    ax[7].set_title("Applied residual torque")
    for panel in ax:
        panel.grid(True, alpha=0.25)
        panel.set_xlabel("time [s]")
        panel.legend(loc="best", fontsize=7, ncol=2)
    fig.suptitle("CMG equation terms and residual reconstruction")
    dynamics_prefix = prefix.with_name(prefix.name + "_equation_terms")
    fig.savefig(dynamics_prefix.with_suffix(".png"), dpi=220)
    fig.savefig(dynamics_prefix.with_suffix(".pdf"))
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-prefix", type=Path)
    parser.add_argument("--export-csv", action="store_true", help="Also write a completely flattened CSV.")
    parser.add_argument("--export-mat", action="store_true", help="Also write a MATLAB .mat containing every signal.")
    args = parser.parse_args()

    archive = args.archive.resolve()
    prefix = (args.output_prefix or archive.with_name(archive.stem + "_diagnostics")).resolve()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    with np.load(archive, allow_pickle=False) as loaded:
        arrays = {name: loaded[name] for name in loaded.files}
    if "t" not in arrays or len(arrays["t"]) == 0:
        raise SystemExit("archive has no neural samples")
    count = len(arrays["t"])
    inconsistent = {name: list(value.shape) for name, value in arrays.items() if value.shape[0] != count}
    nonfinite = {name: int(np.size(value) - np.count_nonzero(np.isfinite(value))) for name, value in arrays.items()}
    nonfinite = {name: count for name, count in nonfinite.items() if count}
    if inconsistent or nonfinite:
        raise SystemExit(f"invalid archive: inconsistent={inconsistent}, nonfinite={nonfinite}")

    schema = _schema_for(archive)
    stats = {
        "archive": str(archive),
        "samples": count,
        "t_start_s": float(arrays["t"][0]),
        "t_end_s": float(arrays["t"][-1]),
        "sample_rate_hz_schema": schema.get("sample_rate_hz"),
        "signals": {
            name: {
                "shape": list(value.shape),
                "dtype": str(value.dtype),
                "min": float(np.min(value)),
                "max": float(np.max(value)),
                "mean": float(np.mean(value)),
                "rms": float(np.sqrt(np.mean(np.square(value.astype(float))))),
            }
            for name, value in arrays.items()
        },
    }
    stats_path = prefix.with_name(prefix.name + "_statistics.json")
    stats_path.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    make_figure(arrays, schema, prefix)
    if args.export_csv:
        export_csv(prefix.with_suffix(".csv"), arrays)
    if args.export_mat:
        from scipy.io import savemat

        savemat(prefix.with_suffix(".mat"), arrays, do_compression=True)
    print(json.dumps({
        "status": "passed",
        "samples": count,
        "signals": len(arrays),
        "png": str(prefix.with_suffix('.png')),
        "pdf": str(prefix.with_suffix('.pdf')),
        "statistics": str(stats_path),
        "equation_terms_png": str(prefix.with_name(prefix.name + '_equation_terms').with_suffix('.png')),
        "equation_terms_pdf": str(prefix.with_name(prefix.name + '_equation_terms').with_suffix('.pdf')),
        "csv": str(prefix.with_suffix('.csv')) if args.export_csv else None,
        "mat": str(prefix.with_suffix('.mat')) if args.export_mat else None,
    }, indent=2))


if __name__ == "__main__":
    main()

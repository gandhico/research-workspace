"""Plot the natural observable, native states, PES, and residual of one family run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def lines(ax, t, values, labels, **kwargs):
    values = np.asarray(values)
    if values.ndim == 1:
        values = values[:, None]
    for i in range(values.shape[1]):
        ax.plot(t, values[:, i], lw=1.0, label=labels[i], **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-prefix", type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    schema = json.loads((archive.parent / "neural_trace_schema.json").read_text(encoding="utf-8"))
    with np.load(archive, allow_pickle=False) as loaded:
        data = {name: loaded[name] for name in loaded.files}
    prefix = (args.output_prefix or archive.with_name(archive.stem + "_family")).resolve()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    t = data["t"]
    stride = max(1, int(np.ceil(len(t) / 15000)))
    s = slice(None, None, stride)
    units = schema.get("unit_order", [str(i) for i in range(6)])
    axes_labels = schema.get("axis_order", ["x", "y", "z"])
    family = schema.get("neuron_family", "cmg")
    mode = schema.get("decoder_mode", "pes")

    fig, panels = plt.subplots(4, 2, figsize=(15, 13), sharex=True, constrained_layout=True)
    ax = panels.ravel()
    lines(ax[0], t[s], data["current"][s], units)
    if "native_current" in data:
        lines(ax[0], t[s], data["native_current"][s], units, ls="--", alpha=0.55)
    ax[0].set_title("Canonical current (solid) and native-scaled current (dashed)")

    raw = data.get("raw_output")
    if raw is not None and family in ("lif", "alif", "izhikevich"):
        for unit in range(raw.shape[1]):
            event = np.flatnonzero(raw[:, unit] > 0)
            ax[1].scatter(t[event], np.full(len(event), unit), s=2, label=units[unit])
        ax[1].set_yticks(range(len(units)), units)
        ax[1].set_title("Native spike raster")
    elif raw is not None:
        lines(ax[1], t[s], raw[s], units)
        ax[1].set_title("Native neuron output")

    lines(ax[2], t[s], data["activity"][s], units)
    ax[2].set_title("Calibrated natural feature used by decoder")
    target = data.get("target", data.get("target_ypr"))
    residual = data.get("residual_torque", data.get("residual_torque_ypr"))
    lines(ax[3], t[s], data["decoded_clipped"][s], axes_labels)
    lines(ax[3], t[s], target[s], axes_labels, ls="--", alpha=0.65)
    ax[3].set_title("Decoded residual (solid) and PES target (dashed)")
    lines(ax[4], t[s], data["pes_error"][s], axes_labels)
    ax[4].axhline(0, color="black", lw=0.7)
    ax[4].set_title("PES error")
    lines(ax[5], t[s], np.linalg.norm(data["weights"], axis=2)[s], axes_labels)
    ax[5].set_title("Normalized decoder row norms")
    lines(ax[6], t[s], np.linalg.norm(data["weight_delta"], axis=2)[s], axes_labels)
    ax[6].set_title("Per-step normalized decoder update norms")
    lines(ax[7], t[s], residual[s], axes_labels)
    ax[7].set_title("Bounded residual torque")
    for panel in ax:
        panel.grid(True, alpha=0.25); panel.set_xlabel("time [s]")
        if panel is not ax[1] or family not in ("lif", "alif", "izhikevich"):
            panel.legend(loc="best", fontsize=7, ncol=2)
    fig.suptitle(f"Matched Nengo neuron-family diagnostics — {family}, {mode}")
    fig.savefig(prefix.with_suffix(".png"), dpi=240)
    fig.savefig(prefix.with_suffix(".pdf"))
    plt.close(fig)

    state_names = [
        name for name in data
        if name.startswith("state_") or name.startswith("native_")
    ]
    if state_names:
        fig, axes = plt.subplots(len(state_names), 1, figsize=(12, 3.3 * len(state_names)), sharex=True, constrained_layout=True)
        axes = np.atleast_1d(axes)
        for panel, name in zip(axes, state_names):
            lines(panel, t[s], data[name][s], units)
            panel.set_title(name.removeprefix("state_").removeprefix("native_").replace("_", " "))
            panel.grid(True, alpha=0.25); panel.legend(loc="best", fontsize=7, ncol=3)
        axes[-1].set_xlabel("time [s]")
        fig.suptitle(f"Native Nengo states — {family}")
        states = prefix.with_name(prefix.name + "_native_states")
        fig.savefig(states.with_suffix(".png"), dpi=240)
        fig.savefig(states.with_suffix(".pdf"))
        plt.close(fig)
    print(json.dumps({"family": family, "mode": mode, "samples": len(t), "output_prefix": str(prefix)}, indent=2))


if __name__ == "__main__":
    main()

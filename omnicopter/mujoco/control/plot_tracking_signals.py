"""Plot time-domain PD versus CMG-PES tracking from matched campaigns."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


COLORS = {"pd": "#2b6cb0", "cmg": "#dd6b20", "ref": "#1a202c", "res": "#805ad5"}
LABELS = {"pd": "PD", "cmg": "CMG-PES canónico", "ref": "Referencia"}
MISSIONS = ("hover", "hover_push", "circle_yaw_push", "yaw_360_6s")
KICKS = {"hover_push": 4., "circle_yaw_push": 22.}


def load(path):
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    numeric = {}
    for key in rows[0]:
        try:
            numeric[key] = np.asarray([float(row[key]) for row in rows])
        except ValueError:
            pass
    return numeric


def style(axis, ylabel, kick=None):
    axis.set_ylabel(ylabel)
    axis.grid(True, alpha=.25)
    axis.spines[["top", "right"]].set_visible(False)
    if kick is not None:
        axis.axvline(kick, color="#c53030", linestyle=":", linewidth=1.3)


def change_text(baseline, candidate, numerical_floor):
    if baseline < numerical_floor:
        return "n/a"
    return f"{100*(baseline-candidate)/baseline:+.1f}%"


def plot_position(axis, pd, cmg, coordinate, kick):
    t = pd["time_s"]
    axis.plot(t, pd[f"ref_{coordinate}_m"], "--", color=COLORS["ref"],
              linewidth=1.5, label=LABELS["ref"])
    axis.plot(t, pd[f"{coordinate}_m"], color=COLORS["pd"], linewidth=1.2,
              label=LABELS["pd"])
    axis.plot(cmg["time_s"], cmg[f"{coordinate}_m"], color=COLORS["cmg"],
              linewidth=1.2, label=LABELS["cmg"])
    style(axis, f"{coordinate.upper()} [m]", kick)


def plot_mission(pd, cmg, mission, output):
    fig, axes = plt.subplots(3, 2, figsize=(13, 10), sharex=False)
    kick = KICKS.get(mission)
    if mission.startswith("yaw_"):
        ax = axes[0, 0]
        ax.plot(pd["time_s"], pd["reference_rotation_deg"], "--",
                color=COLORS["ref"], linewidth=1.5, label=LABELS["ref"])
        ax.plot(pd["time_s"], pd["actual_rotation_progress_deg"],
                color=COLORS["pd"], linewidth=1.2, label=LABELS["pd"])
        ax.plot(cmg["time_s"], cmg["actual_rotation_progress_deg"],
                color=COLORS["cmg"], linewidth=1.2, label=LABELS["cmg"])
        style(ax, "Progreso de yaw [°]", kick)
        plot_position(axes[0, 1], pd, cmg, "z", kick)
        plot_position(axes[1, 0], pd, cmg, "x", kick)
        plot_position(axes[1, 1], pd, cmg, "y", kick)
    elif mission == "circle_yaw_push":
        ax = axes[0, 0]
        ax.plot(pd["ref_x_m"], pd["ref_y_m"], "--", color=COLORS["ref"],
                linewidth=1.5, label=LABELS["ref"])
        ax.plot(pd["x_m"], pd["y_m"], color=COLORS["pd"], linewidth=1.2,
                label=LABELS["pd"])
        ax.plot(cmg["x_m"], cmg["y_m"], color=COLORS["cmg"], linewidth=1.2,
                label=LABELS["cmg"])
        ax.set_xlabel("X [m]"); style(ax, "Y [m]")
        ax.axis("equal")
        ax = axes[0, 1]
        ax.plot(pd["time_s"], pd["reference_rotation_deg"], "--",
                color=COLORS["ref"], linewidth=1.5, label=LABELS["ref"])
        ax.plot(pd["time_s"], pd["actual_rotation_progress_deg"],
                color=COLORS["pd"], linewidth=1.2, label=LABELS["pd"])
        ax.plot(cmg["time_s"], cmg["actual_rotation_progress_deg"],
                color=COLORS["cmg"], linewidth=1.2, label=LABELS["cmg"])
        style(ax, "Progreso de yaw [°]", kick)
        plot_position(axes[1, 0], pd, cmg, "x", kick)
        plot_position(axes[1, 1], pd, cmg, "y", kick)
    else:
        plot_position(axes[0, 0], pd, cmg, "x", kick)
        plot_position(axes[0, 1], pd, cmg, "y", kick)
        plot_position(axes[1, 0], pd, cmg, "z", kick)
        ax = axes[1, 1]
        ax.plot(pd["time_s"], pd["speed_com_m_s"], color=COLORS["pd"],
                linewidth=1.2, label=LABELS["pd"])
        ax.plot(cmg["time_s"], cmg["speed_com_m_s"], color=COLORS["cmg"],
                linewidth=1.2, label=LABELS["cmg"])
        style(ax, "Rapidez COM [m/s]", kick)

    ax = axes[2, 0]
    ax.plot(pd["time_s"], pd["position_error_m"], color=COLORS["pd"],
            linewidth=1.2, label=LABELS["pd"])
    ax.plot(cmg["time_s"], cmg["position_error_m"], color=COLORS["cmg"],
            linewidth=1.2, label=LABELS["cmg"])
    style(ax, "Error de posición [m]", kick); ax.set_xlabel("Tiempo [s]")
    ax = axes[2, 1]
    ax.plot(pd["time_s"], pd["attitude_error_deg"], color=COLORS["pd"],
            linewidth=1.2, label=LABELS["pd"])
    ax.plot(cmg["time_s"], cmg["attitude_error_deg"], color=COLORS["cmg"],
            linewidth=1.2, label=LABELS["cmg"])
    style(ax, "Error de actitud [°]", kick); ax.set_xlabel("Tiempo [s]")

    handles, labels = axes[0, 0].get_legend_handles_labels()
    if kick is not None:
        handles.append(plt.Line2D([0], [0], color="#c53030", linestyle=":"))
        labels.append("Impulso")
    fig.suptitle(f"Omnicóptero — {mission}: seguimiento PD vs CMG-PES canónico", y=.985)
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .955),
               ncols=len(labels), frameon=False)
    fig.subplots_adjust(top=.90, hspace=.25, wspace=.18)
    fig.savefig(output/f"{mission}_tracking.png", dpi=180)
    plt.close(fig)

    # Dedicated controller-action figure keeps scales readable.
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True, constrained_layout=True)
    for data, label, color in ((pd, "PD", COLORS["pd"]),
                               (cmg, "CMG-PES canónico", COLORS["cmg"])):
        motors = np.column_stack([data[f"thrust_{i}_N"] for i in range(1, 9)])
        axes[0].plot(data["time_s"], np.max(np.abs(motors), axis=1),
                     color=color, linewidth=1.2, label=label)
    axes[1].plot(cmg["time_s"], cmg.get("pes_residual_norm", np.zeros_like(cmg["time_s"])),
                 color=COLORS["res"], linewidth=1.2, label="Norma residual CMG-PES canónico")
    style(axes[0], "Máx. |empuje rotor| [N]", kick)
    style(axes[1], "Norma del wrench residual", kick); axes[1].set_xlabel("Tiempo [s]")
    axes[0].legend(frameon=False); axes[1].legend(frameon=False)
    fig.suptitle(f"Omnicóptero — {mission}: autoridad y acción residual")
    fig.savefig(output/f"{mission}_control.png", dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pd_campaign", type=Path)
    parser.add_argument("cmg_campaign", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    summary_rows = []
    for mission in MISSIONS:
        pd = load(args.pd_campaign/mission/"trace.csv")
        cmg = load(args.cmg_campaign/mission/"trace.csv")
        plot_mission(pd, cmg, mission, args.output)
        start = KICKS.get(mission, 0.)
        for name, data in (("PD", pd), ("CMG-PES canónico", cmg)):
            keep = data["time_s"] >= start
            summary_rows.append({
                "mission": mission, "window_start_s": start, "controller": name,
                "position_RMSE_m": float(np.sqrt(np.mean(data["position_error_m"][keep]**2))),
                "attitude_RMSE_deg": float(np.sqrt(np.mean(data["attitude_error_deg"][keep]**2))),
                "peak_position_error_m": float(np.max(data["position_error_m"][keep])),
                "peak_attitude_error_deg": float(np.max(data["attitude_error_deg"][keep])),
            })
        print(mission)
    with (args.output/"window_metrics.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=summary_rows[0].keys())
        writer.writeheader(); writer.writerows(summary_rows)
    rows = {(row["mission"], row["controller"]): row for row in summary_rows}
    lines = ["# Señales de seguimiento PD vs CMG-PES canónico", "",
             "Las ventanas de las misiones con impulso comienzan en el instante del impulso; "
             "las demás usan la misión completa.", "",
             "| Misión/ventana | Posición PD [m] | Posición CMG [m] | Cambio | Actitud PD [°] | Actitud CMG [°] | Cambio |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for mission in MISSIONS:
        pd, cmg = rows[(mission, "PD")], rows[(mission, "CMG-PES canónico")]
        pchange = change_text(pd["position_RMSE_m"], cmg["position_RMSE_m"], 1e-6)
        achange = change_text(pd["attitude_RMSE_deg"], cmg["attitude_RMSE_deg"], 1e-6)
        window = f"desde {pd['window_start_s']:.0f} s" if pd["window_start_s"] else "completa"
        lines.append(f"| `{mission}` ({window}) | {pd['position_RMSE_m']:.6f} | "
                     f"{cmg['position_RMSE_m']:.6f} | {pchange} | "
                     f"{pd['attitude_RMSE_deg']:.4f} | {cmg['attitude_RMSE_deg']:.4f} | {achange} |")
    lines += ["", "Un cambio positivo significa reducción de error con CMG-PES canónico; uno negativo, "
              "degradación. `n/a` indica que el error PD está por debajo del piso numérico elegido, "
              "por lo que un cociente porcentual sería engañoso."]
    (args.output/"REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()

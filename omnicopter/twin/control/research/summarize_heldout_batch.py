"""Merge independent Omnicopter held-out runs into an auditable batch report."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


LABELS = {
    "pd": "PD + feedforward",
    "legacy_12": "CMG-PES actual (12)",
    "cmg_12": "CMG-PES revisado (12)",
}
ORDER = tuple(LABELS)
MISSION_TEXT = {
    "hover_push": "Hover con impulso de velocidad a los 4 s; mide rechazo y recuperación.",
    "attitude_x_45": "Giro +45° alrededor de X, mantenimiento y retorno; mide reorientación grande.",
    "yaw_360_6s": "Giro completo de yaw en 6 s; mide seguimiento rápido y límites de actuación.",
}


def mean_std(values):
    values = np.asarray(values, dtype=float)
    return float(np.mean(values)), float(np.std(values, ddof=1 if len(values) > 1 else 0))


def summarize(rows, keys):
    grouped = {}
    for row in rows:
        key = tuple(row[name] for name in keys)
        grouped.setdefault(key, []).append(row)
    result = []
    for key, group in grouped.items():
        pos_mean, pos_std = mean_std([r["position_RMSE_m"] for r in group])
        att_mean, att_std = mean_std([r["attitude_RMSE_deg"] for r in group])
        item = dict(zip(keys, key))
        item.update({
            "runs": len(group),
            # Historical runner called this pass. It only certifies completion,
            # no contact and no non-finite/height failure, not tracking quality.
            "safe_completions": sum(r["status"] == "pass" for r in group),
            "position_RMSE_mean_m": pos_mean,
            "position_RMSE_std_m": pos_std,
            "attitude_RMSE_mean_deg": att_mean,
            "attitude_RMSE_std_deg": att_std,
            "worst_peak_position_m": max(r["peak_position_error_m"] for r in group),
            "worst_peak_attitude_deg": max(r["peak_attitude_error_deg"] for r in group),
            "max_saturation_fraction": max(r["saturation_fraction"] for r in group),
            "runs_with_saturation": sum(r["saturation_fraction"] > 0 for r in group),
        })
        result.append(item)
    return result


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def reduction(new, old):
    return 100.0 * (old - new) / old


def paired_wins(rows, challenger, reference, metric):
    lookup = {(r["controller"], r["seed"], r["mission"]): r for r in rows}
    cases = sorted((r["seed"], r["mission"]) for r in rows if r["controller"] == challenger)
    wins = sum(lookup[(challenger, *case)][metric] < lookup[(reference, *case)][metric]
               for case in cases)
    return wins, len(cases)


def make_plot(path, mission_summary, overall):
    missions = list(MISSION_TEXT)
    controllers = list(ORDER)
    colors = ["#718096", "#d69e2e", "#2b6cb0"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    x = np.arange(len(missions) + 1)
    width = .24
    for index, controller in enumerate(controllers):
        rows = {(r["mission"], r["controller"]): r for r in mission_summary}
        aggregate = next(r for r in overall if r["controller"] == controller)
        pos = [rows[(mission, controller)]["position_RMSE_mean_m"] for mission in missions]
        att = [rows[(mission, controller)]["attitude_RMSE_mean_deg"] for mission in missions]
        pos.append(aggregate["position_RMSE_mean_m"])
        att.append(aggregate["attitude_RMSE_mean_deg"])
        offset = (index - 1) * width
        axes[0].bar(x + offset, pos, width, color=colors[index], label=LABELS[controller])
        axes[1].bar(x + offset, att, width, color=colors[index], label=LABELS[controller])
    labels = ["Hover +\nimpulso", "Actitud\nX +45°", "Yaw 360°\nen 6 s", "Promedio\nglobal"]
    for axis, ylabel in zip(axes, ("RMSE de posición [m]", "RMSE de actitud [°]")):
        axis.set_xticks(x, labels)
        axis.set_ylabel(ylabel)
        axis.grid(axis="y", alpha=.25)
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, ncols=1)
    fig.suptitle("Omnicóptero: lote retenido, 3 semillas × 3 misiones, 500 Hz")
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)

    rows, configs = [], []
    for source in args.inputs:
        rows.extend(json.loads((source / "runs.json").read_text(encoding="utf-8")))
        configs.append(json.loads((source / "config.json").read_text(encoding="utf-8")))
    invariant_fields = ("model_sha256", "hover_sha256", "missions_sha256",
                        "research_controller_sha256", "learning_rate_per_s", "beta",
                        "screening_timestep_s", "nominal_plant")
    for field in invariant_fields:
        if len({json.dumps(config[field], sort_keys=True) for config in configs}) != 1:
            raise ValueError(f"Input batches differ in {field}")
    if set(r["controller"] for r in rows) != set(ORDER):
        raise ValueError("Expected exactly PD, legacy_12 and cmg_12")

    mission_summary = summarize(rows, ("mission", "controller"))
    overall = summarize(rows, ("controller",))
    mission_summary.sort(key=lambda r: (list(MISSION_TEXT).index(r["mission"]),
                                        ORDER.index(r["controller"])))
    overall.sort(key=lambda r: ORDER.index(r["controller"]))
    write_csv(args.output / "runs.csv", rows)
    write_csv(args.output / "mission_results.csv", mission_summary)
    write_csv(args.output / "controller_results.csv", overall)

    lookup = {r["controller"]: r for r in overall}
    revised = lookup["cmg_12"]
    comparisons = {}
    for reference in ("pd", "legacy_12"):
        ref = lookup[reference]
        comparisons[reference] = {
            "position_RMSE_reduction_percent": reduction(
                revised["position_RMSE_mean_m"], ref["position_RMSE_mean_m"]),
            "attitude_RMSE_reduction_percent": reduction(
                revised["attitude_RMSE_mean_deg"], ref["attitude_RMSE_mean_deg"]),
            "position_paired_wins": paired_wins(rows, "cmg_12", reference, "position_RMSE_m"),
            "attitude_paired_wins": paired_wins(rows, "cmg_12", reference, "attitude_RMSE_deg"),
        }
    metadata = {
        "sources": [str(path.resolve()) for path in args.inputs],
        "seeds": sorted({r["seed"] for r in rows}),
        "missions": list(MISSION_TEXT),
        "controllers": list(ORDER),
        "invariants": {field: configs[0][field] for field in invariant_fields},
        "comparisons": comparisons,
        "interpretation": "safe_completions is not a tracking acceptance gate",
    }
    (args.output / "batch.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    make_plot(args.output / "heldout_comparison.png", mission_summary, overall)

    lines = [
        "# Lote retenido CMG-PES del omnicóptero", "",
        "Fecha: 2026-09-10. Simulación MuJoCo a 500 Hz; semillas retenidas 10, 11 y 12.", "",
        "Este lote usa incertidumbre sintética de masa, inercia, ganancia/retardo de motor y "
        "fuerza/par externo. No representa todavía aerodinámica identificada ni validación de hardware.", "",
        "## Misiones", "",
        "| Misión | Propósito | Duración | Repeticiones por controlador |", "|---|---|---:|---:|",
        f"| `hover_push` | {MISSION_TEXT['hover_push']} | 20 s | 3 |",
        f"| `attitude_x_45` | {MISSION_TEXT['attitude_x_45']} | 28 s | 3 |",
        f"| `yaw_360_6s` | {MISSION_TEXT['yaw_360_6s']} | 16 s | 3 |", "",
        "## Resultado por misión", "",
        "Valores: media ± desviación estándar entre semillas.", "",
        "| Misión | Controlador | Posición RMSE [m] | Actitud RMSE [°] | Completadas | Saturación máxima |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in mission_summary:
        lines.append(
            f"| `{row['mission']}` | {LABELS[row['controller']]} | "
            f"{row['position_RMSE_mean_m']:.4f} ± {row['position_RMSE_std_m']:.4f} | "
            f"{row['attitude_RMSE_mean_deg']:.3f} ± {row['attitude_RMSE_std_deg']:.3f} | "
            f"{row['safe_completions']}/{row['runs']} | {100*row['max_saturation_fraction']:.1f}% |")
    lines += ["", "## Resultado global", "",
              "| Controlador | Posición RMSE [m] | Actitud RMSE [°] | Completadas | Casos con saturación |",
              "|---|---:|---:|---:|---:|"]
    for row in overall:
        lines.append(
            f"| {LABELS[row['controller']]} | {row['position_RMSE_mean_m']:.4f} ± "
            f"{row['position_RMSE_std_m']:.4f} | {row['attitude_RMSE_mean_deg']:.3f} ± "
            f"{row['attitude_RMSE_std_deg']:.3f} | {row['safe_completions']}/{row['runs']} | "
            f"{row['runs_with_saturation']}/{row['runs']} |")
    pd_cmp, legacy_cmp = comparisons["pd"], comparisons["legacy_12"]
    legacy_position_text = (
        f"reduce posición en {legacy_cmp['position_RMSE_reduction_percent']:.1f}%"
        if legacy_cmp["position_RMSE_reduction_percent"] >= 0
        else f"aumenta posición en {-legacy_cmp['position_RMSE_reduction_percent']:.1f}%")
    lines += ["", "## Lectura", "",
              f"- Frente al PD, el CMG-PES revisado reduce el RMSE medio global de posición en "
              f"{pd_cmp['position_RMSE_reduction_percent']:.1f}% y el de actitud en "
              f"{pd_cmp['attitude_RMSE_reduction_percent']:.1f}%.",
              f"- Frente al CMG-PES actual, {legacy_position_text} y reduce actitud en "
              f"{legacy_cmp['attitude_RMSE_reduction_percent']:.1f}%.",
              f"- Gana frente al PD en {pd_cmp['position_paired_wins'][0]}/9 casos de posición y "
              f"{pd_cmp['attitude_paired_wins'][0]}/9 de actitud.",
              f"- Gana frente al CMG-PES actual en {legacy_cmp['position_paired_wins'][0]}/9 casos "
              f"de posición y {legacy_cmp['attitude_paired_wins'][0]}/9 de actitud.",
              "- Excepción importante: en semilla 10, `attitude_x_45`, el CMG-PES revisado fue peor "
              "que el actual; el PD y ambos residuales alcanzaron saturación. Esto apunta a introducir "
              "anti-windup/aprendizaje condicionado por autoridad antes de aumentar neuronas.", "",
              "> **Definición de completada:** sin caída por altura, contacto ni valores no finitos. "
              "No significa que haya aprobado los umbrales nominales de seguimiento.", "",
              "La conclusión es preliminar: tres semillas retenidas permiten detectar tendencias y "
              "fallos, pero no sostienen todavía una afirmación estadística ni una conclusión de vuelo."]
    (args.output / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()

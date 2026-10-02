"""Create a matched four-controller Omnicopter campaign comparison."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ORDER = ("pd", "cmg-pes", "nengo-pd", "nengo-cmg-pes")
LABELS = {
    "pd": "PD directo", "cmg-pes": "CMG-PES canónico directo",
    "nengo-pd": "Nengo-PD", "nengo-cmg-pes": "Nengo-CMG-PES canónico",
}
METRICS = ("position_RMSE_m", "attitude_RMSE_deg", "max_abs_input_N",
           "saturation_fraction")


def load(path):
    path = path.resolve()
    return (path, json.loads((path/"manifest.json").read_text(encoding="utf-8")),
            json.loads((path/"campaign.json").read_text(encoding="utf-8")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaigns", nargs=4, type=Path,
                        help="PD CMG-PES Nengo-PD Nengo-CMG-PES directories")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    loaded = [load(path) for path in args.campaigns]
    controllers = [manifest["controller"] for _, manifest, _ in loaded]
    if controllers != list(ORDER):
        raise ValueError(f"Expected controller order {ORDER}; received {controllers}")
    names = [[row["name"] for row in results] for _, _, results in loaded]
    if any(candidate != names[0] for candidate in names[1:]):
        raise ValueError("Mission lists or order differ")
    for field in ("model_xml_sha256", "mesh_sha256", "hover_py_sha256",
                  "gains", "gates", "selected_missions", "rotation_convention"):
        values = [json.dumps(manifest[field], sort_keys=True) for _, manifest, _ in loaded]
        if len(set(values)) != 1:
            raise ValueError(f"Provenance mismatch: {field}")
    args.output.mkdir(parents=True, exist_ok=False)
    lookup = {manifest["controller"]: {r["name"]: r for r in results}
              for _, manifest, results in loaded}
    rows = []
    for mission in names[0]:
        for controller in ORDER:
            source = lookup[controller][mission]
            rows.append({"mission": mission, "controller": controller,
                         "status": source["status"],
                         **{metric: source.get(metric) for metric in METRICS}})
    with (args.output/"comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    aggregate = []
    for controller in ORDER:
        group = [r for r in rows if r["controller"] == controller]
        aggregate.append({"controller": controller, "passed": sum(r["status"] == "pass" for r in group),
                          "runs": len(group), **{f"mean_{metric}": float(np.mean(
                              [r[metric] for r in group])) for metric in METRICS}})
    (args.output/"aggregate.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    equivalence = {}
    for direct, nengo_name in (("pd", "nengo-pd"), ("cmg-pes", "nengo-cmg-pes")):
        equivalence[f"{direct}_vs_{nengo_name}"] = {
            metric: float(max(abs(lookup[direct][mission][metric]
                                  - lookup[nengo_name][mission][metric])
                              for mission in names[0]))
            for metric in METRICS
        }
    (args.output/"backend_equivalence.json").write_text(
        json.dumps(equivalence, indent=2)+"\n", encoding="utf-8")
    mission_hashes = {manifest["controller"]: manifest["missions_py_sha256"]
                      for _, manifest, _ in loaded}
    (args.output/"provenance.json").write_text(json.dumps({
        "campaigns": {manifest["controller"]: str(path)
                      for path, manifest, _ in loaded},
        "missions_py_sha256": mission_hashes,
        "mission_source_hashes_match": len(set(mission_hashes.values())) == 1,
        "matched_invariants": ["model XML", "mesh", "hover controller", "gains",
                               "gates", "mission definitions", "rotation convention"],
    }, indent=2)+"\n", encoding="utf-8")
    x, width = np.arange(len(names[0])), .2
    fig, axes = plt.subplots(2, 1, figsize=(15, 9), sharex=True, constrained_layout=True)
    for index, controller in enumerate(ORDER):
        group = [r for r in rows if r["controller"] == controller]
        for axis, metric in zip(axes, ("position_RMSE_m", "attitude_RMSE_deg")):
            axis.bar(x+(index-1.5)*width, [r[metric] for r in group], width,
                     label=LABELS[controller])
    axes[0].set_ylabel("RMSE posición [m]"); axes[1].set_ylabel("RMSE actitud [°]")
    axes[1].set_xticks(x, names[0], rotation=65, ha="right")
    for axis in axes: axis.grid(axis="y", alpha=.25)
    axes[0].legend(ncols=2, frameon=False)
    fig.suptitle("Campaña pareada de cuatro controladores del omnicóptero")
    fig.savefig(args.output/"comparison.png", dpi=180); plt.close(fig)
    lines = ["# Comparación pareada de cuatro controladores", "",
             "| Controlador | Misiones aprobadas | RMSE posición media [m] | RMSE actitud media [°] | Saturación media |",
             "|---|---:|---:|---:|---:|"]
    for row in aggregate:
        lines.append(f"| {LABELS[row['controller']]} | {row['passed']}/{row['runs']} | "
                     f"{row['mean_position_RMSE_m']:.6f} | {row['mean_attitude_RMSE_deg']:.4f} | "
                     f"{100*row['mean_saturation_fraction']:.3f}% |")
    lines += ["", "## Conformidad de backend", "",
              "| Par | Máx. Δ RMSE posición [m] | Máx. Δ RMSE actitud [°] | Máx. Δ pico motor [N] |",
              "|---|---:|---:|---:|"]
    for pair, value in equivalence.items():
        lines.append(f"| `{pair}` | {value['position_RMSE_m']:.3e} | "
                     f"{value['attitude_RMSE_deg']:.3e} | {value['max_abs_input_N']:.3e} |")
    lines += ["", "PD/Nengo-PD y CMG-PES canónico/Nengo-CMG-PES son pares de conformidad "
              "entre backends. El beneficio del controlador debe evaluarse comparando PD con CMG-PES; "
              "no se deduce de la equivalencia entre backends.",
              "", "## Límite de interpretación", "",
              "Esta tabla corresponde a una campaña nominal con coincidencia exacta entre modelo y planta; "
              "no constituye una clasificación universal de controladores. La media agregada incluye el "
              "transitorio de arranque del CMG-PES canónico. El rechazo de perturbaciones debe informarse "
              "en una ventana posterior a la perturbación, y la robustez ante incertidumbre de planta debe "
              "evaluarse con la campaña *held-out* de semillas. La arquitectura de investigación revisada, "
              "centrada en el equilibrio, no forma parte de las cuatro variantes de esta tabla."]
    if len(set(mission_hashes.values())) != 1:
        lines += ["", "> **Provenance note:** the Nengo runs began before a telemetry-only "
                  "addition (body rates and simulated sensor fields) to `missions.py`; therefore "
                  "their mission-source hash differs from the two direct runs. Model, controller "
                  "core, gains, gates and serialized mission definitions match. This batch is an "
                  "engineering conformance result; rerun all four after the code freeze for the "
                  "publication release."]
    (args.output/"REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()

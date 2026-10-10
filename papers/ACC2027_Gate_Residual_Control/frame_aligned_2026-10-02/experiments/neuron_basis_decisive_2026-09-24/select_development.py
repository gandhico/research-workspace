"""Select one preregistered operating point per conventional neuron family."""
from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEV = HERE / "results" / "development"
DEV_BASELINE = HERE / "results" / "development_baseline"
OUT = HERE / "analysis" / "development"
FAMILIES = ("lif", "alif", "lifrate", "izhikevich")
MISSIONS = ("roll", "hard45")
TAG_RE = re.compile(r"b(?P<b>\d+p\d+)_g(?P<g>\d+p\d+)_tau(?P<t>\d+p\d+)")


def parse_tag(tag):
    match = TAG_RE.fullmatch(tag)
    if match is None:
        raise ValueError(tag)
    return {name: float(value.replace("p", ".")) for name, value in match.groupdict().items()}


def gmean(values):
    return math.exp(sum(math.log(v) for v in values) / len(values))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = {}
    for mission in MISSIONS:
        path = DEV_BASELINE / mission / "classical" / "summary.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        baseline[mission] = value["metrics"]["qerr_true_mean_rad"]

    grouped = defaultdict(dict)
    for path in DEV.rglob("summary.json"):
        summary = json.loads(path.read_text(encoding="utf-8"))
        family = summary["controller"]
        tag = path.parents[1].name
        grouped[(family, tag)][summary["mission"]] = summary

    rows = []
    selected = {}
    for (family, tag), by_mission in grouped.items():
        if set(by_mission) != set(MISSIONS):
            continue
        params = parse_tag(tag)
        ratios = [
            by_mission[m]["metrics"]["qerr_true_mean_rad"] / baseline[m]
            for m in MISSIONS
        ]
        efforts = [
            by_mission[m]["metrics"]["gated_residual_normalized_rms"]
            for m in MISSIONS
        ]
        admissible = all(r <= 10.0 for r in ratios)
        score = gmean(ratios) * (1.0 + sum(efforts) / len(efforts))
        row = {
            "family": family,
            "tag": tag,
            "current_bias": params["b"],
            "current_gain": params["g"],
            "feature_tau_s": params["t"],
            "roll_ratio": ratios[0],
            "hard45_ratio": ratios[1],
            "geomean_ratio": gmean(ratios),
            "mean_residual_nrms": sum(efforts) / len(efforts),
            "score": score,
            "admissible": admissible,
        }
        rows.append(row)

    for family in FAMILIES:
        choices = [r for r in rows if r["family"] == family and r["admissible"]]
        if not choices:
            raise SystemExit(f"No admissible candidate for {family}")
        best = min(choices, key=lambda r: (r["score"], r["tag"]))
        selected[family] = best

    rows.sort(key=lambda r: (r["family"], r["score"]))
    with (OUT / "development_candidates.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "selected_settings.json").write_text(
        json.dumps(selected, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Threshold-aware development selection",
        "",
        "Selected on the preregistered 15 s X2 Roll + Hard45 screen. Lower score is better. These settings must be confirmed at 45 s and then frozen for all held-out cases.",
        "",
        "| Family | Bias | Gain | Filter | Roll ratio | Hard45 ratio | Effort | Score |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for family in FAMILIES:
        item = selected[family]
        lines.append(
            f"| {family} | {item['current_bias']:.2f} | {item['current_gain']:.2f} | {1000*item['feature_tau_s']:.0f} ms | {item['roll_ratio']:.3f} | {item['hard45_ratio']:.3f} | {item['mean_residual_nrms']:.3f} | {item['score']:.3f} |"
        )
    (OUT / "DEVELOPMENT_SELECTION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(selected, indent=2))


if __name__ == "__main__":
    main()

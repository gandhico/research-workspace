"""Audit final P1 shortlist statistics from existing per-seed registries.

This script does not rerun experiments. It reads the completed P1 registries,
selects the best readout per neuron within each scope, and writes:

* summary statistics with failure counts
* paired comparison statistics by seed
* a Markdown decision note for manuscript claim discipline
"""

from __future__ import annotations

import argparse
import csv
import itertools
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev
from typing import Iterable

try:
    from scipy import stats as scipy_stats
except Exception:  # pragma: no cover - optional runtime dependency
    scipy_stats = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRIAGE = Path(r"C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage")
DEFAULT_OUT = ROOT / "results" / "final_stats"


@dataclass(frozen=True)
class RegistrySpec:
    scope: str
    role: str
    path: Path
    allowed_archs: tuple[str, ...] | None = None
    allowed_neurons: tuple[str, ...] | None = None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--triage-root", type=Path, default=DEFAULT_TRIAGE)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--tag", default="20260719")
    return p.parse_args()


def as_float(value: str) -> float:
    if value is None or value == "":
        return math.nan
    return float(value)


def as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def read_registry(spec: RegistrySpec) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with spec.path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            arch = row.get("arch") or "ff"
            neuron = row.get("neuron") or ""
            if spec.allowed_archs is not None and arch not in spec.allowed_archs:
                continue
            if spec.allowed_neurons is not None and neuron not in spec.allowed_neurons:
                continue
            parsed: dict[str, object] = dict(row)
            parsed["scope"] = spec.scope
            parsed["role"] = spec.role
            parsed["seed"] = int(row["seed"])
            parsed["arch"] = arch
            for key in ["accuracy", "macro_f1", "events_per_sample", "gate_mean", "wall_s"]:
                parsed[key] = as_float(row.get(key, ""))
            parsed["stable"] = as_bool(row.get("stable", ""))
            parsed["nan_batches"] = int(float(row.get("nan_batches", 0) or 0))
            rows.append(parsed)
    return rows


def selected_best_readouts(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = (str(row["scope"]), str(row["dataset"]), str(row["arch"]), str(row["neuron"]))
        grouped[key + (str(row["readout"]),)].append(row)

    best_readout: dict[tuple[str, str, str, str], str] = {}
    best_score: dict[tuple[str, str, str, str], float] = {}
    for key_with_readout, group_rows in grouped.items():
        key = key_with_readout[:-1]
        readout = key_with_readout[-1]
        valid = [
            float(r["accuracy"])
            for r in group_rows
            if bool(r["stable"]) and int(r["nan_batches"]) == 0 and not math.isnan(float(r["accuracy"]))
        ]
        score = mean(valid) if valid else -math.inf
        if key not in best_score or score > best_score[key]:
            best_score[key] = score
            best_readout[key] = readout

    selected: list[dict[str, object]] = []
    for row in rows:
        key = (str(row["scope"]), str(row["dataset"]), str(row["arch"]), str(row["neuron"]))
        if str(row["readout"]) == best_readout[key]:
            selected.append(row)
    return selected


def tcrit_95(n: int) -> float:
    if n < 2:
        return math.nan
    if scipy_stats is not None:
        return float(scipy_stats.t.ppf(0.975, n - 1))
    table = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365}
    return table.get(n, 1.96)


def metric_summary(values: list[float]) -> tuple[int, float, float, float]:
    clean = [v for v in values if not math.isnan(v)]
    n = len(clean)
    if n == 0:
        return 0, math.nan, math.nan, math.nan
    avg = mean(clean)
    sd = stdev(clean) if n > 1 else 0.0
    ci = tcrit_95(n) * sd / math.sqrt(n) if n > 1 else math.nan
    return n, avg, sd, ci


def build_summary(selected: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in selected:
        key = (
            str(row["scope"]),
            str(row["dataset"]),
            str(row["arch"]),
            str(row["neuron"]),
            str(row["readout"]),
        )
        grouped[key].append(row)

    out: list[dict[str, object]] = []
    for key, group_rows in sorted(grouped.items()):
        scope, dataset, arch, neuron, readout = key
        acc_n, acc_mean, acc_std, acc_ci95 = metric_summary([float(r["accuracy"]) for r in group_rows])
        _, f1_mean, f1_std, f1_ci95 = metric_summary([float(r["macro_f1"]) for r in group_rows])
        _, events_mean, events_std, events_ci95 = metric_summary([float(r["events_per_sample"]) for r in group_rows])
        _, gate_mean, gate_std, gate_ci95 = metric_summary([float(r["gate_mean"]) for r in group_rows])
        failures = sum(1 for r in group_rows if (not bool(r["stable"])) or int(r["nan_batches"]) > 0)
        nan_total = sum(int(r["nan_batches"]) for r in group_rows)
        seeds = ",".join(str(r["seed"]) for r in sorted(group_rows, key=lambda x: int(x["seed"])))
        out.append(
            {
                "scope": scope,
                "dataset": dataset,
                "arch": arch,
                "neuron": neuron,
                "readout": readout,
                "seeds": seeds,
                "n": acc_n,
                "failures": failures,
                "nan_total": nan_total,
                "accuracy_mean": acc_mean,
                "accuracy_std": acc_std,
                "accuracy_ci95": acc_ci95,
                "macro_f1_mean": f1_mean,
                "macro_f1_std": f1_std,
                "macro_f1_ci95": f1_ci95,
                "events_mean": events_mean,
                "events_std": events_std,
                "events_ci95": events_ci95,
                "gate_mean": gate_mean,
                "gate_std": gate_std,
                "gate_ci95": gate_ci95,
            }
        )
    return out


def exact_signflip_p_two_sided(diffs: list[float]) -> float:
    clean = [d for d in diffs if abs(d) > 1e-12]
    if not clean:
        return 1.0
    obs = abs(mean(clean))
    count = 0
    total = 0
    for signs in itertools.product([-1.0, 1.0], repeat=len(clean)):
        total += 1
        sample_mean = abs(mean([s * d for s, d in zip(signs, clean)]))
        if sample_mean >= obs - 1e-12:
            count += 1
    return count / total


def paired_rows(selected: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], dict[str, dict[int, dict[str, object]]]] = defaultdict(lambda: defaultdict(dict))
    for row in selected:
        setting = (str(row["scope"]), str(row["dataset"]), str(row["arch"]))
        model = f"{row['neuron']}/{row['readout']}"
        grouped[setting][model][int(row["seed"])] = row

    out: list[dict[str, object]] = []
    for setting, model_map in sorted(grouped.items()):
        scope, dataset, arch = setting
        models = sorted(model_map)
        for model_a, model_b in itertools.combinations(models, 2):
            shared_seeds = sorted(set(model_map[model_a]) & set(model_map[model_b]))
            diffs = [
                float(model_map[model_a][seed]["accuracy"]) - float(model_map[model_b][seed]["accuracy"])
                for seed in shared_seeds
            ]
            n = len(diffs)
            diff_mean = mean(diffs) if n else math.nan
            diff_std = stdev(diffs) if n > 1 else 0.0
            t_stat = diff_mean / (diff_std / math.sqrt(n)) if n > 1 and diff_std > 0 else math.nan
            t_p = math.nan
            if scipy_stats is not None and n > 1:
                t_res = scipy_stats.ttest_rel(
                    [float(model_map[model_a][seed]["accuracy"]) for seed in shared_seeds],
                    [float(model_map[model_b][seed]["accuracy"]) for seed in shared_seeds],
                )
                t_p = float(t_res.pvalue)
            signflip_p = exact_signflip_p_two_sided(diffs)
            out.append(
                {
                    "scope": scope,
                    "dataset": dataset,
                    "arch": arch,
                    "model_a": model_a,
                    "model_b": model_b,
                    "paired_n": n,
                    "shared_seeds": ",".join(str(s) for s in shared_seeds),
                    "accuracy_diff_mean_a_minus_b": diff_mean,
                    "accuracy_diff_std": diff_std,
                    "paired_t_stat": t_stat,
                    "paired_t_p_two_sided": t_p,
                    "exact_signflip_p_two_sided": signflip_p,
                    "a_seed_wins": sum(1 for d in diffs if d > 0),
                    "b_seed_wins": sum(1 for d in diffs if d < 0),
                    "ties": sum(1 for d in diffs if abs(d) <= 1e-12),
                }
            )
    return out


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: object, digits: int = 4) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return "NA"
        return f"{value:.{digits}f}"
    return str(value)


def selected_lines(summary: list[dict[str, object]]) -> list[str]:
    lines = [
        "| Scope | Dataset | Arch | Neuron/readout | Accuracy mean/std | CI95 | Failures | Events mean |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        label = f"{row['neuron']} {row['readout']}"
        acc = f"{fmt(row['accuracy_mean'])} +/- {fmt(row['accuracy_std'])}"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["scope"]),
                    str(row["dataset"]),
                    str(row["arch"]),
                    label,
                    acc,
                    fmt(row["accuracy_ci95"]),
                    str(row["failures"]),
                    fmt(row["events_mean"]),
                ]
            )
            + " |"
        )
    return lines


def strongest_pair_lines(paired: list[dict[str, object]]) -> list[str]:
    interesting = [
        row
        for row in paired
        if "hyperlif/" in str(row["model_a"]) or "hyperlif/" in str(row["model_b"])
    ]
    interesting = sorted(
        interesting,
        key=lambda r: (str(r["scope"]), str(r["arch"]), abs(float(r["accuracy_diff_mean_a_minus_b"]))),
        reverse=True,
    )[:12]
    lines = [
        "| Scope | Arch | Model A | Model B | Mean diff A-B | t p | sign-flip p | Wins A/B |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in interesting:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["scope"]),
                    str(row["arch"]),
                    str(row["model_a"]),
                    str(row["model_b"]),
                    fmt(row["accuracy_diff_mean_a_minus_b"]),
                    fmt(row["paired_t_p_two_sided"]),
                    fmt(row["exact_signflip_p_two_sided"]),
                    f"{row['a_seed_wins']}/{row['b_seed_wins']}",
                ]
            )
            + " |"
        )
    return lines


def write_note(path: Path, summary: list[dict[str, object]], paired: list[dict[str, object]], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P1 Final Statistics Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Inputs",
        "",
        f"- triage root: `{args.triage_root}`",
        f"- output directory: `{args.out_dir}`",
        "- registries: full 450-run FF sweep, roster60 architecture-transfer sweep, N-MNIST tiny FF, SHD-wide FF, SHD-wide RSNN/delay shortlist",
        "",
        "## Decision",
        "",
        "The existing registries are sufficient to compute per-seed descriptive statistics, CI95 values, paired deltas, and failure counts for the main feedforward table, the architecture-transfer table, and the current reviewer-baseline table. They are not sufficient for a strict two-sided nonparametric significance claim at p<0.05 because each cell has only five seeds; the exact sign-flip lower bound is 0.0625 when all five paired differences agree.",
        "",
        "Recommended manuscript stance: report mean/std and failure counts in the main table, keep paired tests in supplement or methods notes, and describe the PLIF/ALIF result as a reviewer-baseline shortlist rather than as a fully powered statistical benchmark. A larger seed run is only needed if advisors want formal nonparametric p<0.05 claims.",
        "",
        "## Selected Configurations",
        "",
        *selected_lines(summary),
        "",
        "## HyperLIF-Centered Paired Comparisons",
        "",
        *strongest_pair_lines(paired),
        "",
        "## Output Files",
        "",
        f"- `{args.out_dir / ('p1_final_stats_summary_' + args.tag + '.csv')}`",
        f"- `{args.out_dir / ('p1_final_paired_tests_' + args.tag + '.csv')}`",
        "",
        "## Claim Impact",
        "",
        "- Safe: descriptive mean/std/CI and failure-count reporting for the current shortlist.",
        "- Safe: paired directional deltas as exploratory/statistical-context evidence.",
        "- Unsafe: strict nonparametric p<0.05 claims from the five-seed shortlist.",
        "- Open: decide whether to place paired-test p-values in supplement only, or add a compact statement in Methods.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    triage = args.triage_root
    specs = [
        RegistrySpec(
            "full_ff_temporal_450",
            "main feedforward temporal-specific table",
            triage / "results" / "hpc_559182" / "hpc_export" / "_registry.csv",
        ),
        RegistrySpec(
            "full_arch_transfer_roster60",
            "main architecture-transfer table",
            triage / "results" / "roster60" / "_registry.csv",
            allowed_archs=("conv", "rsnn", "delay"),
            allowed_neurons=("lif", "hyperlif", "adaptive"),
        ),
        RegistrySpec(
            "nmnist_tiny_ff_best_readout",
            "near-static reviewer-baseline preflight",
            triage / "results" / "p1_plif_alif_ff_nmnist_tiny_20260719" / "_registry.csv",
        ),
        RegistrySpec(
            "shd_wide_ff_shortlist",
            "SHD-wide feedforward reviewer-baseline shortlist",
            triage / "results" / "p1_baseline_shortlist_ff_shd_wide_20260719" / "_registry.csv",
        ),
        RegistrySpec(
            "shd_wide_arch_shortlist",
            "SHD-wide recurrent/delay reviewer-baseline shortlist",
            triage / "results" / "p1_baseline_arch_shortlist_shd_wide_20260719" / "_registry.csv",
        ),
    ]
    all_rows: list[dict[str, object]] = []
    for spec in specs:
        if not spec.path.exists():
            raise FileNotFoundError(spec.path)
        all_rows.extend(read_registry(spec))

    selected = selected_best_readouts(all_rows)
    summary = build_summary(selected)
    paired = paired_rows(selected)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.out_dir / f"p1_final_stats_summary_{args.tag}.csv"
    paired_path = args.out_dir / f"p1_final_paired_tests_{args.tag}.csv"
    note_path = args.out_dir / f"P1_FINAL_STATISTICS_AUDIT_{args.tag}.md"
    write_csv(summary_path, summary)
    write_csv(paired_path, paired)
    write_note(note_path, summary, paired, args)

    print(f"summary={summary_path}")
    print(f"paired={paired_path}")
    print(f"note={note_path}")
    print(f"selected_configs={len(summary)} paired_rows={len(paired)} scipy={scipy_stats is not None}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

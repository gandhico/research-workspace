"""Smoke/tiny benchmark orchestration: run the roster across seeds, log, aggregate, rank."""

from __future__ import annotations

import re
import statistics as stats
from pathlib import Path

from ..data import load_dataset
from ..models import ReservoirSNNClassifier, SNNClassifier
from ..neurons import HyperLIFConfig
from ..utils import RunDir, append_registry, set_seed, write_metrics_csv, write_summary_json
from .roster import phase1_roster
from .trainer import train_and_eval


def _slug(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z._-]+", "_", name)


def _existing_summary(results_root, dataset, slug, seed):
    """Resume support: return a prior completed run's summary for (dataset, config, seed), or None.
    Lets foreground chunks accumulate across windows even if one is interrupted."""
    import json

    d = Path(results_root) / dataset / slug / f"seed{seed}"
    summaries = sorted(d.glob("*/summary.json")) if d.exists() else []
    for s in reversed(summaries):
        try:
            return json.loads(s.read_text(encoding="utf-8"))
        except Exception:
            continue
    return None


def run_smoke(
    *, dataset="synthetic", mode="smoke", seeds=(0, 1, 2), epochs=5, hidden=64, lr=1e-3, dt=1e-3,
    T=20, input_scale=16.0, batch_size=16, clip_norm=1.0, results_root=None, roster=None, tag=None,
    architecture="feedforward",
):
    label = tag or mode
    results_root = Path(results_root) if results_root else Path(__file__).resolve().parents[3] / "results" / f"{label}_{dataset}"
    roster = roster if roster is not None else phase1_roster()
    per_config = {r["name"]: [] for r in roster}

    print(f"\n== {mode} benchmark ==  dataset={dataset}  roster={len(roster)}  seeds={list(seeds)}  epochs={epochs}  hidden={hidden}  dt={dt}")
    for seed in seeds:
        set_seed(seed)
        Xtr, ytr, Xte, yte, meta = load_dataset(dataset, mode=mode, seed=seed, T=T)
        for r in roster:
            existing = _existing_summary(results_root, meta["dataset"], _slug(r["name"]), seed)
            if existing is not None:
                per_config[r["name"]].append(existing)
                print(f"  seed{seed}  {r['name']:24s} (resumed) acc={existing.get('final_accuracy', 0):.3f}", flush=True)
                continue
            cfg = HyperLIFConfig(model=r["neuron"], **r["cfg"])
            if architecture == "reservoir":
                model = ReservoirSNNClassifier(meta["n_in"], hidden, meta["n_classes"], cfg,
                                               readout=r["readout"], dt=dt, input_scale=input_scale, seed=seed)
            else:
                model = SNNClassifier(meta["n_in"], hidden, meta["n_classes"], cfg,
                                      readout=r["readout"], dt=dt, input_scale=input_scale)
            history, summary = train_and_eval(
                model, (Xtr, ytr, Xte, yte), n_classes=meta["n_classes"],
                epochs=epochs, batch_size=batch_size, lr=lr, clip_norm=clip_norm, seed=seed,
            )
            run = RunDir(results_root, meta["dataset"], _slug(r["name"]), seed, mode=mode)
            write_metrics_csv(run.file("metrics.csv"), history)
            write_summary_json(run.file("summary.json"), {"config": r, "neuron_cfg": cfg.to_dict(), "meta": meta, **summary})
            rec = {"dataset": meta["dataset"], "config": r["name"], "neuron": r["neuron"],
                   "readout": r["readout"], "seed": seed,
                   "accuracy": summary.get("final_accuracy"), "macro_f1": summary.get("final_macro_f1"),
                   "events_per_sample": summary.get("events_per_sample"),
                   "active_frac": summary.get("active_neuron_fraction"),
                   "outside_op_frac": summary.get("outside_operating_fraction"),
                   "stable": summary.get("stable"), "wall_s": summary.get("wall_time_s")}
            append_registry(results_root, rec)
            per_config[r["name"]].append(summary)
            print(f"  seed{seed}  {r['name']:24s} acc={summary.get('final_accuracy', 0):.3f} "
                  f"ev/s={summary.get('events_per_sample', 0):6.2f} active={summary.get('active_neuron_fraction', 0):.2f} "
                  f"stable={summary.get('stable')}", flush=True)

    table = _aggregate(per_config)
    _write_summary(results_root, table, mode, seeds, epochs, hidden, dt)
    _print_table(table)
    return table


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return float(stats.mean(xs)) if xs else 0.0


def _std(xs):
    xs = [x for x in xs if x is not None]
    return float(stats.pstdev(xs)) if len(xs) > 1 else 0.0


def _aggregate(per_config):
    rows = []
    for name, runs in per_config.items():
        accs = [s.get("final_accuracy") for s in runs]
        rows.append({
            "config": name,
            "acc_mean": _mean(accs), "acc_std": _std(accs),
            "macro_f1_mean": _mean([s.get("final_macro_f1") for s in runs]),
            "events_per_sample": _mean([s.get("events_per_sample") for s in runs]),
            "active_frac": _mean([s.get("active_neuron_fraction") for s in runs]),
            "dead_frac": _mean([s.get("dead_neuron_fraction") for s in runs]),
            "outside_op_frac": _mean([s.get("outside_operating_fraction") for s in runs]),
            "stable_frac": _mean([1.0 if s.get("stable") else 0.0 for s in runs]),
            "wall_s": _mean([s.get("wall_time_s") for s in runs]),
        })
    rows.sort(key=lambda r: r["acc_mean"], reverse=True)
    return rows


def _print_table(rows):
    print(f"\n{'config':24s} {'acc':>14s} {'macroF1':>8s} {'ev/s':>7s} {'active':>7s} {'stable':>7s}")
    for r in rows:
        print(f"{r['config']:24s} {r['acc_mean']:.3f}±{r['acc_std']:.3f}  {r['macro_f1_mean']:7.3f} "
              f"{r['events_per_sample']:7.2f} {r['active_frac']:7.2f} {r['stable_frac']:7.2f}")


def _write_summary(results_root, rows, mode, seeds, epochs, hidden, dt):
    lines = [
        f"# {mode.capitalize()} benchmark — synthetic temporal task",
        "",
        f"Roster across seeds={list(seeds)}, epochs={epochs}, hidden={hidden}, dt={dt}. "
        "Pipeline de-risk run (toy task) — **not** a capability claim. Real datasets: see `data/tonic_adapter.py`.",
        "",
        "| config | accuracy | macro-F1 | events/sample | active | stable |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(f"| {r['config']} | {r['acc_mean']:.3f} ± {r['acc_std']:.3f} | {r['macro_f1_mean']:.3f} | "
                     f"{r['events_per_sample']:.2f} | {r['active_frac']:.2f} | {r['stable_frac']:.2f} |")
    Path(results_root).mkdir(parents=True, exist_ok=True)
    (Path(results_root) / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_metrics_csv(Path(results_root) / "ranking.csv", rows)

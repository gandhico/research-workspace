"""Reproducible run IO: per-run folders, a flat registry, and metric/summary writers.

Layout (mirrors the audit-harness convention so reporting tooling transfers):

    results/<dataset>/<architecture>/seed<seed>/<timestamp>/
        metrics.csv      # per-epoch (or per-eval) rows
        summary.json     # final scalar metrics + full config + provenance
    results/_registry.csv  # one row per run, for aggregation/ranking
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass
class RunDir:
    """Creates and holds the path for a single reproducible run."""

    results_root: Path
    dataset: str
    architecture: str
    seed: int
    mode: str = "tiny"
    timestamp: str = field(default_factory=lambda: time.strftime("%Y%m%d_%H%M%S"))

    def __post_init__(self) -> None:
        self.path = (
            Path(self.results_root)
            / self.dataset
            / self.architecture
            / f"seed{self.seed}"
            / self.timestamp
        )
        self.path.mkdir(parents=True, exist_ok=True)

    def file(self, name: str) -> Path:
        return self.path / name


def write_metrics_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    cols = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def write_summary_json(path: Path, summary: Mapping[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)


def append_registry(results_root: Path, record: Mapping[str, Any]) -> None:
    """Append one run's scalar summary to results/_registry.csv (header auto-managed)."""
    reg = Path(results_root) / "_registry.csv"
    reg.parent.mkdir(parents=True, exist_ok=True)
    exists = reg.exists()
    cols = list(record.keys())
    if exists:  # union of existing header and new keys, stable order
        with open(reg, newline="", encoding="utf-8") as f:
            existing = next(csv.reader(f), [])
        cols = existing + [c for c in cols if c not in existing]
    with open(reg, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if not exists:
            w.writeheader()
        w.writerow({c: record.get(c, "") for c in cols})

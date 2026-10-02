"""Shared experiment setup for the paper project.

Adds ``src`` to the import path and defines canonical output directories. The
experiment scripts are the single source of truth for the numerical data: they
write CSV files to ``results/csv`` and plain-text logs to ``results/logs``. The
figure and table scripts consume those CSV files and never re-run simulations,
so every figure and table is traceable to a named data file.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
CSV_DIR = RESULTS_DIR / "csv"
LOGS_DIR = RESULTS_DIR / "logs"
PAPER_DIR = PROJECT_ROOT / "paper"
PAPER_FIGURES_DIR = PAPER_DIR / "figures"
PAPER_TABLES_DIR = PAPER_DIR / "tables"


def ensure_results() -> None:
    for path in (FIGURES_DIR, CSV_DIR, LOGS_DIR, PAPER_FIGURES_DIR, PAPER_TABLES_DIR):
        path.mkdir(parents=True, exist_ok=True)


def write_log(name: str, text: str) -> None:
    ensure_results()
    (LOGS_DIR / name).write_text(text, encoding="utf-8")
    print(text.rstrip("\n"))

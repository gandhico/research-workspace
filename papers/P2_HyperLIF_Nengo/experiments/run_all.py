"""Run all numbered experiments in order, regenerating every CSV and log."""

from __future__ import annotations

import runpy
import time
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    scripts = sorted(here.glob("[0-9][0-9]_*.py"))
    for script in scripts:
        print(f"=== Running {script.name} ===")
        start = time.perf_counter()
        runpy.run_path(str(script), run_name="__main__")
        print(f"--- {script.name} done in {time.perf_counter() - start:.1f}s\n")


if __name__ == "__main__":
    main()

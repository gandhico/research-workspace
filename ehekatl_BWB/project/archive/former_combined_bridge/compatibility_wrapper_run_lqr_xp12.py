#!/usr/bin/env python3
"""Archived reconstruction of the former compatibility wrapper."""

from pathlib import Path
import runpy
import sys

if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "controllers" / "ehekatl_xplane12_bridge" / "run_lqr_xp12.py"
    if str(target.parent) not in sys.path:
        sys.path.insert(0, str(target.parent))
    runpy.run_path(str(target), run_name="__main__")

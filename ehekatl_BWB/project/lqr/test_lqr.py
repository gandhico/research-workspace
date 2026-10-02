#!/usr/bin/env python3
"""Compatibility wrapper for the canonical LQR tests."""

from pathlib import Path
import runpy


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "tests" / "test_lqr.py"
    runpy.run_path(str(target), run_name="__main__")

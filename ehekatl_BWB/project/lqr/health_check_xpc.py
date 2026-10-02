#!/usr/bin/env python3
"""Compatibility wrapper for the project-wide XP12 health check."""

from pathlib import Path
import runpy
import sys


if __name__ == "__main__":
    target = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "health_check_xpc.py"
    )
    if str(target.parent) not in sys.path:
        sys.path.insert(0, str(target.parent))
    runpy.run_path(str(target), run_name="__main__")

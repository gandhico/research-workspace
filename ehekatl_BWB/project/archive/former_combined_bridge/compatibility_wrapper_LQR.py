"""Archived reconstruction of the former compatibility re-export."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = PROJECT_ROOT / "controllers" / "ehekatl_xplane12_bridge"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

from controllers.ehekatl_xplane12_bridge.LQR import *  # noqa: F401,F403

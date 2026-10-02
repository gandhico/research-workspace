#!/usr/bin/env python3
"""Direct guarded/logged R3 DeePC test; interface parallel to run_backstepping_xp12.py."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_rich_r3_roll_deepc_pilot_xp12 import main
if __name__=='__main__':main()

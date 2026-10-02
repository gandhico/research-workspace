"""
Nengo GUI launcher for Stage 5:
NEF position loop + SNN attitude loop.

Run:
    nengo gui_y6_stage5_nef_position.py
"""

from y6_nef_position_fixed import build_network
from y6_nengo import default_ref

# Nengo GUI requires a top-level variable named `model`
model = build_network(default_ref)

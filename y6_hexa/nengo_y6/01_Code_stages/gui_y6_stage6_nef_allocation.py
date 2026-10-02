"""
Nengo GUI launcher for Stage 6:
NEF position + SNN attitude + NEF allocation.

Run:
    nengo gui_y6_stage6_nef_allocation.py
"""

from y6_nef_allocation_stage6_fixed import build_network
from y6_nengo import default_ref

# Nengo GUI requires a top-level variable named `model`
model = build_network(default_ref)

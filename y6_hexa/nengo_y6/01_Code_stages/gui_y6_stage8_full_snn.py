"""
Nengo GUI launcher for Stage 8:
Full SNN controller.

Run:
    nengo gui_y6_stage8_full_snn.py
"""

from y6_full_snn_fixed import build_network
from y6_nengo import default_ref

# Nengo GUI requires a top-level variable named `model`
model = build_network(default_ref)

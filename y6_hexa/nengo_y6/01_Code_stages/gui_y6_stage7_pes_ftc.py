"""
Nengo GUI launcher for Stage 7:
NEF allocation with PES fault-tolerant control.

Run:
    nengo gui_y6_stage7_pes_ftc.py
"""

from y6_pes_ftc_fixed import build_network
from y6_nengo import default_ref

# Nengo GUI requires a top-level variable named `model`
model = build_network(default_ref, fault_rotor=0, fault_t=6.0, learning_rate=1e-5)

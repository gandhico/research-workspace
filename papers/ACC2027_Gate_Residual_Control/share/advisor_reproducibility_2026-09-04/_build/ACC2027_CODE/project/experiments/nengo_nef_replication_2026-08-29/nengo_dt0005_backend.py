"""Nengo-GUI backend that fixes the validated controller timestep at 0.5 ms."""
from __future__ import annotations

import nengo


class Simulator(nengo.Simulator):
    def __init__(self, network, *args, **kwargs):
        kwargs.pop("dt", None)
        super().__init__(network, *args, dt=5e-4, **kwargs)


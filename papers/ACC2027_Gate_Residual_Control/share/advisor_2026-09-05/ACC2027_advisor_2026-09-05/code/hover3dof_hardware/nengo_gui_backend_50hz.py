"""Nengo GUI monitor backend; the independent Q8 worker remains at 200 Hz."""
import nengo


class Simulator(nengo.Simulator):
    def __init__(self, network, *args, **kwargs):
        kwargs.pop("dt", None)
        super().__init__(network, *args, dt=0.02, **kwargs)

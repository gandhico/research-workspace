"""Stage-2 control probe: pendulum plant + PD demonstrator (spiking controller built post-Phase-2)."""

from .pendulum import Pendulum, make_demos, make_reference, pd_torque, rollout_pd, tracking_rmse

__all__ = ["Pendulum", "make_demos", "make_reference", "pd_torque", "rollout_pd", "tracking_rmse"]

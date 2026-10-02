# =============================================================================
# Controllers
# =============================================================================
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import signal
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np


# ------------------------------------------------------------------
# data structures matching node contracts
# ------------------------------------------------------------------
@dataclass
class LaneState:
    lane_error: float
    d_lane_error: float
    slope_xy: float
    loop_dt: float
    previous_steering: float


@dataclass
class ControlOutput:
    raw_steering: float
    info: dict[str, Any] = field(default_factory=dict)


def build_default_args() -> argparse.Namespace:
    """Helper argument builder to supply default tuning gains.

    Can be overridden directly via python or populated by ROS2 launch.
    """
    args = argparse.Namespace()
    # General Limits
    args.max_steering = 0.523  # ~30 degrees in rad
    args.derivative_limit = 5.0
    args.pid_kp = 1.0
    args.pid_slope_gain = 0.2

    # SMC Gains
    # Tamed from the first stand test: the previous switch_gain=0.4 with a thin
    # boundary=0.05 made the switching term alone ~0.26 rad (~15 deg) for a
    # near-zero error, saturating steering to +/-30 deg and chattering. Widening
    # the boundary layer and cutting the switch gain makes it behave like a
    # smooth proportional law near the path. Re-tune from here.
    args.smc_lambda = 1.0
    args.smc_surface_slope_gain = 0.5
    args.smc_boundary = 0.30
    args.smc_error_gain = 0.6
    args.smc_slope_gain = 0.3
    args.smc_switch_gain = 0.08

    # NMPC Tuning
    args.nmpc_q_error = 10.0
    args.nmpc_q_slope = 2.0
    args.nmpc_r_steer = 0.5
    args.nmpc_r_dsteer = 1.0
    args.nmpc_model_am = 0.8
    args.nmpc_model_adelta = 0.5
    args.nmpc_model_bdelta = 0.5
    args.nmpc_model_bm = 0.2
    args.nmpc_rate_limit = 0.15  # rad per step max delta
    args.nmpc_candidates = 5
    args.nmpc_horizon = 4
    args.nmpc_beam = 3

    return args


# ------------------------------------------------------------------
# Base Class
# ------------------------------------------------------------------
class ControllerBase:
    name = "base"

    def step(self, state: LaneState) -> ControlOutput:
        raise NotImplementedError

    def close(self) -> None:
        pass


# ------------------------------------------------------------------
# SMC Implementation
# ------------------------------------------------------------------
class SMCLaneController(ControllerBase):
    name = "smc"

    def __init__(self, args: argparse.Namespace):
        self.args = args

    @staticmethod
    def sat(x: float) -> float:
        return float(np.clip(x, -1.0, 1.0))

    def step(self, state: LaneState) -> ControlOutput:
        de = float(
            np.clip(
                state.d_lane_error,
                -self.args.derivative_limit,
                self.args.derivative_limit,
            )
        )
        sigma = (
            de
            + self.args.smc_lambda * state.lane_error
            + self.args.smc_surface_slope_gain * state.slope_xy
        )
        boundary = max(float(self.args.smc_boundary), 1e-6)
        switching = self.sat(sigma / boundary)

        raw = (
            -self.args.smc_error_gain * state.lane_error
            -self.args.smc_slope_gain * state.slope_xy
            -self.args.smc_switch_gain * switching
        )

        return ControlOutput(
            raw_steering=float(raw),
            info={
                "smc_sigma": float(sigma),
                "smc_switching": float(switching),
                "de_limited": float(de),
            },
        )


# ------------------------------------------------------------------
# NMPC Implementation
# ------------------------------------------------------------------
class ImageNMPCController(ControllerBase):
    name = "nmpc_image"

    def __init__(self, args: argparse.Namespace):
        self.args = args

    def _rollout_cost(
        self,
        e0: float,
        m0: float,
        delta_prev: float,
        seq: list[float],
        dt: float,
    ) -> float:
        e = float(e0)
        m = float(m0)
        prev = float(delta_prev)
        cost = 0.0

        for delta in seq:
            ddelta = delta - prev
            cost += (
                self.args.nmpc_q_error * e * e
                + self.args.nmpc_q_slope * m * m
                + self.args.nmpc_r_steer * delta * delta
                + self.args.nmpc_r_dsteer * ddelta * ddelta
            )

            e_next = e + dt * (
                self.args.nmpc_model_am * m + self.args.nmpc_model_adelta * delta
            )
            m_next = m + dt * (
                self.args.nmpc_model_bdelta * delta - self.args.nmpc_model_bm * m
            )

            e, m, prev = float(e_next), float(m_next), float(delta)

        return float(cost)

    def step(self, state: LaneState) -> ControlOutput:
        dt = max(float(state.loop_dt), 1e-6)
        max_delta = float(self.args.max_steering)
        rate = max(float(self.args.nmpc_rate_limit), 1e-6)
        n_candidates = max(int(self.args.nmpc_candidates), 3)

        beams: list[tuple[float, list[float]]] = [(0.0, [])]

        for _ in range(int(self.args.nmpc_horizon)):
            new_beams: list[tuple[float, list[float]]] = []

            for _, seq in beams:
                prev = float(state.previous_steering if not seq else seq[-1])
                local_grid = np.linspace(prev - rate, prev + rate, n_candidates)
                local_grid = np.clip(local_grid, -max_delta, max_delta)
                local_grid = np.unique(np.round(local_grid, decimals=6))

                for delta in local_grid:
                    candidate = seq + [float(delta)]
                    cost = self._rollout_cost(
                        state.lane_error,
                        state.slope_xy,
                        state.previous_steering,
                        candidate,
                        dt,
                    )
                    new_beams.append((cost, candidate))

            if not new_beams:
                break

            new_beams.sort(key=lambda item: item[0])
            beams = new_beams[: int(self.args.nmpc_beam)]

        if not beams or not beams[0][1]:
            raw = (
                -self.args.pid_kp * state.lane_error
                - self.args.pid_slope_gain * state.slope_xy
            )
            return ControlOutput(
                raw_steering=float(raw), info={"nmpc_fallback": True}
            )

        best_cost, best_seq = beams[0]
        raw = float(best_seq[0])

        return ControlOutput(
            raw_steering=raw,
            info={
                "nmpc_cost": float(best_cost),
                "nmpc_first_delta": float(raw),
                "nmpc_seq0": best_seq[:3],
                "nmpc_rate_limit": float(rate),
                "nmpc_candidates": int(n_candidates),
            },
        )
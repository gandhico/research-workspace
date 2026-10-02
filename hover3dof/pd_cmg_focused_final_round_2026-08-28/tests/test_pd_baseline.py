"""Offline unit tests for the explicit PD baseline."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pd_baseline import (  # noqa: E402
    VendorPlant,
    allocate_exact_torque,
    allocate_stability_priority_torque,
    effective_pd_matrices,
    equivalent_second_order,
    full_axis_torque_limits,
    limit_and_slew_motor_residual,
    euler_rates_ypr_to_body_omega_ypr,
    mujoco_pd_parameters_ypr,
    mujoco_pes_target_ypr,
    mujoco_quaternion_pd_torque_ypr,
    pd_torque,
    pd_voltage_raw,
    realized_torque,
    residual_torque_limits_from_motor_volts,
    torque_to_motor_differential,
    vendor_lqr_voltage,
)


class PDBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plant = VendorPlant()

    def test_lqr_transform_is_diagonal_pd(self) -> None:
        kp, kd, offdiag = effective_pd_matrices(self.plant)
        self.assertLess(offdiag, 1e-12)
        np.testing.assert_allclose(np.diag(kp), [1.60996896, 6.18729742, 6.18729742], rtol=1e-8)
        np.testing.assert_allclose(np.diag(kd), [0.59634432, 1.69438395, 1.69438395], rtol=1e-8)

    def test_pd_equals_unclipped_lqr_torque(self) -> None:
        rng = np.random.default_rng(7)
        for _ in range(100):
            desired = rng.normal(0.0, 0.01, 3)
            angle = rng.normal(0.0, 0.01, 3)
            rate = rng.normal(0.0, 0.01, 3)
            voltage = vendor_lqr_voltage(desired, angle, rate, self.plant, clip=False)
            np.testing.assert_allclose(
                realized_torque(voltage, self.plant),
                pd_torque(desired, angle, rate, self.plant),
                rtol=1e-12,
                atol=1e-12,
            )

    def test_explicit_pd_mixer_equals_unclipped_lqr_voltage(self) -> None:
        rng = np.random.default_rng(11)
        for _ in range(100):
            desired = rng.normal(0.0, 0.2, 3)
            angle = rng.normal(0.0, 0.2, 3)
            rate = rng.normal(0.0, 0.2, 3)
            np.testing.assert_allclose(
                pd_voltage_raw(desired, angle, rate, self.plant),
                vendor_lqr_voltage(desired, angle, rate, self.plant, clip=False),
                atol=1e-12,
            )

    def test_torque_mixer_is_zero_common_mode(self) -> None:
        differential = torque_to_motor_differential(np.array([0.01, 0.02, -0.03]), self.plant)
        self.assertAlmostEqual(float(np.sum(differential)), 0.0, places=12)

    def test_residual_authority_matches_motor_voltage_parameterization(self) -> None:
        limits = residual_torque_limits_from_motor_volts(3.0, self.plant)
        np.testing.assert_allclose(limits, [0.0432, 0.14031468, 0.14031468], rtol=1e-8)
        np.testing.assert_allclose(full_axis_torque_limits(self.plant), [0.1728, 0.56125872, 0.56125872], rtol=1e-8)

    def test_motor_residual_bound_and_slew_apply_to_inserted_signal(self) -> None:
        previous = np.zeros(4)
        requested = np.array([3.0, -3.0, 0.5, -0.5])
        first = limit_and_slew_motor_residual(requested, previous, 1.2, 4.0, 0.005)
        np.testing.assert_allclose(first, [0.02, -0.02, 0.02, -0.02])
        value = first
        for _ in range(100):
            value = limit_and_slew_motor_residual(requested, value, 1.2, 4.0, 0.005)
        self.assertTrue(np.all(np.abs(value) <= 1.2 + 1e-12))

    def test_exact_allocator_preserves_feasible_torque_and_bounds(self) -> None:
        requested = np.array([0.01, 0.02, -0.015])
        voltage = allocate_exact_torque(requested, self.plant)
        self.assertTrue(np.all(voltage >= self.plant.minimum_voltage))
        self.assertTrue(np.all(voltage <= self.plant.maximum_voltage))
        np.testing.assert_allclose(realized_torque(voltage, self.plant), requested, atol=1e-12)

    def test_infeasible_allocator_request_is_explicit(self) -> None:
        with self.assertRaises(ValueError):
            allocate_exact_torque(np.array([100.0, 100.0, 100.0]), self.plant)

    def test_stability_allocator_keeps_all_motors_active(self) -> None:
        allocation = allocate_stability_priority_torque(
            np.array([1.0, 0.04, -0.03]), self.plant, motor_floor_voltage=2.0
        )
        self.assertGreaterEqual(float(np.min(allocation.voltage_fblr)), 2.0 - 1e-12)
        self.assertLessEqual(float(np.max(allocation.voltage_fblr)), 24.0 + 1e-12)

    def test_stability_allocator_reduces_yaw_before_pitch_roll(self) -> None:
        requested = np.array([1.0, 0.04, -0.03])
        allocation = allocate_stability_priority_torque(requested, self.plant, 2.0)
        self.assertLess(allocation.yaw_scale, 1.0)
        self.assertAlmostEqual(allocation.pitch_roll_scale, 1.0)
        np.testing.assert_allclose(allocation.realized_torque_ypr[1:], requested[1:], atol=1e-12)
        self.assertAlmostEqual(
            allocation.realized_torque_ypr[0],
            allocation.yaw_scale * requested[0],
            places=12,
        )

    def test_stability_allocator_is_exact_when_request_is_feasible(self) -> None:
        requested = np.array([0.01, 0.02, -0.015])
        allocation = allocate_stability_priority_torque(requested, self.plant, 2.0)
        self.assertAlmostEqual(allocation.yaw_scale, 1.0)
        self.assertAlmostEqual(allocation.pitch_roll_scale, 1.0)
        np.testing.assert_allclose(allocation.realized_torque_ypr, requested, atol=1e-12)

    def test_equivalent_second_order_values(self) -> None:
        wn, zeta = equivalent_second_order(self.plant)
        np.testing.assert_allclose(wn, [3.81799962, 10.58504292, 10.58504292], rtol=1e-8)
        np.testing.assert_allclose(zeta, [0.70710754, 1.44935063, 1.44935063], rtol=1e-8)

    def test_mujoco_pd_parameters_match_drone_formula_after_ypr_reorder(self) -> None:
        kq, kw, limits = mujoco_pd_parameters_ypr(self.plant)
        inertia = self.plant.inertia
        np.testing.assert_allclose(kq, 2.0 * inertia * np.array([3.5, 4.0, 4.0])**2)
        np.testing.assert_allclose(kw, 2.0 * .95 * np.array([3.5, 4.0, 4.0]) * inertia)
        np.testing.assert_allclose(limits, inertia * np.array([10.0, 12.0, 12.0]))

    def test_euler_rate_to_body_rate_identity_at_level(self) -> None:
        rate = np.array([.3, -.2, .1])
        np.testing.assert_allclose(euler_rates_ypr_to_body_omega_ypr(np.zeros(3), rate), rate)

    def test_mujoco_pd_torque_is_bounded(self) -> None:
        _, _, limits = mujoco_pd_parameters_ypr(self.plant)
        torque = mujoco_quaternion_pd_torque_ypr(np.ones(3), np.zeros(3), self.plant)
        np.testing.assert_allclose(torque, limits)

    def test_hover_transform_matches_canonical_drone_pd_and_pes(self) -> None:
        """The Hover equations equal drone.py after the declared frame map."""
        eq_xyz = np.array([0.07, -0.11, 0.16])
        omega_hover_ypr = np.array([0.31, -0.22, 0.13])
        # drone.py xyz torque/rate coordinates have the opposite physical sign.
        omega_drone_xyz = -omega_hover_ypr[[2, 1, 0]]
        inertia_xyz = self.plant.inertia[[2, 1, 0]]
        wn_xyz = np.array([4.0, 4.0, 3.5])
        kq_xyz = 2.0 * inertia_xyz * wn_xyz**2
        kw_xyz = 2.0 * .95 * wn_xyz * inertia_xyz
        limits_xyz = inertia_xyz * np.array([12.0, 12.0, 10.0])
        tau_drone_xyz = np.clip(
            -kq_xyz * eq_xyz - kw_xyz * omega_drone_xyz,
            -limits_xyz,
            limits_xyz,
        )
        expected_hover_ypr = -tau_drone_xyz[[2, 1, 0]]
        np.testing.assert_allclose(
            mujoco_quaternion_pd_torque_ypr(eq_xyz[[2, 1, 0]], omega_hover_ypr, self.plant),
            expected_hover_ypr,
        )

        target_drone_xyz = np.clip(-8.0 * eq_xyz, -1.0, 1.0)
        expected_target_hover_ypr = -target_drone_xyz[[2, 1, 0]]
        np.testing.assert_allclose(
            mujoco_pes_target_ypr(eq_xyz[[2, 1, 0]], omega_hover_ypr, 8.0, 0.0),
            expected_target_hover_ypr,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

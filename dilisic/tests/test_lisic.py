import unittest

import numpy as np

from dilisic.controllers import DILISICWrapper, LISICController, LISICParameters
from dilisic.plants import FlexibleSingleLinkArm


class LISICTests(unittest.TestCase):
    def test_rbf_shapes_are_finite(self):
        controller = LISICController()
        phi, phi_a = controller.basis(0.25)
        self.assertEqual(phi.shape, (45,))
        self.assertEqual(phi_a.shape, (46,))
        self.assertTrue(np.all(np.isfinite(phi)))
        self.assertTrue(np.all(np.isfinite(phi_a)))

    def test_riccati_solution_positive_definite(self):
        controller = LISICController()
        eigs = np.linalg.eigvalsh(controller.p_e)
        self.assertTrue(np.all(eigs > 0.0), eigs)

    def test_projection_keeps_weights_bounded(self):
        params = LISICParameters(max_v_f=2.0, max_w_f=2.0, max_v_h=2.0, max_w_h=2.0)
        controller = LISICController(params)
        for _ in range(100):
            controller.update(0.01, s=100.0, u_h=100.0)
        norms = controller.weight_norms()
        self.assertLessEqual(norms["v_f"], params.max_v_f + 1.0e-9)
        self.assertLessEqual(norms["w_f"], params.max_w_f + 1.0e-9)
        self.assertLessEqual(norms["v_h"], params.max_v_h + 1.0e-9)
        self.assertLessEqual(norms["w_h"], params.max_w_h + 1.0e-9)

    def test_single_agent_smoke_step_is_finite(self):
        plant = FlexibleSingleLinkArm()
        wrapper = DILISICWrapper()
        state = np.array([0.1, 0.0, 0.0, 0.0])
        ref_state = wrapper.initialize(state)
        for _ in range(20):
            control, info = wrapper.step(state, ref_state, u_di=0.0, dt=0.001)
            state = plant.rk4_step(state, control, disturbance=0.0, dt=0.001)
            self.assertTrue(np.all(np.isfinite(state)))
            self.assertTrue(np.isfinite(control))
            self.assertTrue(np.isfinite(info["s"]))

    def test_tracking_surface_uses_section_iii_error_convention(self):
        controller = LISICController()
        x = np.array([2.0, 3.0, 5.0, 7.0])
        x_ref = np.array([1.0, 1.0, 2.0, 3.0, 11.0])
        s, q_a = controller.tracking_surface(x, x_ref)
        self.assertAlmostEqual(s, 4.0 + 15.0 * 3.0 + 75.0 * 2.0 + 125.0)
        self.assertAlmostEqual(q_a, -11.0 + 15.0 * 4.0 + 75.0 * 3.0 + 125.0 * 2.0)

    def test_initial_inverse_gain_matches_flexible_arm(self):
        plant = FlexibleSingleLinkArm()
        controller = LISICController()
        _, h_hat, _, _ = controller.estimates(0.0)
        self.assertAlmostEqual(h_hat, 1.0 / plant.g(np.zeros(4)), places=12)

    def test_reference_and_plant_receive_same_filtered_u_di(self):
        wrapper = DILISICWrapper(reference_filter_tau=0.05)
        state = np.array([0.0, 0.0, 0.0, 0.0])
        ref = wrapper.initialize(state)
        wrapper.step(state, ref, u_di=0.0, dt=0.001)
        total, info = wrapper.step(state, ref, u_di=10.0, dt=0.001)
        self.assertAlmostEqual(total, info["u_di_filtered"] + info["u_lisic"])
        self.assertNotAlmostEqual(info["u_di"], info["u_di_filtered"])


if __name__ == "__main__":
    unittest.main()

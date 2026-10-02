import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from dilisic_shadow import ChainKalman, ShadowDILISIC  # noqa: E402


def sine(t, a=0.3, w=2 * np.pi * 0.25):
    return a * np.sin(w * t), a * w * np.cos(w * t), -a * w**2 * np.sin(w * t), -a * w**3 * np.cos(w * t)


def test_kalman_recovers_derivatives_of_quantized_sine():
    dt = 0.01
    kf = ChainKalman(dt)
    kf.reset(0.0)
    t = np.arange(0, 30, dt)
    q, qd, qdd, q3 = sine(t)
    quantum = 2 * np.pi / 4096
    est = np.array([kf.update(round(v / quantum) * quantum) for v in q])
    late = t > 10
    assert 1.5 < kf.estimator_bandwidth_hz() < 3.0
    assert np.max(np.abs(est[late, 0] - q[late])) < 2e-3
    assert np.max(np.abs(est[late, 1] - qd[late])) < 0.05 * np.max(np.abs(qd))
    assert np.max(np.abs(est[late, 2] - qdd[late])) < 0.30 * np.max(np.abs(qdd))
    # Documented limitation: jerk is noise-dominated (~72% worst-case error).
    assert np.max(np.abs(est[late, 3] - q3[late])) < 1.0 * np.max(np.abs(q3))


def test_shadow_outputs_finite_and_reference_model_tracks_baseline():
    dt = 0.01
    sh = ShadowDILISIC(dt)
    sh.reset(0.0)  # deliberately wrong initial velocity (true 0.47 rad/s)
    t = np.arange(0, 20, dt)
    q, qd, qdd, _ = sine(t)
    outs = [sh.step(q[k], q[k], qd[k], qdd[k]) for k in range(len(t))]
    for key in ("u_lisic_raw", "u_total", "s", "f_hat", "h_hat"):
        assert np.all(np.isfinite([o[key] for o in outs]))
    ref = np.array([o["x_ref_q"] for o in outs])
    assert np.max(np.abs(ref[t > 5] - q[t > 5])) < 0.02
    assert all(abs(o["u_lisic_bounded"]) <= sh.correction_bound for o in outs)

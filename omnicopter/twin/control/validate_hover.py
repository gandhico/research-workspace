"""Numerical acceptance checks for the simulated stage-1 hover controller."""
import json
from pathlib import Path
import numpy as np
import mujoco
from hover import make_sim, reset, kick, rotation, attitude_error


def allocator_checks():
    model, data, controller = make_sim()
    allocator = controller.allocator
    rng = np.random.default_rng(20260904)
    worst_kkt = 0.0
    # Deliberately infeasible requests exercise bound activation/release.
    for _ in range(150):
        wrench = np.r_[rng.normal(0, 35, 3), rng.normal(0, 6, 3)]
        u = allocator.solve(wrench)
        y = allocator.weight * wrench
        gradient = allocator.a.T @ (allocator.a @ u - y)
        lower = np.isclose(u, allocator.lower, atol=1e-7)
        upper = np.isclose(u, allocator.upper, atol=1e-7)
        violation = np.where(lower, np.maximum(-gradient, 0),
                             np.where(upper, np.maximum(gradient, 0), np.abs(gradient)))
        worst_kkt = max(worst_kkt, float(np.max(violation)))
        assert np.all(u >= allocator.lower - 1e-10) and np.all(u <= allocator.upper + 1e-10)
        assert np.max(violation) < 1e-6, violation
        clipped = np.clip(allocator.pinv @ y, allocator.lower, allocator.upper)
        assert np.linalg.norm(allocator.a @ u - y) <= np.linalg.norm(allocator.a @ clipped - y) + 1e-8
    # Independently compare every geometric wrench column with MuJoCo actuation.
    worst_column_error = 0.0
    for _ in range(5):
        reset(model, data, controller, False)
        mujoco.mju_quatIntegrate(data.qpos[3:7], rng.normal(0, 1, 3), 1.0)
        mujoco.mj_forward(model, data)
        r = data.xmat[controller.bid].reshape(3, 3)
        for i in range(8):
            data.ctrl[:] = 0
            data.ctrl[i] = 1
            mujoco.mj_forward(model, data)
            expected = np.zeros(model.nv)
            mujoco.mj_applyFT(model, data, r @ controller.matrix[:3, i],
                             r @ controller.matrix[3:, i], data.xipos[controller.bid],
                             controller.bid, expected)
            error = float(np.max(np.abs(data.qfrc_actuator - expected)))
            worst_column_error = max(worst_column_error, error)
            assert error < 1e-10
    q = controller.target_q
    assert np.linalg.norm(attitude_error(q, -q)) < 1e-12
    return {"random_bounded_requests": 150, "worst_KKT_violation": worst_kkt,
            "wrench_column_checks": 40, "worst_generalized_force_error": worst_column_error}


def run_case(name, offset=None, angle=None, impulse=False, dt=0.002):
    model, data, controller = make_sim()
    model.opt.timestep = dt
    reset(model, data, controller, name == "demo")
    if offset is not None:
        data.qpos[:3] += offset
    if angle is not None:
        mujoco.mju_quatIntegrate(data.qpos[3:7], np.deg2rad(np.array(angle, dtype=float)), 1.0)
    max_u, contacts, saturated, tail_p, tail_r, rows = 0., 0, 0, [], [], []
    peak_error = 0.
    for step in range(round(10 / dt)):
        if impulse and step == round(2 / dt):
            kick(data)
        mujoco.mj_forward(model, data)
        controls, metrics = controller.command(data)
        assert np.all(np.isfinite(data.qpos)) and np.all(np.isfinite(controls))
        data.ctrl[:] = controls
        max_u = max(max_u, float(np.max(np.abs(controls))))
        contacts += int(data.ncon > 0)
        saturated += int(metrics["saturated"])
        peak_error = max(peak_error, metrics["position_error_m"])
        if data.time >= 8:
            tail_p.append(metrics["position_error_m"])
            tail_r.append(metrics["attitude_error_deg"])
        if step % round(.01 / dt) == 0:
            rows.append([float(data.time), metrics["position_error_m"], metrics["attitude_error_deg"],
                         float(np.max(np.abs(controls))), metrics["force_residual_N"], metrics["torque_residual_Nm"]])
        mujoco.mj_step(model, data)
    result = {"name": name, "dt_s": dt, "duration_s": 10,
              "offset_m": offset, "rotation_vector_deg": angle, "impulse_at_2s": impulse,
              "peak_position_error_m": peak_error,
              "last_2s_max_position_error_m": max(tail_p),
              "last_2s_max_attitude_error_deg": max(tail_r),
              "peak_abs_thrust_N": max_u, "steps_with_contacts": contacts,
              "saturated_steps": saturated}
    result["passed"] = bool(max(tail_p) < .005 and max(tail_r) < .2 and contacts == 0 and max_u <= 10 + 1e-8)
    return result, rows


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "output/validation"
    out.mkdir(parents=True, exist_ok=True)
    report = {"allocator": allocator_checks(), "acceptance": {
        "last_2s_position_error_less_than_m": .005,
        "last_2s_attitude_error_less_than_deg": .2, "no_contacts": True,
        "maximum_abs_thrust_N": 10}, "cases": []}
    cases = [("equilibrium", {}), ("demo", {}), ("impulse", {"impulse": True}),
             ("larger_displacement", {"offset": [.3, -.2, -.3], "angle": [20, -15, 10]}),
             ("half_timestep", {"offset": [.1, -.08, -.15], "angle": [6, -4, 3], "dt": .001})]
    for axis in range(3):
        for sign in [-1, 1]:
            angles = [0, 0, 0]
            angles[axis] = sign * 15
            cases.append((f"axis_{axis}_{sign:+d}", {"angle": angles}))
    for name, kwargs in cases:
        result, rows = run_case(name, **kwargs)
        report["cases"].append(result)
        np.savetxt(out / f"{name}.csv", rows, delimiter=",", comments="",
                   header="time_s,position_error_m,attitude_error_deg,peak_abs_thrust_N,force_residual_N,torque_residual_Nm")
        print(json.dumps(result), flush=True)
    report["passed"] = all(r["passed"] for r in report["cases"])
    (out / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(out / "validation.json")
    if not report["passed"]:
        raise SystemExit("Hover acceptance checks failed")

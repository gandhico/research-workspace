"""Experiment 06: accuracy of the two discrete stepping schemes.

Both stepping modes share the same exact (exponential) gate relaxation; they
differ only in the membrane update:

  * ``julia``  : explicit Euler on the membrane equation (matches the Julia
                 reference / Algorithm 1 of the theory paper),
  * ``stable`` : exact update of the membrane equation linearized over one step
                 with frozen current and conductance (matches the Nengo port).

We integrate the *continuous* HyperLIF ODE with a fine-step RK4 reference and
measure the voltage/gate error of each scheme over a range of step sizes. This
quantifies the accuracy gained by the exponential membrane update and verifies
that both schemes converge to the same trajectory as dt -> 0. Feeds Figure
``fig_integration`` and Table ``tab_integration``.
"""

from __future__ import annotations

import numpy as np

from _common import CSV_DIR, ensure_results, write_log
from neurons import HyperLIFParams
from neurons.hyperlif import hyperlif_derivatives, simulate_hyperlif
from simulation.metrics import rmse, write_rows
from simulation.ode_integrators import rk4_integrate


def _stability_demo(p: HyperLIFParams, drive: float = 4.0, horizon: float = 0.1):
    """Large-step stability of explicit vs exponential membrane updates.

    At a drive above the DB onset the gate saturates open and the reset
    conductance approaches its maximum, so the membrane relaxation rate
    lambda = 1/tau + G is large. Explicit Euler is stable only for
    lambda*dt < 2; the exponential update is unconditionally stable.
    """

    rows = []
    for dt in [5e-3, 1e-2, 1.3e-2, 1.5e-2, 2e-2, 3e-2]:
        n = max(2, int(round(horizon / dt)))
        current = np.full(n, drive)
        out = {"dt": dt, "lambda_dt_at_full_gate": (1.0 / p.tau + p.reset_gain) * dt}
        for method in ("julia", "stable"):
            sim = simulate_hyperlif(current, dt, p, method=method)
            v = sim["voltage"]
            out[f"{method}_max_abs_voltage"] = float(np.max(np.abs(v)))
            out[f"{method}_finite"] = bool(np.all(np.isfinite(v)))
        rows.append(out)
    return rows


def _reference(drive: float, duration: float, dt_ref: float, p: HyperLIFParams):
    n = int(round(duration / dt_ref))
    current = np.full(n, drive)

    def deriv(state, j):
        dv, dr = hyperlif_derivatives(state[0], state[1], j, p)
        return np.array([dv, dr], dtype=float)

    trace = rk4_integrate(deriv, np.array([p.v_rest, 0.0]), current, dt_ref)
    t_ref = (np.arange(n) + 1) * dt_ref
    return t_ref, trace[:, 0], trace[:, 1]


def main() -> None:
    ensure_results()

    p = HyperLIFParams()
    drive = 1.5  # sustained limit-cycle firing for the baseline model
    duration = 0.08
    dt_ref = 2e-6

    t_ref, v_ref, r_ref = _reference(drive, duration, dt_ref, p)

    test_dts = [2e-3, 1e-3, 5e-4, 2.5e-4, 1e-4, 5e-5]
    rows: list[dict] = []
    julia_minus_stable: list[dict] = []

    for dt in test_dts:
        n = int(round(duration / dt))
        current = np.full(n, drive)
        t_test = (np.arange(n) + 1) * dt
        v_ref_i = np.interp(t_test, t_ref, v_ref)
        r_ref_i = np.interp(t_test, t_ref, r_ref)

        traces = {}
        for method in ("julia", "stable"):
            sim = simulate_hyperlif(current, dt, p, method=method)
            v, r = sim["voltage"], sim["reset_gate"]
            traces[method] = v
            rows.append(
                {
                    "dt": dt,
                    "method": method,
                    "voltage_rmse": rmse(v, v_ref_i),
                    "voltage_max_abs": float(np.max(np.abs(v - v_ref_i))),
                    "gate_rmse": rmse(r, r_ref_i),
                    "gate_max_abs": float(np.max(np.abs(r - r_ref_i))),
                }
            )
        julia_minus_stable.append(
            {
                "dt": dt,
                "voltage_diff_rmse": rmse(traces["julia"], traces["stable"]),
                "voltage_diff_max_abs": float(np.max(np.abs(traces["julia"] - traces["stable"]))),
            }
        )

    write_rows(CSV_DIR / "06_integration_accuracy.csv", rows)
    write_rows(CSV_DIR / "06_integration_julia_vs_stable.csv", julia_minus_stable)

    stab_rows = _stability_demo(p)
    write_rows(CSV_DIR / "06_stability.csv", stab_rows)

    log = [f"Reference: RK4 of the continuous ODE, dt_ref={dt_ref}, drive I={drive}, T={duration}s"]
    for dt in test_dts:
        jr = next(r for r in rows if r["dt"] == dt and r["method"] == "julia")
        sr = next(r for r in rows if r["dt"] == dt and r["method"] == "stable")
        log.append(
            f"dt={dt:.1e}: voltage RMSE julia={jr['voltage_rmse']:.3e}, "
            f"stable={sr['voltage_rmse']:.3e}; gate RMSE={jr['gate_rmse']:.3e}"
        )
    log.append("Large-step stability (drive I=4.0, gate saturates open):")
    for sr in stab_rows:
        log.append(
            f"dt={sr['dt']:.1e} (lambda*dt={sr['lambda_dt_at_full_gate']:.2f}): "
            f"julia max|v|={sr['julia_max_abs_voltage']:.3e} (finite={sr['julia_finite']}), "
            f"stable max|v|={sr['stable_max_abs_voltage']:.3e} (finite={sr['stable_finite']})"
        )
    write_log("06_numerical_integration.txt", "\n".join(log) + "\n")


if __name__ == "__main__":
    main()

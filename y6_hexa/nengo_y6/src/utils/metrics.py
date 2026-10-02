"""
metrics.py  —  step-response + control-effort benchmark metrics.

All metrics are computed from the **actual simulation traces** (time, output,
control) — no analytic shortcuts — so they are valid for classical *and* neural
controllers alike.  Shared by every experiment.

Metric set (per the project's standing benchmark requirement):
  rise time (10-90%), settling time (+/-2%), overshoot %, steady-state error,
  IAE, ISE, control energy, control effort beyond hover, saturation %,
  tracking RMSE, plus a one-line stability note.
"""
import numpy as np


def _rise_time(t, y, y0, target):
    """10%-90% rise time for a rising step (returns NaN if never reached)."""
    amp = target - y0
    if amp == 0:
        return float("nan")
    lo, hi = y0 + 0.1 * amp, y0 + 0.9 * amp
    i_lo = np.argmax(y >= lo) if np.any(y >= lo) else None
    i_hi = np.argmax(y >= hi) if np.any(y >= hi) else None
    if i_lo is None or i_hi is None:
        return float("nan")
    return float(t[i_hi] - t[i_lo])


def _settling_time(t, y, target, amp, band):
    """Time (from window start) after which |y-target| stays within band*|amp|."""
    tol = abs(band * amp)
    outside = np.abs(y - target) > tol
    if not np.any(outside):
        return 0.0
    last = np.where(outside)[0][-1]
    if last + 1 < len(t):
        return float(t[last + 1] - t[0])
    return float("nan")  # never settled within the window


def step_metrics(t, y, u, target, t_step, P, settle_band=0.02, ss_window=1.0):
    """Return a dict of benchmark metrics over the step window t >= t_step."""
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    u = np.asarray(u, float)

    m = t >= t_step
    tw, yw, uw = t[m], y[m], u[m]

    y0 = yw[0]
    amp = target - y0
    e = target - yw

    rise = _rise_time(tw, yw, y0, target)
    settle = _settling_time(tw, yw, target, amp, settle_band)
    overshoot = max(0.0, (np.max(yw) - target) / abs(amp) * 100.0) if amp else 0.0

    ss_mask = tw >= (tw[-1] - ss_window)
    sse = float(target - np.mean(yw[ss_mask]))

    iae = float(np.trapezoid(np.abs(e), tw))
    ise = float(np.trapezoid(e ** 2, tw))

    energy = float(np.trapezoid(uw ** 2, tw))                       # int u^2 dt
    effort = float(np.trapezoid((uw - P.u_hover) ** 2, tw))         # beyond hover
    sat = float(np.mean((uw <= P.u_min + 1e-9) |
                        (uw >= P.u_max - 1e-9)) * 100.0)
    rmse = float(np.sqrt(np.mean(e ** 2)))

    return dict(rise_time_s=rise, settling_time_s=settle, overshoot_pct=overshoot,
                sse_m=sse, iae=iae, ise=ise, control_energy=energy,
                ctrl_effort_beyond_hover=effort, saturation_pct=sat,
                tracking_rmse_m=rmse)


def step_metrics_general(t, y, u, target, t_step, u_ref=0.0, u_min=None,
                         u_max=None, settle_band=0.02, ss_window=1.0, settle_abs=None):
    """Generic version of step_metrics for any subsystem (no gravity/hover).

    ``u_ref`` is the nominal/equilibrium control value (0 for torques).  Saturation
    is reported only if ``u_min``/``u_max`` are given.  ``settle_abs`` optionally
    overrides the settling tolerance with an absolute value (useful for near-zero
    targets where a relative band is ill-defined).
    """
    t = np.asarray(t, float); y = np.asarray(y, float); u = np.asarray(u, float)
    m = t >= t_step
    tw, yw, uw = t[m], y[m], u[m]
    y0 = yw[0]
    amp = target - y0
    e = target - yw

    rise = _rise_time(tw, yw, y0, target)
    if settle_abs is not None:
        outside = np.abs(yw - target) > settle_abs
        if not np.any(outside):
            settle = 0.0
        else:
            last = np.where(outside)[0][-1]
            settle = float(tw[last + 1] - tw[0]) if last + 1 < len(tw) else float("nan")
    else:
        settle = _settling_time(tw, yw, target, amp, settle_band)
    overshoot = max(0.0, (np.max(yw) - target) / abs(amp) * 100.0) if amp else 0.0

    ss_mask = tw >= (tw[-1] - ss_window)
    sse = float(target - np.mean(yw[ss_mask]))
    iae = float(np.trapezoid(np.abs(e), tw))
    ise = float(np.trapezoid(e ** 2, tw))
    energy = float(np.trapezoid(uw ** 2, tw))
    effort = float(np.trapezoid((uw - u_ref) ** 2, tw))
    if u_min is not None and u_max is not None:
        sat = float(np.mean((uw <= u_min + 1e-9) | (uw >= u_max - 1e-9)) * 100.0)
    else:
        sat = 0.0
    rmse = float(np.sqrt(np.mean(e ** 2)))
    return dict(rise_time_s=rise, settling_time_s=settle, overshoot_pct=overshoot,
                sse=sse, iae=iae, ise=ise, control_energy=energy,
                ctrl_effort=effort, saturation_pct=sat, tracking_rmse=rmse)


def tracking_metrics(t, y, ref, u=None, t0=0.0):
    """Trajectory-tracking metrics (for sinusoid/ramp references, not steps)."""
    t = np.asarray(t, float); y = np.asarray(y, float); ref = np.asarray(ref, float)
    m = t >= t0
    tw, yw, rw = t[m], y[m], ref[m]
    e = rw - yw
    out = dict(rmse=float(np.sqrt(np.mean(e ** 2))),
               iae=float(np.trapezoid(np.abs(e), tw)),
               ise=float(np.trapezoid(e ** 2, tw)),
               max_abs_err=float(np.max(np.abs(e))),
               final_abs_err=float(abs(e[-1])))
    if u is not None:
        out["control_energy"] = float(np.trapezoid(np.asarray(u, float)[m] ** 2, tw))
    return out


def stability_note(metrics, tol=0.02):
    """One-line qualitative stability verdict (works for any subsystem)."""
    sse = metrics.get("sse_m", metrics.get("sse", 0.0))
    if np.isnan(metrics["settling_time_s"]):
        return "UNSTABLE/UNSETTLED: did not enter the settling band within the window"
    if abs(sse) < tol:
        return "stable; settled within tolerance"
    return "stable but residual steady-state offset"

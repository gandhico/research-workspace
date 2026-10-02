"""Run DILISIC in shadow mode on the QArm wrist, from a recorded log or on live hardware.

  replay LOG_full.csv   Recorded wrist data (e.g. a qarm_wrist_step_test *_full.csv);
                        the logged wrist command is used as the baseline reference.
  hw                    The live wrist tracks a smooth baseline sinusoid (a visible
                        motion). ONLY the baseline is sent to the servo; DILISIC runs
                        alongside and its request is logged, never actuated.

The hardware run uses the same safety layer as qarm_wrist_step_test.py
(Quanser gains, hardware-clocked sampling, PAL limits, abort monitors).
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np

from dilisic_shadow import ShadowDILISIC

LOG_DIR = Path(__file__).resolve().parents[1] / "hw_logs"
WRIST = 3
WRIST_SLEW = 0.8  # rad/s software rate limit on the streamed wrist command (< pi/2 caution level)
FIELDS = ["q_hat", "qd_hat", "qdd_hat", "qddd_hat", "x_ref_q", "x_ref_qd", "u_di", "u_di_filtered",
          "u_lisic_raw", "u_lisic_bounded", "u_total", "lisic_saturated", "shadow_bound_hit",
          "s", "f_hat", "h_hat", "u_r", "w_norm_max", "s_e3", "s_e2", "s_e1", "s_e0"]


def baseline(t, centre, amplitude, w, duration, ramp_s):
    """Sinusoid with a raised-cosine amplitude ramp at both ends, and its exact derivatives.

    q = c + A e(t) sin(wt), e = (1 - cos(pi m))/2, m = min(1, t/R, (T - t)/R).
    (Run 20260927_193307 omitted the e' and e'' terms; the resulting feed-forward
    mismatch during the ramps drove the reference model 0.06 rad off.)
    """
    m_raw = min(1.0, t / ramp_s, (duration - t) / ramp_s)
    m = max(m_raw, 0.0)
    if m_raw >= 1.0 or m_raw <= 0.0:
        dm = 0.0
    else:
        dm = 1.0 / ramp_s if t / ramp_s < (duration - t) / ramp_s else -1.0 / ramp_s
    e = 0.5 - 0.5 * np.cos(np.pi * m)
    de = 0.5 * np.pi * np.sin(np.pi * m) * dm
    dde = 0.5 * np.pi**2 * np.cos(np.pi * m) * dm**2
    s, c = np.sin(w * t), np.cos(w * t)
    q = centre + amplitude * e * s
    qd = amplitude * (de * s + e * w * c)
    qdd = amplitude * (dde * s + 2 * de * w * c - e * w * w * s)
    return q, qd, qdd


def summarize(rows, header, extra):
    a = {k: np.array([r[i] for r in rows], dtype=float) for i, k in enumerate(header)}
    t = a["time_s"]
    finite = all(np.all(np.isfinite(a[k])) for k in FIELDS)
    u = a["u_lisic_raw"]
    late = t > 2.0

    def p(x, q):
        return float(np.percentile(np.abs(x), q))

    return {**extra, "samples": len(rows), "duration_s": float(t[-1] - t[0]), "all_finite": finite,
            "u_lisic_abs_p50": p(u, 50), "u_lisic_abs_p95": p(u, 95), "u_lisic_abs_max": p(u, 100),
            "u_lisic_abs_p95_after_2s": p(u[late], 95) if late.any() else None,
            "lisic_saturated_frac": float(a["lisic_saturated"].mean()),
            "shadow_bound_hit_frac": float(a["shadow_bound_hit"].mean()),
            "s_abs_max": p(a["s"], 100), "h_hat_range": [float(a["h_hat"].min()), float(a["h_hat"].max())],
            "f_hat_abs_max": p(a["f_hat"], 100), "w_norm_max": float(a["w_norm_max"].max()),
            "meas_minus_baseline_abs_max": p(a["q_meas"] - a["q_ref"], 100),
            "ref_model_minus_baseline_abs_max_after_2s":
                p((a["x_ref_q"] - a["q_ref"])[late], 100) if late.any() else None,
            "estimator_minus_meas_abs_max": p(a["q_hat"] - a["q_meas"], 100),
            "s_term_rms_after_2s": {k: float(np.sqrt(np.mean(a[k][late] ** 2))) if late.any() else None
                                    for k in ("s_e3", "s_e2", "s_e1", "s_e0")}}


def write_outputs(tag, rows, header, summary):
    path = LOG_DIR / f"{tag}.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    summary["log"] = str(path)
    (LOG_DIR / f"{tag}_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


def replay(log: Path, adapt: bool = True, sigma_snap: float = 2.0):
    """Replay a step-test *_full.csv (reference = logged wrist command, derivatives 0) or a
    *_shadow_hw.csv (reference = logged smooth baseline, derivatives by differentiation)."""
    data = np.genfromtxt(log, delimiter=",", names=True)
    t = data["time_s"]
    dt = float(np.median(np.diff(t)))
    if "q_ref" in data.dtype.names:
        q, r = data["q_meas"], data["q_ref"]
        rd = np.gradient(r, dt)
        rdd = np.gradient(rd, dt)
    else:
        q, r = data["pos_wrist"], data["cmd_wrist"]
        rd = rdd = np.zeros_like(r)
    sh = ShadowDILISIC(dt, adapt=adapt, sigma_snap=sigma_snap)
    sh.reset(float(q[0]), float(rd[0]))
    header = ["time_s", "q_meas", "q_ref"] + FIELDS
    rows = []
    for k in range(len(t)):
        out = sh.step(float(q[k]), float(r[k]), float(rd[k]), float(rdd[k]))
        rows.append([t[k], q[k], r[k]] + [out[f] for f in FIELDS])
    summary = summarize(rows, header, {"mode": "replay", "source": str(log), "dt": dt, "adapt": adapt,
                                       "sigma_snap": sigma_snap,
                                       "estimator_bandwidth_hz": sh.kf.estimator_bandwidth_hz()})
    tag = f"_shadow_replay_{'adapt' if adapt else 'frozen'}_snap{sigma_snap:g}"
    write_outputs(time.strftime("%Y%m%d_%H%M%S") + tag, rows, header, summary)


def hardware(amplitude, freq, duration, rate):
    from quanser.hardware import Clock, HIL
    import qarm_wrist_step_test as bench

    dt = 1.0 / rate
    w = 2 * np.pi * freq
    ramp_s = 2.0
    card = HIL()
    card.open("qarm_usb", "0")
    arm = bench.Arm(card)
    sh = ShadowDILISIC(dt, adapt=False)      # primary readout: frozen weights
    sh_a = ShadowDILISIC(dt, adapt=True)     # side-by-side: paper adaptation (open loop here)
    header = ["time_s", "q_meas", "q_ref", "host_s"] + [f"pos_{j}" for j in bench.JOINTS] + \
             [f"cur_{j}" for j in bench.JOINTS] + FIELDS + ["cmd_wrist", "u_lisic_raw_adapt",
                                                           "h_hat_adapt", "lisic_saturated_adapt"]
    rows, abort, task = [], None, None
    try:
        q0, *_ = arm.read()
        hold = np.clip(q0, bench.CMD_LO, bench.CMD_HI)
        # Streaming setpoints every 10 ms restarts the servo's velocity profile, so the
        # wrist crawled (0.05 rad in 1.2 s, run 20260927_193148). For the streamed
        # joint, disable the firmware profile (0 = no limit) and rate-limit in software.
        opts = bench.options_string(vel_wrist=0, acc_wrist=0)
        card.set_card_specific_options(opts, len(opts) + 1)
        card.set_double_property(bench.QUANSER_GAIN_PROPS, len(bench.QUANSER_GAIN_PROPS),
                                 bench.QUANSER_GAIN_VALUES)
        centre = hold[WRIST]
        if not (bench.CMD_LO[WRIST] + amplitude + 0.1 < centre < bench.CMD_HI[WRIST] - amplitude - 0.1):
            raise SystemExit("wrist too close to its limit for this amplitude")
        task = card.task_create_reader(int(rate), bench.CUR_IN, 5, None, 0, None, 0,
                                       arm.other_ch, len(arm.other_ch))
        card.task_start(task, Clock.HARDWARE_CLOCK_0, rate, 2**32 - 1)
        t0 = time.perf_counter()
        settled_ref = None
        prev_cmd = centre
        for k in range(int(duration * rate)):
            t = k * dt
            q, qd, temp, pwm, cur = arm.read_task(task)
            host = time.perf_counter() - t0
            if k == 0:
                sh.reset(float(q[WRIST]))
                sh_a.reset(float(q[WRIST]))
            q_ref, qd_ref, qdd_ref = baseline(t, centre, amplitude, w, duration, ramp_s)
            cmd = hold.copy()
            cmd[WRIST] = prev_cmd + np.clip(q_ref - prev_cmd, -WRIST_SLEW * dt, WRIST_SLEW * dt)
            cmd = arm.command(cmd)            # baseline only, never DILISIC
            prev_cmd = cmd[WRIST]
            out = sh.step(float(q[WRIST]), q_ref, qd_ref, qdd_ref)
            out_a = sh_a.step(float(q[WRIST]), q_ref, qd_ref, qdd_ref)
            rows.append([t, q[WRIST], q_ref, host, *q, *cur] + [out[f] for f in FIELDS] +
                        [cmd[WRIST], out_a["u_lisic_raw"], out_a["h_hat"], out_a["lisic_saturated"]])

            if settled_ref is None and t > bench.SETTLE_S:
                settled_ref = q.copy()
            if not np.all(np.isfinite(np.concatenate([q, cur, temp]))):
                abort = "non-finite reading"
            elif settled_ref is not None and np.max(np.abs((q - settled_ref)[:3])) > bench.MAX_DRIFT_OTHERS:
                abort = f"non-wrist drift {np.round(q - settled_ref, 3).tolist()}"
            elif abs(q[WRIST] - centre) > amplitude + 0.05:
                abort = f"wrist left envelope {q[WRIST] - centre:.3f}"
            elif abs(q[WRIST] - q_ref) > 0.15:
                abort = f"wrist tracking error {q[WRIST] - q_ref:.3f}"
            elif np.any(np.abs(cur) > bench.MAX_CUR_FRAC * bench.CUR_RANGE):
                abort = f"current {np.round(cur, 3).tolist()}"
            elif np.any(temp > bench.MAX_TEMP_C):
                abort = f"temperature {temp.tolist()}"
            if abort:
                arm.command(q)
                break
        if not abort:
            end = time.perf_counter() + 1.0
            while time.perf_counter() < end:
                arm.command(hold)
                time.sleep(0.02)
    finally:
        if task is not None:
            card.task_stop(task)
            card.task_delete(task)
        card.close()
    ua = np.abs([r[header.index("u_lisic_raw_adapt")] for r in rows])
    ha = [r[header.index("h_hat_adapt")] for r in rows]
    summary = summarize(rows, header, {"mode": "hw", "abort_reason": abort, "amplitude_rad": amplitude,
                                       "primary_readout": "frozen LISIC weights",
                                       "adaptive_u_abs_p50": float(np.percentile(ua, 50)),
                                       "adaptive_u_abs_p95": float(np.percentile(ua, 95)),
                                       "adaptive_saturated_frac": float(np.mean(
                                           [r[header.index("lisic_saturated_adapt")] for r in rows])),
                                       "adaptive_h_hat_range": [float(min(ha)), float(max(ha))],
                                       "freq_hz": freq, "rate_hz": rate, "actuated": "baseline only",
                                       "estimator_bandwidth_hz": sh.kf.estimator_bandwidth_hz()})
    write_outputs(time.strftime("%Y%m%d_%H%M%S") + "_shadow_hw", rows, header, summary)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)
    r = sub.add_parser("replay")
    r.add_argument("log", type=Path)
    r.add_argument("--frozen", action="store_true", help="freeze LISIC weight adaptation")
    r.add_argument("--sigma-snap", type=float, default=2.0)
    h = sub.add_parser("hw")
    h.add_argument("--amplitude", type=float, default=0.3)
    h.add_argument("--freq", type=float, default=0.25)
    h.add_argument("--duration", type=float, default=30.0)
    h.add_argument("--rate", type=float, default=100.0)
    a = p.parse_args()
    if a.mode == "replay":
        replay(a.log, adapt=not a.frozen, sigma_snap=a.sigma_snap)
    else:
        if a.amplitude > 0.5 or a.freq > 0.5:
            raise SystemExit("refusing: amplitude <= 0.5 rad and freq <= 0.5 Hz for shadow runs")
        hardware(a.amplitude, a.freq, a.duration, a.rate)

"""
Real-time matplotlib dashboard for HyperLIF gate-state residual experiments.

Usage:
    dash = Dashboard(enabled=True, update_every=50)
    dash.setup(params)
    for step in sim_loop:
        dash.update(state, refs, control_info)
    dash.close()
    dash.save_figures(output_dir)

The dashboard displays:
    Row 0: Quaternion components q0..q3 + reference
    Row 1: Euler angles roll/pitch/yaw + reference
    Row 2: Angular velocity wx,wy,wz
    Row 3: Body torques τx,τy,τz and collective thrust
    Row 4: Motor commands u1..u4 (if rotor-level)
    Row 5: Neural state: gate, voltage, events, residual
    Row 6: Tracking metrics: qerr_angle, altitude z, RMSE
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


_MAX_BUFFER = 6000  # ~3s at dt=0.0005


@dataclass
class DashState:
    """Single-step state snapshot for dashboard update."""
    t: float
    q: np.ndarray           # [w,x,y,z]
    q_ref: np.ndarray
    euler: np.ndarray       # [roll,pitch,yaw]
    euler_ref: np.ndarray
    omega: np.ndarray       # [wx,wy,wz]
    tau: np.ndarray         # [τx,τy,τz]
    collective: float
    motors: Optional[np.ndarray]     # [u1,u2,u3,u4] or None
    qerr_angle: float
    z: float
    gate: np.ndarray         # HyperLIF gate state (6 or 8 neurons)
    voltage: np.ndarray
    events: np.ndarray
    residual: Optional[np.ndarray]
    rotor_sat_flags: Optional[np.ndarray]


class Dashboard:
    """
    Real-time matplotlib dashboard (non-blocking animation).

    Uses blit=False and tight_layout refresh for simplicity and Windows compat.
    """

    def __init__(self, enabled: bool = True, update_every: int = 50,
                 max_t_shown: float = 10.0):
        self.enabled = enabled
        self.update_every = update_every
        self.max_t_shown = max_t_shown
        self._fig = None
        self._axes = None
        self._lines: dict = {}
        self._step = 0
        self._buf: dict[str, deque] = {}
        self._has_rotors = False
        self._initialized = False

    def setup(self, has_rotors: bool = False, title: str = "") -> None:
        if not self.enabled:
            return
        try:
            import matplotlib
            matplotlib.use("TkAgg")
        except Exception:
            pass

        import matplotlib.pyplot as plt
        self._has_rotors = has_rotors
        n_rows = 7 if has_rotors else 6
        self._fig, self._axes = plt.subplots(n_rows, 1,
                                              figsize=(11, 3 * n_rows), sharex=False)
        self._fig.suptitle(title or "HyperLIF Gate-State Residual — Live Dashboard",
                           fontsize=10)
        plt.subplots_adjust(hspace=0.45, left=0.08, right=0.97)

        keys = ["t", "q0","q1","q2","q3", "q0r","q1r","q2r","q3r",
                "roll","pitch","yaw","roll_r","pitch_r","yaw_r",
                "wx","wy","wz", "tx","ty","tz","coll",
                "qerr","z"]
        if has_rotors:
            keys += ["u1","u2","u3","u4","rotor_sat"]
        keys += ["gate0","gate1","gate2", "v_mean","ev_count","res_norm"]

        for k in keys:
            self._buf[k] = deque(maxlen=_MAX_BUFFER)

        self._initialized = True
        plt.ion()
        self._fig.canvas.draw()
        plt.pause(0.001)

    def update(self, s: DashState) -> None:
        if not self.enabled or not self._initialized:
            return

        b = self._buf
        b["t"].append(s.t)
        for i, c in enumerate(["q0","q1","q2","q3"]):
            b[c].append(s.q[i])
        for i, c in enumerate(["q0r","q1r","q2r","q3r"]):
            b[c].append(s.q_ref[i])
        labels_e = ["roll","pitch","yaw"]
        labels_r = ["roll_r","pitch_r","yaw_r"]
        for i in range(3):
            b[labels_e[i]].append(s.euler[i])
            b[labels_r[i]].append(s.euler_ref[i])
        for i, c in enumerate(["wx","wy","wz"]):
            b[c].append(s.omega[i])
        for i, c in enumerate(["tx","ty","tz"]):
            b[c].append(s.tau[i])
        b["coll"].append(s.collective)
        b["qerr"].append(s.qerr_angle)
        b["z"].append(s.z)

        g = s.gate if len(s.gate) >= 3 else np.pad(s.gate, (0, 3 - len(s.gate)))
        b["gate0"].append(g[0])
        b["gate1"].append(g[1])
        b["gate2"].append(g[2])
        b["v_mean"].append(float(np.mean(s.voltage)) if len(s.voltage) > 0 else 0.0)
        b["ev_count"].append(float(np.sum(s.events)))
        b["res_norm"].append(float(np.linalg.norm(s.residual)) if s.residual is not None else 0.0)

        if self._has_rotors and s.motors is not None:
            for i, c in enumerate(["u1","u2","u3","u4"]):
                b[c].append(s.motors[i])
            b["rotor_sat"].append(float(np.sum(s.rotor_sat_flags)) if s.rotor_sat_flags is not None else 0.0)

        self._step += 1
        if self._step % self.update_every == 0:
            self._redraw()

    def _redraw(self) -> None:
        import matplotlib.pyplot as plt
        axes = self._axes
        b = self._buf
        t = np.array(b["t"])
        if len(t) < 2:
            return

        # Clip to max_t_shown
        t_min = max(0, t[-1] - self.max_t_shown)
        mask  = t >= t_min
        tm = t[mask]

        def _m(key): return np.array(b[key])[mask]

        ax = axes[0]
        ax.cla()
        for c, lb, ls in [("q0","q0","--"),("q1","q1","--"),("q2","q2","--"),("q3","q3","--"),
                           ("q0r","q0_ref","-"),("q1r","q1_ref","-"),("q2r","q2_ref","-"),("q3r","q3_ref","-")]:
            ax.plot(tm, _m(c), ls, linewidth=0.8, label=lb)
        ax.set_ylabel("Quaternion"); ax.grid(True, alpha=0.3); ax.set_title("Quaternion", fontsize=8)

        ax = axes[1]
        ax.cla()
        for c, lb, clr in [("roll","roll","C0"),("pitch","pitch","C1"),("yaw","yaw","C2")]:
            ax.plot(tm, np.degrees(_m(c)), color=clr, linewidth=1.0, label=lb)
            ax.plot(tm, np.degrees(_m(c+"_r")), "--", color=clr, linewidth=0.8)
        ax.set_ylabel("Euler [deg]"); ax.grid(True, alpha=0.3); ax.set_title("Euler Angles (— meas, -- ref)", fontsize=8)

        ax = axes[2]
        ax.cla()
        for c, lb in [("wx","ωx"),("wy","ωy"),("wz","ωz")]:
            ax.plot(tm, _m(c), linewidth=1.0, label=lb)
        ax.set_ylabel("ω [rad/s]"); ax.grid(True, alpha=0.3); ax.set_title("Body Rates", fontsize=8)
        ax.legend(fontsize=7, loc="upper right")

        ax = axes[3]
        ax.cla()
        for c, lb in [("tx","τx"),("ty","τy"),("tz","τz")]:
            ax.plot(tm, _m(c), linewidth=1.0, label=lb)
        ax.plot(tm, _m("coll"), "k--", linewidth=0.8, label="T_coll")
        ax.set_ylabel("Torque / Thrust"); ax.grid(True, alpha=0.3); ax.set_title("Control Signals", fontsize=8)
        ax.legend(fontsize=7, loc="upper right")

        row = 4
        if self._has_rotors:
            ax = axes[row]; ax.cla()
            for c, lb in [("u1","m1"),("u2","m2"),("u3","m3"),("u4","m4")]:
                ax.plot(tm, _m(c), linewidth=1.0, label=lb)
            ax.set_ylabel("Motor cmd [N]"); ax.grid(True, alpha=0.3); ax.set_title("Motor Commands", fontsize=8)
            ax.legend(fontsize=7, loc="upper right")
            row = 5

        ax = axes[row]; ax.cla()
        ax.plot(tm, _m("qerr"), "r-", linewidth=1.2, label="qerr")
        ax.plot(tm, _m("z"), "b-", linewidth=1.0, label="z")
        ax.set_ylabel("qerr [rad] / z [m]"); ax.grid(True, alpha=0.3); ax.set_title("Tracking Metrics", fontsize=8)
        ax.legend(fontsize=7, loc="upper right")
        row += 1

        ax = axes[row]; ax.cla()
        ax.plot(tm, _m("gate0"), label="gate[0]")
        ax.plot(tm, _m("gate1"), label="gate[1]")
        ax.plot(tm, _m("gate2"), label="gate[2]")
        ax.plot(tm, _m("v_mean"), "--", label="V_mean")
        ax.plot(tm, _m("ev_count"), "k.", markersize=1, label="events")
        if np.max(_m("res_norm")) > 1e-8:
            ax.plot(tm, _m("res_norm"), "m-", linewidth=0.8, label="|res|")
        ax.set_ylabel("Neural"); ax.set_xlabel("t [s]")
        ax.grid(True, alpha=0.3); ax.set_title("Neural / Residual State", fontsize=8)
        ax.legend(fontsize=7, loc="upper right")

        try:
            self._fig.canvas.draw_idle()
            self._fig.canvas.flush_events()
        except Exception:
            pass

    def save_figures(self, output_dir, stem: str = "dashboard") -> None:
        if not self.enabled or self._fig is None:
            return
        import matplotlib.pyplot as plt
        path = output_dir / f"{stem}_dashboard.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        self._redraw()
        self._fig.savefig(str(path), dpi=180, bbox_inches="tight")
        print(f"Dashboard figure saved: {path}")

    def close(self) -> None:
        if self._fig is not None:
            import matplotlib.pyplot as plt
            plt.close(self._fig)
            self._fig = None

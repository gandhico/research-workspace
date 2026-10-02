from __future__ import annotations

import argparse
import csv
import json
import math
import signal
import time
from collections import deque
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from .filters import DerivativeFilter
from .qube_io import DEFAULT_QUANSER_PYTHON, ensure_quanser_python, get_qube_class, read_state, safe_stop_qube


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def wrap_to_pi(x: float) -> float:
    return (x + math.pi) % (2.0 * math.pi) - math.pi


# ----------------------------------------------------------------------------
# LED color coding — distinguishes controller/phase at a glance.
#   BLUE            waiting / swinging (not yet balancing)
#   GREEN           active balance, classical only (residual_mode == "none")
#   CYAN -> MAGENTA active balance WITH residual applied; blends toward magenta
#                   as |applied residual| approaches --residual-max-voltage, so
#                   the LED visibly pulses when the residual kicks in
#   RED             fault / e-stop / shutdown
# ----------------------------------------------------------------------------
def led_for_state(
    control_mode: str,
    residual_mode: str,
    u_residual_applied: float,
    residual_max_voltage: float,
) -> np.ndarray:
    if control_mode in ("fault_zero", "swingup_theta_abort_zero"):
        return np.array([1.0, 0.0, 0.0])
    if control_mode != "simulink_balance":
        return np.array([0.0, 0.0, 1.0])
    if residual_mode == "none":
        return np.array([0.0, 1.0, 0.0])
    frac = float(np.clip(abs(u_residual_applied) / max(residual_max_voltage, 1e-6), 0.0, 1.0))
    return np.array([frac, 1.0 - frac, 1.0])  # cyan (0,1,1) -> magenta (1,0,1)


class LivePlot:
    """Throttled, non-blocking live scope for angle + voltage during a hardware run.

    Uses matplotlib (already a project dependency, no new install needed) rather than
    pyqtgraph. Update calls are cheap (line data + draw_idle + flush_events) and are
    rate-limited by the caller (see --live-plot-hz) so they never gate the control
    loop's own timing — the motor-voltage write always happens before this is called.
    """

    def __init__(self, window_s: float, title: str) -> None:
        import matplotlib
        import matplotlib.pyplot as plt

        matplotlib.use("TkAgg", force=False)
        plt.ion()
        self.plt = plt
        self.window_s = float(window_s)
        self.t: deque[float] = deque()
        self.alpha_deg: deque[float] = deque()
        self.theta_deg: deque[float] = deque()
        self.voltage: deque[float] = deque()
        self.residual: deque[float] = deque()

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
        self.fig.suptitle(title)
        (self.line_alpha,) = self.ax1.plot([], [], label="alpha (upright err, deg)", color="tab:orange")
        (self.line_theta,) = self.ax1.plot([], [], label="theta (arm, deg)", color="tab:blue", alpha=0.6)
        self.ax1.axhline(0.0, color="gray", linewidth=0.5)
        self.ax1.set_ylabel("deg")
        self.ax1.legend(loc="upper right", fontsize=8)
        self.ax1.grid(True, alpha=0.3)

        (self.line_v,) = self.ax2.plot([], [], label="command voltage (V)", color="tab:green")
        (self.line_res,) = self.ax2.plot([], [], label="applied residual (V)", color="tab:purple")
        self.ax2.set_ylabel("V")
        self.ax2.set_xlabel("time (s)")
        self.ax2.legend(loc="upper right", fontsize=8)
        self.ax2.grid(True, alpha=0.3)

        self.fig.tight_layout()
        plt.show(block=False)

    def push(self, t: float, alpha_deg: float, theta_deg: float, voltage: float, residual: float) -> None:
        self.t.append(t)
        self.alpha_deg.append(alpha_deg)
        self.theta_deg.append(theta_deg)
        self.voltage.append(voltage)
        self.residual.append(residual)
        cutoff = t - self.window_s
        while self.t and self.t[0] < cutoff:
            self.t.popleft()
            self.alpha_deg.popleft()
            self.theta_deg.popleft()
            self.voltage.popleft()
            self.residual.popleft()

    def redraw(self) -> None:
        if not self.t:
            return
        t_arr = list(self.t)
        self.line_alpha.set_data(t_arr, list(self.alpha_deg))
        self.line_theta.set_data(t_arr, list(self.theta_deg))
        self.line_v.set_data(t_arr, list(self.voltage))
        self.line_res.set_data(t_arr, list(self.residual))
        for ax in (self.ax1, self.ax2):
            ax.set_xlim(t_arr[0], max(t_arr[-1], t_arr[0] + 1e-3))
            ax.relim()
            ax.autoscale_view(scalex=False)
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    def close(self) -> None:
        try:
            self.plt.close(self.fig)
        except Exception:
            pass


class SimulinkDerivativeBlock:
    """Discrete implementation of 50s/(s+50)-style filtered derivative.

    Implements H(s)=w*s/(s+w) by keeping a low-pass state z:
        z_dot = w * (x - z)
        y     = w * (x - z)
    """

    def __init__(self, bandwidth_rad_s: float, sample_time_s: float) -> None:
        self.bandwidth_rad_s = float(bandwidth_rad_s)
        self.sample_time_s = float(sample_time_s)
        self.z = 0.0
        self.initialized = False

    def reset(self, x0: float = 0.0) -> None:
        self.z = float(x0)
        self.initialized = True

    def step(self, x: float, dt: float | None = None) -> float:
        # dt defaults to the nominal sample_time_s (unchanged behavior for any other
        # caller), but the main control loop passes the ACTUAL measured loop_dt — see
        # the call sites below. Without this, a one-off slow iteration (e.g. a
        # --live-plot redraw taking tens of ms instead of the nominal ~2ms) gets
        # filtered as if only sample_time_s had elapsed, producing a badly wrong
        # velocity estimate for exactly that sample — which feeds straight into the
        # PD balance law's derivative terms and shows up as a sudden control kick.
        # Fixed 2026-09-03 after this was observed making hardware harder to control
        # specifically when --live-plot was enabled.
        x = float(x)
        if not self.initialized:
            self.reset(x)
            return 0.0
        w = self.bandwidth_rad_s
        dt = self.sample_time_s if dt is None else max(float(dt), 1e-6)
        a = math.exp(-w * dt)
        z_prev = self.z
        self.z = a * self.z + (1.0 - a) * x
        # filtered derivative output
        return w * (x - z_prev)


class ShadowGateResidual:
    """Shadow-mode gate-state residual based on the HyperLIF / Adaptive HyperLIF gate.

    Computes, per control tick: a normalized ``demand_score``, a HyperLIF-family
    ``gate_state`` and Eq.7 ``conductance_state`` from a single-step neuron driven by
    control demand, a low-pass ``event_activity``, and a BOUNDED residual *candidate*.

    SAFETY: this object only *computes and reports* values. It never writes to the
    motor. The caller keeps ``u_applied = u0`` in shadow mode. The candidate is bounded
    to ``residual_max_voltage`` purely so a future applied mode would be well-scaled.

    Simplification for this first shadow build (documented on purpose): the membrane is
    a clean leaky low-pass of the demand drive, and the Eq.7 conductance is exposed as a
    *readout* (not fed back into the membrane) and the hysteresis latch is disabled
    (GAMMA=0) so the gate RELEASES cleanly on recovery. This keeps the gate/conductance/
    event timing interpretable and robust. Applied mode (later) can enable the full
    conductance feedback + latch after tuning.
    """

    # Fixed internal neuron parameters (control-rate, seconds).
    TAU = 0.05          # membrane low-pass (~50 ms)
    TAU_R = 0.02        # gate time constant (~20 ms)
    TAU_EVENT = 0.10    # event low-pass (~100 ms)
    ALPHA = 8.0         # gate sigmoid slope
    GAMMA = 0.0         # hysteresis latch DISABLED in shadow (clean release)
    V_THRESH = 1.0      # gate sigmoid center
    G_BASE = 20.0       # base conductance (Eq.5/Eq.7)
    DRIVE_GAIN = 2.5    # maps demand_score in [0,1] to membrane drive

    # Demand-score weights (sum = 1.0) and normalization references.
    W_ALPHA = 0.35
    W_ALPHA_DOT = 0.30
    W_THETA = 0.10
    W_VOLT = 0.25
    ALPHA_DOT_REF = 3.0   # rad/s
    THETA_DOT_REF = 5.0   # rad/s

    def __init__(self, neuron: str, sample_time_s: float, residual_threshold: float,
                 residual_demand_threshold: float, residual_max_voltage: float,
                 alpha_err_ref_rad: float) -> None:
        self.neuron = neuron
        self.beta = 5.0 if neuron == "adaptive_hyperlif" else 0.0  # the only HyperLIF->Adaptive difference
        self.dt = float(sample_time_s)
        self.residual_threshold = float(residual_threshold)
        self.residual_demand_threshold = float(residual_demand_threshold)
        self.residual_max_voltage = float(residual_max_voltage)
        self.alpha_err_ref_rad = max(float(alpha_err_ref_rad), 1e-6)
        self.v = 0.0
        self.r = 0.0
        self.event_filt = 0.0
        self._decay_r = math.exp(-self.dt / self.TAU_R)
        self._decay_v = math.exp(-self.dt / self.TAU)
        self._decay_event = math.exp(-self.dt / self.TAU_EVENT)

    @staticmethod
    def _sigmoid(x: float) -> float:
        if x <= -60.0:
            return 0.0
        if x >= 60.0:
            return 1.0
        return 1.0 / (1.0 + math.exp(-x))

    def demand_score(self, alpha_control: float, alpha_dot: float, theta_dot: float,
                     command_voltage: float, voltage_limit: float) -> float:
        """Stateless, normalized demand in [0, 1] from available signals."""
        a = abs(alpha_control) / self.alpha_err_ref_rad
        ad = abs(alpha_dot) / self.ALPHA_DOT_REF
        td = abs(theta_dot) / self.THETA_DOT_REF
        vv = abs(command_voltage) / max(abs(voltage_limit), 1e-6)
        d = self.W_ALPHA * a + self.W_ALPHA_DOT * ad + self.W_THETA * td + self.W_VOLT * vv
        return min(1.0, max(0.0, d))

    def step_gate(self, demand: float, alpha_control: float) -> dict[str, float]:
        """Advance the gate neuron one tick and return gate/conductance/event/candidate.

        Pure computation; does NOT touch the motor.
        """
        drive = self.DRIVE_GAIN * demand
        prev_r = self.r
        # membrane: clean leaky low-pass of the demand drive (no conductance feedback in shadow)
        self.v = self.v * self._decay_v + drive * (1.0 - self._decay_v)
        # gate update (HyperLIF gate; GAMMA=0 here so theta_eff = V_THRESH)
        theta_eff = self.V_THRESH - self.GAMMA * self.r
        r_tgt = self._sigmoid(self.ALPHA * (self.v - theta_eff))
        self.r = min(1.0, max(0.0, self.r * self._decay_r + r_tgt * (1.0 - self._decay_r)))
        gate_state = self.r
        # Eq.7 effective conductance as a readout (g_base + beta*|I|) * r^2
        conductance_state = (self.G_BASE + self.beta * abs(drive)) * (gate_state ** 2)
        # event = upward crossing of the gate through residual_threshold
        event = 1.0 if (prev_r < self.residual_threshold <= gate_state) else 0.0
        self.event_filt = self._decay_event * self.event_filt + (1.0 - self._decay_event) * event
        # bounded, interpretable residual candidate: |candidate| <= residual_max_voltage
        corrective = math.tanh(2.0 * (-alpha_control))  # corrective DIRECTION (toward upright), in [-1, 1]
        candidate = self.residual_max_voltage * corrective * gate_state * demand
        active = 1.0 if (gate_state >= self.residual_threshold and demand >= self.residual_demand_threshold) else 0.0
        return {
            "gate_state": gate_state,
            "conductance_state": conductance_state,
            "event_activity": self.event_filt,
            "u_residual_candidate": candidate,
            "residual_active_flag": active,
            "corrective": corrective,
        }


# Modes that APPLY residual voltage to the motor (always bounded by residual_max_voltage,
# total clipped by voltage_limit, and applied ONLY during active balance). 'none' and
# 'shadow_gate' are NOT here, so they never touch the motor command.
RESIDUAL_APPLIED_MODES: frozenset[str] = frozenset({"gate", "shuffled_gate", "always_on"})
RESIDUAL_MODES: tuple[str, ...] = ("none", "shadow_gate", "gate", "shuffled_gate", "always_on")


def _str2bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "t", "yes", "y", "on")


class ShuffleSource:
    """Time-misaligned gate/demand source for the shuffled_gate timing control.

    Loads gate_state (and demand_score) from a prior shadow/residual CSV and samples it
    at (elapsed + offset) wrapped, preserving the source's gate activation statistics while
    breaking alignment with the CURRENT perturbations. Used only by shuffled_gate.
    """

    def __init__(self, path: Path, offset_s: float) -> None:
        with Path(path).open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows or "gate_state" not in rows[0]:
            raise SystemExit(f"[shuffle-source] {path} has no 'gate_state' column.")

        def grab(name: str, default: float = 0.0) -> np.ndarray:
            return np.array([float(r.get(name) or default) for r in rows], dtype=float)

        self.gate = grab("gate_state")
        self.demand = grab("demand_score") if "demand_score" in rows[0] else self.gate.copy()
        t = grab("time_s")
        self.n = len(self.gate)
        diffs = np.diff(t) if self.n > 1 else np.array([0.002])
        self.dt = float(np.median(diffs)) if diffs.size and np.median(diffs) > 0 else 0.002
        self.offset = float(offset_s)

    def sample(self, elapsed: float) -> tuple[float, float]:
        idx = int(round((elapsed + self.offset) / self.dt)) % self.n
        return float(self.gate[idx]), float(self.demand[idx])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Python replication/twin of Quanser qs3_balance.slx with manual swing gating."
    )
    parser.add_argument("--version", type=int, choices=[2, 3], default=3)
    parser.add_argument("--id", type=int, default=0)
    parser.add_argument("--hardware", type=int, choices=[0, 1], default=0, help="0=virtual twin, 1=physical Qube.")
    parser.add_argument("--pendulum", type=int, choices=[0, 1], default=1)
    parser.add_argument("--sample-rate", type=float, default=500.0)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--armed", action="store_true", help="Required for nonzero motor voltage.")
    parser.add_argument("--voltage-limit", type=float, default=5.0)

    # qs3_balance.slx default values visible in the Simulink diagram
    parser.add_argument("--theta-ref-deg", type=float, default=30.0)
    parser.add_argument("--kp-theta", type=float, default=-2.0)
    parser.add_argument("--kd-theta", type=float, default=-2.0)
    parser.add_argument("--kp-alpha", type=float, default=30.0)
    parser.add_argument("--kd-alpha", type=float, default=2.5)
    parser.add_argument("--derivative-bandwidth", type=float, default=50.0)
    parser.add_argument("--motor-sign", type=float, default=-1.0)

    # Important when Python/PAL and Simulink/QUARC use different pendulum zero references.
    # Use 0 when alpha=0 means upright. Use 180 when alpha=pi/-pi means upright.
    parser.add_argument("--alpha-upright-offset-deg", type=float, default=0.0)

    # Simulink-like switching plus safer Python/hardware options.
    parser.add_argument("--capture-angle-deg", type=float, default=10.0)
    parser.add_argument("--capture-hysteresis-deg", type=float, default=2.0)
    parser.add_argument("--engage-confirm-samples", type=int, default=5)
    parser.add_argument("--max-engage-alpha-dot", type=float, default=float("inf"))
    parser.add_argument("--require-manual-swing", action="store_true")
    parser.add_argument("--manual-swing-release-deg", type=float, default=15.0)

    # Better hardware behavior: avoid the fixed 30-deg command causing a large jump at engagement.
    parser.add_argument(
        "--theta-ref-mode",
        choices=["fixed", "current_on_engage"],
        default="fixed",
        help="fixed reproduces qs3_balance.slx. current_on_engage latches theta_ref to current base angle when balance first engages.",
    )
    parser.add_argument("--soft-start-s", type=float, default=0.0, help="Ramp motor command after engagement.")
    parser.add_argument("--reset-control-filters-on-engage", action="store_true")

    # --- Automatic (energy-pumping) swing-up, in place of --require-manual-swing ---
    # Law and physical constants pulled directly from Quanser's own validated model:
    # C:\Users\gandhico\Documents\Quanser\6_teaching\1_Controls\Qube_Servo_3\
    #   sp6_pendulum_control\2_swingup_control\digital_twin\matlab\{qs3_swingup.slx,
    #   setup_swingup.m, qube3_rotpen_param.m}
    # Formula (extracted from the .slx block diagram, "Energy-Based Swing-Up Control"):
    #   Jp_cm = mp*Lp^2/12                                (pendulum inertia about its own CoM)
    #   E     = 0.5*Jp_cm*alpha_dot^2 + mp*g*l*(1-cos(alpha))   (KE + PE, alpha=0 hanging)
    #   Er    = 2*mp*g*l                                  (PE needed to just reach upright)
    #   pump  = sign(alpha_dot*cos(alpha))
    #   u_accel = clip(ke*(E-Er)*pump, -a_max, a_max)     (ke=50 is the model's own slider default)
    #   V_swingup = clip(u_accel*mr*r*Rm/kt, -voltage_limit, voltage_limit)  (accel -> torque -> voltage)
    # This replaces an earlier ad-hoc formula (non-physical omega0^2 energy scale, ke~0.2-0.35)
    # that was ~140x too weak relative to Quanser's own validated ke=50 on the correct Joule scale.
    parser.add_argument(
        "--auto-swing-up",
        action="store_true",
        help="Actively pump energy into the pendulum instead of waiting for a manual swing. "
        "Overrides --require-manual-swing (no human swing needed). Uses the existing "
        "capture/hysteresis/confirm-samples logic to hand off to balance once inside the capture band.",
    )
    # QUBE-Servo 3 physical parameters, from qube3_rotpen_param.m (do not change unless the
    # physical hardware unit is actually different from Quanser's stock QUBE-Servo 3).
    parser.add_argument("--swingup-mp-kg", type=float, default=0.024, help="Pendulum link mass (kg).")
    parser.add_argument("--swingup-lp-m", type=float, default=0.129, help="Pendulum link total length (m).")
    parser.add_argument("--swingup-mr-kg", type=float, default=0.095, help="Rotary arm mass (kg).")
    parser.add_argument("--swingup-r-m", type=float, default=0.085, help="Rotary arm length (m).")
    parser.add_argument("--swingup-rm-ohm", type=float, default=7.5, help="Motor resistance (Ohm).")
    parser.add_argument("--swingup-kt-nm-a", type=float, default=0.0422, help="Motor current-torque constant (N.m/A).")
    # Swing-up law tuning — ke=50 matches Quanser's own model default exactly (0-100 slider range).
    parser.add_argument("--swingup-k-energy", type=float, default=50.0, help="ke (m/s/J): energy-pump gain. 50.0 is Quanser's own validated default.")
    parser.add_argument("--swingup-k-theta", type=float, default=2.5, help="Arm-centering gain during swing-up (this runner's own addition, not in the stock Quanser model — it has no arm-centering term).")
    parser.add_argument("--swingup-k-theta-dot", type=float, default=0.5, help="Arm-rate damping gain during swing-up (this runner's own addition).")
    parser.add_argument("--swingup-slew-v-per-s", type=float, default=500.0, help="Max swing-up voltage slew rate (V/s).")
    parser.add_argument("--swingup-theta-abort-deg", type=float, default=120.0, help="Hard safety stop if |theta| exceeds this during auto swing-up.")
    parser.add_argument(
        "--swingup-pump-hysteresis",
        type=float,
        default=0.15,
        help="Deadband (rad/s-scale) on the pump-direction switching signal "
        "alpha_dot*cos(alpha). Below this magnitude, the PREVIOUS pump direction is "
        "held instead of re-evaluating sign(); prevents rapid direction-flip chatter "
        "(motor buzzing, flickering LED) right at each swing's zero-crossing, where "
        "sensor noise would otherwise flip the sign many times per pass.",
    )
    parser.add_argument(
        "--swingup-theta-guard-deg",
        type=float,
        default=45.0,
        help="Soft guard: once |theta| exceeds this, pump authority is progressively "
        "tapered toward zero (and centering strengthened) as theta approaches "
        "--swingup-theta-abort-deg, so the arm can't wander toward its hard limit and "
        "eat into the rotation range needed to balance. Set >= the abort angle to disable.",
    )

    # --- Real-time visualization ---
    parser.add_argument(
        "--live-plot",
        action="store_true",
        help="Open a live matplotlib window (angle + voltage vs. time, rolling window). "
        "Throttled to --live-plot-hz to avoid disturbing the control loop.",
    )
    parser.add_argument("--live-plot-hz", type=float, default=6.0, help="Live-plot redraw rate (Hz). Lowered from 10 on 2026-09-03 — redraws still cost tens of ms each; fewer of them means fewer chances to fall behind, on top of the dt-aware derivative fix above.")
    parser.add_argument("--live-plot-window-s", type=float, default=12.0, help="Rolling time window shown on the live plot (s).")

    parser.add_argument("--quanser-python", type=Path, default=DEFAULT_QUANSER_PYTHON)
    parser.add_argument("--log-root", type=Path, default=PROJECT_ROOT / "results" / "online")
    parser.add_argument("--log-prefix", type=str, default="qube3")
    parser.add_argument("--print-rate", type=float, default=10.0)

    # --- Gate-state residual (controlled applied mini-ablation) ---
    # none/shadow_gate never touch the motor. gate/shuffled_gate/always_on apply a residual
    # bounded by --residual-max-voltage, ONLY during active balance, total clipped to the
    # motor voltage limit.
    parser.add_argument(
        "--residual-mode",
        choices=list(RESIDUAL_MODES),
        default="none",
        help="none=classical only; shadow_gate=compute+log only (no apply); "
        "gate=demand-triggered applied residual; shuffled_gate=timing control (misaligned gate); "
        "always_on=ungated applied residual. Applied modes act ONLY in active balance.",
    )
    parser.add_argument("--residual-scale", type=float, default=0.0,
                        help="Applied residual scale. Safety is enforced by --residual-max-voltage, so use 1.0 for applied modes.")
    parser.add_argument("--residual-sign", type=float, default=1.0, help="Sign/orientation multiplier for the applied residual.")
    parser.add_argument("--residual-neuron", choices=["hyperlif", "adaptive_hyperlif"], default="adaptive_hyperlif")
    parser.add_argument("--residual-threshold", type=float, default=0.15, help="Gate activation level for event/active detection.")
    parser.add_argument("--residual-demand-threshold", type=float, default=0.20, help="Demand level above which the residual is considered 'active'.")
    parser.add_argument("--residual-max-voltage", type=float, default=0.25, help="Hard bound on the applied residual magnitude (V). Independent of the motor limit.")
    parser.add_argument("--residual-shuffle-source", type=Path, default=None, help="Optional prior CSV providing the (misaligned) gate signal for shuffled_gate.")
    parser.add_argument("--residual-shuffle-offset-s", type=float, default=5.0, help="Time offset (s) used to misalign the shuffled gate.")
    parser.add_argument("--residual-apply-active-only", type=str, default="true", help="true/false. Active-balance-only application (ENFORCED for safety regardless).")
    parser.add_argument("--residual-log-prefix", type=str, default=None, help="Optional log filename prefix override for residual runs.")
    return parser.parse_args(argv)


def zero_row_reason(reason: str) -> str:
    return reason


def run(args: argparse.Namespace) -> Path:
    residual_mode = str(args.residual_mode)
    if residual_mode not in RESIDUAL_MODES:
        raise SystemExit(f"[BLOCKED] unknown --residual-mode '{residual_mode}'.")
    residual_applied = residual_mode in RESIDUAL_APPLIED_MODES  # gate / shuffled_gate / always_on
    residual_sign = float(args.residual_sign)
    residual_max_voltage = float(args.residual_max_voltage)
    apply_active_only = _str2bool(args.residual_apply_active_only)

    ensure_quanser_python(args.quanser_python)
    qube_cls = get_qube_class(args.version)

    sample_rate = float(args.sample_rate)
    sample_time = 1.0 / sample_rate
    args.log_root.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_prefix = args.residual_log_prefix or args.log_prefix
    log_path = args.log_root / f"{log_prefix}_simulink_balance_{timestamp}.csv"

    stop_requested = False

    def request_stop(_signum: int | None = None, _frame: Any = None) -> None:
        nonlocal stop_requested
        stop_requested = True
        print("\nStop requested. Sending zero voltage and closing Qube...")

    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)

    print("Starting Python qs3_balance.slx replication.")
    print(f"Hardware flag: {args.hardware} (0=virtual, 1=physical)")
    print(f"Armed: {args.armed}")
    print(f"Alpha upright offset: {args.alpha_upright_offset_deg:.1f} deg")
    print(f"Theta reference mode: {args.theta_ref_mode}")
    print("=" * 64)
    print(f"RESIDUAL MODE: {residual_mode}   |   neuron: {args.residual_neuron}")
    if residual_applied:
        print(f"RESIDUAL APPLIED TO MOTOR: *** YES *** (active balance only; "
              f"|residual| <= {residual_max_voltage:.3f} V; total clipped to +/-{args.voltage_limit:.2f} V)")
    elif residual_mode == "shadow_gate":
        print("RESIDUAL APPLIED TO MOTOR: NO  (SHADOW: computed + logged only; u_applied = u0)")
    else:
        print("RESIDUAL APPLIED TO MOTOR: NO  (classical controller only)")
    print(f"  residual_scale       = {args.residual_scale}")
    print(f"  residual_sign        = {residual_sign}")
    print(f"  residual_max_voltage = {residual_max_voltage} V")
    print(f"  apply_active_only    = {apply_active_only}  (active-balance-only is ENFORCED regardless)")
    print(f"  gate_thr={args.residual_threshold}, demand_thr={args.residual_demand_threshold}")
    if residual_mode == "shuffled_gate":
        src = args.residual_shuffle_source if args.residual_shuffle_source else "(in-run delayed buffer)"
        print(f"  shuffle_source={src}, shuffle_offset_s={args.residual_shuffle_offset_s}")
    if residual_applied and not apply_active_only:
        print("  NOTE: active-balance-only is ENFORCED for hardware safety; the false flag is "
              "recorded but does NOT relax the gate.")
    print("=" * 64)
    print(f"Log: {log_path}")
    print("Press Ctrl+C to stop safely.")

    fieldnames = [
        "time_s",
        "mode",
        "armed",
        "hardware",
        "control_mode",
        "loop_dt_s",
        "theta_rad",
        "theta_ref_active_rad",
        "alpha_raw_rad",
        "alpha_control_rad",
        "theta_dot_sim_rad_s",
        "alpha_dot_sim_rad_s",
        "motor_current_a",
        "amplifier_fault",
        "motor_stall_detected",
        "motor_stall_error",
        "command_voltage",
        # --- shadow gate-state residual columns (logging only) ---
        "residual_mode",
        "residual_scale",
        "u0_command",
        "u_residual_candidate",
        "u_residual_applied",
        "u_total_command",
        "demand_score",
        "saturation_proximity",
        "gate_state",
        "conductance_state",
        "event_activity",
        "residual_active_flag",
        "residual_neuron",
        "residual_threshold",
        "residual_sign",
        "residual_apply_active_only",
        "residual_max_voltage",
        "residual_energy",
        "applied_residual_energy",
        "applied_residual_active_flag",
        "controller_info_json",
        "state_json",
    ]

    rows: list[dict[str, Any]] = []
    qube = None

    # Filters required by read_state when tachometer is not used.
    state_theta_filter = DerivativeFilter(bandwidth_rad_s=50.0, sample_time_s=sample_time)
    state_alpha_filter = DerivativeFilter(bandwidth_rad_s=50.0, sample_time_s=sample_time)

    # Simulink derivative blocks for -theta and -alpha.
    theta_dot_block = SimulinkDerivativeBlock(args.derivative_bandwidth, sample_time)
    alpha_dot_block = SimulinkDerivativeBlock(args.derivative_bandwidth, sample_time)

    # Gate-state residual neuron (drives the motor only in applied modes, active balance only).
    residual_gate = ShadowGateResidual(
        neuron=args.residual_neuron,
        sample_time_s=sample_time,
        residual_threshold=args.residual_threshold,
        residual_demand_threshold=args.residual_demand_threshold,
        residual_max_voltage=residual_max_voltage,
        alpha_err_ref_rad=math.radians(float(args.capture_angle_deg) + float(args.capture_hysteresis_deg)),
    )
    # shuffled_gate timing source: external prior log (if given) else an in-run delayed buffer.
    shuffle_source = None
    if residual_mode == "shuffled_gate" and args.residual_shuffle_source:
        shuffle_source = ShuffleSource(args.residual_shuffle_source, float(args.residual_shuffle_offset_s))
    shuffle_buf: deque[tuple[float, float]] = deque(
        maxlen=max(1, int(round(float(args.residual_shuffle_offset_s) * sample_rate)))
    )

    manual_swing_seen = not bool(args.require_manual_swing)
    if args.auto_swing_up:
        manual_swing_seen = True  # auto swing-up does not wait for a human
    capture_count = 0
    balance_has_engaged = False
    active_latch = False
    engage_time = None
    theta_ref_active = math.radians(float(args.theta_ref_deg))
    last_print_time = -1e9
    next_tick = None

    # Auto swing-up state — Quanser's own qs3_swingup.slx energy law (see argparse comment above).
    g_const = 9.81
    swingup_mp = float(args.swingup_mp_kg)
    swingup_lp = float(args.swingup_lp_m)
    swingup_l = swingup_lp / 2.0  # center-of-mass distance, matches qube3_rotpen_param.m's `l = Lp/2`
    swingup_jp_cm = swingup_mp * swingup_lp**2 / 12.0
    swingup_mgl = swingup_mp * g_const * swingup_l
    swingup_er = 2.0 * swingup_mgl
    swingup_mr = float(args.swingup_mr_kg)
    swingup_r = float(args.swingup_r_m)
    swingup_rm = float(args.swingup_rm_ohm)
    swingup_kt = float(args.swingup_kt_nm_a)
    # accel(m/s^2) -> torque(N.m) -> voltage(V), same chain as setup_swingup.m's tau_max/a_max.
    swingup_accel_to_volts = swingup_mr * swingup_r * swingup_rm / max(swingup_kt, 1e-9)
    swingup_tau_max = swingup_kt * float(args.voltage_limit) / max(swingup_rm, 1e-9)
    swingup_a_max = swingup_tau_max / max(swingup_mr * swingup_r, 1e-9)
    swingup_u_prev = 0.0
    swingup_pump_sign = 1.0  # persists across samples; only changes outside the hysteresis deadband
    fault_reported = False  # edge-trigger: print the hardware fault diagnostic only once
    swingup_du_max_per_sample = float(args.swingup_slew_v_per_s) * sample_time
    theta_abort_rad = math.radians(float(args.swingup_theta_abort_deg))
    theta_guard_rad = math.radians(float(args.swingup_theta_guard_deg))

    live_plot = None
    last_plot_time = -1e9
    plot_period_s = 1.0 / max(float(args.live_plot_hz), 1e-6)

    alpha_offset_rad = math.radians(float(args.alpha_upright_offset_deg))
    capture_rad = math.radians(float(args.capture_angle_deg))
    release_rad = math.radians(float(args.capture_angle_deg) + float(args.capture_hysteresis_deg))
    manual_release_rad = math.radians(float(args.manual_swing_release_deg))

    try:
        qube = qube_cls(
            id=args.id,
            hardware=args.hardware,
            frequency=int(round(sample_rate)),
            pendulum=args.pendulum,
            readMode=1,
        )
        qube.write_voltage(0.0)

        if args.auto_swing_up:
            _startup_state = read_state(
                qube, time_s=0.0,
                theta_filter=DerivativeFilter(bandwidth_rad_s=50.0, sample_time_s=sample_time),
                alpha_filter=DerivativeFilter(bandwidth_rad_s=50.0, sample_time_s=sample_time),
                sample_time_s=sample_time, use_tachometer=False, alpha_offset_rad=0.0,
            )
            _theta0_deg = math.degrees(float(_startup_state.theta_rad))
            print(f"Arm start position: theta={_theta0_deg:+.1f} deg from encoder zero (this run's 'center').")
            if abs(_theta0_deg) > float(args.swingup_theta_guard_deg):
                print(
                    f"  WARNING: this is already past the {args.swingup_theta_guard_deg:.0f} deg soft guard — "
                    "the arm has likely drifted from prior runs. Consider power-cycling the Qube or "
                    "manually re-centering the arm by hand before arming, so the full rotation range "
                    "is available for swing-up + balance."
                )

        if args.live_plot:
            live_plot = LivePlot(
                window_s=float(args.live_plot_window_s),
                title=f"Qube live | residual_mode={residual_mode} | hardware={args.hardware}",
            )

        start = time.perf_counter()
        last_loop = start
        next_tick = start

        while not stop_requested:
            now = time.perf_counter()
            elapsed = now - start
            if elapsed > float(args.duration):
                break

            loop_dt = max(now - last_loop, sample_time)
            last_loop = now

            state = read_state(
                qube,
                time_s=elapsed,
                theta_filter=state_theta_filter,
                alpha_filter=state_alpha_filter,
                sample_time_s=sample_time,
                use_tachometer=False,
                # This runner applies its own upright offset below via
                # --alpha-upright-offset-deg / alpha_offset_rad — read_state must
                # return the RAW (unshifted) angle here, or the two offsets stack
                # to 2*pi and cancel out (see qube_io.read_state's docstring note).
                alpha_offset_rad=0.0,
            )

            theta = float(state.theta_rad)
            alpha_raw = float(state.alpha_rad)
            alpha_control = wrap_to_pi(alpha_raw - alpha_offset_rad)

            # The Simulink diagram applies Transfer Fcn blocks to -theta and -alpha.
            theta_dot_sim = theta_dot_block.step(-theta, loop_dt)
            alpha_dot_sim = alpha_dot_block.step(-alpha_control, loop_dt)

            has_fault = bool(state.amplifier_fault or state.motor_stall_detected or state.motor_stall_error)

            abs_alpha = abs(alpha_control)
            inside_capture_now = abs_alpha <= capture_rad
            outside_release = abs_alpha >= release_rad

            if args.require_manual_swing and not manual_swing_seen:
                # Do not let startup alpha=0 accidentally arm the balance controller.
                if abs_alpha >= manual_release_rad:
                    manual_swing_seen = True

            allow_velocity = abs(alpha_dot_sim) <= float(args.max_engage_alpha_dot)

            # Simulink-like switch behavior:
            #   - Before engagement, optional velocity and confirmation gates avoid accidental catches.
            #   - After engagement, keep applying the balance law while the pendulum remains inside
            #     the release band. Do NOT disable only because alpha_dot becomes high; that was
            #     suppressing the controller exactly during the catch.
            if active_latch and outside_release:
                active_latch = False
                capture_count = 0

            just_engaged = False
            if not active_latch:
                if manual_swing_seen and inside_capture_now and allow_velocity:
                    capture_count += 1
                else:
                    capture_count = 0

                if capture_count >= int(args.engage_confirm_samples):
                    active_latch = True
                    just_engaged = True
                    balance_has_engaged = True
                    engage_time = elapsed
                    if args.theta_ref_mode == "current_on_engage":
                        theta_ref_active = theta
                    if args.reset_control_filters_on_engage:
                        theta_dot_block.reset(-theta)
                        alpha_dot_block.reset(-alpha_control)
                        theta_dot_sim = 0.0
                        alpha_dot_sim = 0.0

            enabled = bool(args.armed) and not has_fault and manual_swing_seen and active_latch

            theta_error = theta_ref_active - theta
            neg_alpha = -alpha_control

            controller_voltage_before_motor_sign = (
                float(args.kp_theta) * theta_error
                + float(args.kd_theta) * theta_dot_sim
                + float(args.kp_alpha) * neg_alpha
                + float(args.kd_alpha) * alpha_dot_sim
            )
            raw_voltage = float(args.motor_sign) * controller_voltage_before_motor_sign

            if enabled and engage_time is not None and float(args.soft_start_s) > 0.0:
                ramp = min(1.0, max(0.0, (elapsed - engage_time) / float(args.soft_start_s)))
                raw_voltage *= ramp

            voltage = float(np.clip(raw_voltage, -float(args.voltage_limit), float(args.voltage_limit)))

            # Auto swing-up: Quanser's own qs3_swingup.slx energy law, expressed in THIS
            # file's variables. alpha_raw is hanging-referenced (0=down) because read_state()
            # above is called with alpha_offset_rad=0.0, matching the model's own convention
            # exactly. alpha_dot_sim here is the derivative of -alpha_control
            # (== -alpha_raw up to a constant shift), so the raw-convention rate is its negation.
            theta_abort = bool(args.auto_swing_up) and abs(theta) > theta_abort_rad
            swingup_voltage = 0.0
            if args.auto_swing_up and not theta_abort:
                alpha_dot_raw = -alpha_dot_sim
                kinetic_energy = 0.5 * swingup_jp_cm * alpha_dot_raw**2
                potential_energy = swingup_mgl * (1.0 - math.cos(alpha_raw))
                energy = kinetic_energy + potential_energy
                energy_error = energy - swingup_er
                pump_signal = alpha_dot_raw * math.cos(alpha_raw)
                # Schmitt-trigger pump direction: only flip sign once |pump_signal| clears the
                # hysteresis deadband; otherwise hold the previous direction. Without this, sensor
                # noise right at each swing's zero-crossing flips the sign many times per pass,
                # producing rapid direction-reversal chatter (buzzing motor, flickering LED) that
                # wastes most of the pumped energy instead of driving a clean swing. The deadband
                # also covers the at-rest degenerate case (pump_signal ~= 0 at startup) by simply
                # holding the initial default direction (+1) until real motion breaks it.
                if abs(pump_signal) > float(args.swingup_pump_hysteresis):
                    swingup_pump_sign = math.copysign(1.0, pump_signal)
                pump = swingup_pump_sign

                # Arm-range guard: once |theta| exceeds --swingup-theta-guard-deg, linearly
                # taper pump authority to 0 by --swingup-theta-abort-deg, and correspondingly
                # boost the centering terms — so a run of pump kicks in the same direction
                # can't walk the arm into its hard limit and eat into the rotation range the
                # balance phase needs. taper=1 below the guard angle (full pump, normal
                # centering); taper=0 at/beyond the abort angle (no pump, max centering).
                abs_theta = abs(theta)
                if abs_theta <= theta_guard_rad or theta_abort_rad <= theta_guard_rad:
                    taper = 1.0
                else:
                    taper = 1.0 - min(1.0, (abs_theta - theta_guard_rad) / (theta_abort_rad - theta_guard_rad))
                centering_boost = 1.0 + 2.0 * (1.0 - taper)  # up to 3x centering authority near the limit

                # ke*(E-Er)*pump -> saturate at a_max (m/s^2) -> convert to volts via the
                # motor's own torque constant, exactly matching setup_swingup.m's
                # tau_max/a_max derivation. Arm-centering (this runner's own addition, not
                # in the stock Quanser model) is added afterward, directly in volts.
                u_accel = float(args.swingup_k_energy) * energy_error * pump * taper
                u_accel = float(np.clip(u_accel, -swingup_a_max, swingup_a_max))
                u_sw_energy_volts = u_accel * swingup_accel_to_volts

                u_sw = (
                    u_sw_energy_volts
                    - float(args.swingup_k_theta) * theta * centering_boost
                    - float(args.swingup_k_theta_dot) * theta_dot_sim * centering_boost
                )
                u_sw = float(np.clip(u_sw, -float(args.voltage_limit), float(args.voltage_limit)))
                du = float(np.clip(u_sw - swingup_u_prev, -swingup_du_max_per_sample, swingup_du_max_per_sample))
                swingup_voltage = swingup_u_prev + du
                swingup_u_prev = swingup_voltage

            if not args.armed:
                control_mode = "not_armed_zero"
                voltage = 0.0
            elif has_fault:
                control_mode = "fault_zero"
                voltage = 0.0
                swingup_u_prev = 0.0
                if not fault_reported:
                    fault_reported = True
                    print(
                        f"\nHARDWARE FAULT at t={elapsed:.2f}s (theta={math.degrees(theta):+.1f} deg, "
                        f"alpha={math.degrees(alpha_control):+.1f} deg): "
                        f"amplifier_fault={state.amplifier_fault} "
                        f"motor_stall_detected={state.motor_stall_detected} "
                        f"motor_stall_error={state.motor_stall_error}. "
                        "Motor forced to 0V for the rest of this run (or until the flag clears)."
                    )
            elif theta_abort:
                control_mode = "swingup_theta_abort_zero"
                voltage = 0.0
                swingup_u_prev = 0.0
                stop_requested = True
                print(f"\nAuto swing-up safety abort: |theta|={math.degrees(theta):.1f} deg exceeds "
                      f"--swingup-theta-abort-deg={args.swingup_theta_abort_deg}. Stopping.")
            elif not manual_swing_seen:
                control_mode = "waiting_for_manual_swing_zero"
                voltage = 0.0
            elif not enabled:
                if args.auto_swing_up:
                    control_mode = "auto_swing_up"
                    voltage = swingup_voltage
                elif not inside_capture_now:
                    control_mode = "waiting_for_capture_zero"
                elif not allow_velocity:
                    control_mode = "waiting_for_slow_capture_zero"
                else:
                    control_mode = "waiting_for_confirm_zero"
                if not args.auto_swing_up:
                    voltage = 0.0
            else:
                control_mode = "simulink_balance"
                swingup_u_prev = 0.0

            # ---- Gate-state residual: computed BEFORE the motor write ----
            # u0 is the classical command. none/shadow_gate keep applied = 0 (motor gets u0).
            # Applied modes (gate/shuffled_gate/always_on) add a residual that is:
            #   (a) nonzero ONLY during active balance (control_mode == "simulink_balance"),
            #   (b) hard-clipped to +/- residual_max_voltage, and
            #   (c) summed with u0 and clipped to the motor voltage limit.
            u0_command = voltage
            saturation_proximity = min(1.0, abs(voltage) / max(float(args.voltage_limit), 1e-6))
            is_active_balance = (control_mode == "simulink_balance")
            demand_score = 0.0
            res = {
                "gate_state": 0.0, "conductance_state": 0.0, "event_activity": 0.0,
                "u_residual_candidate": 0.0, "residual_active_flag": 0.0, "corrective": 0.0,
            }
            u_residual_applied = 0.0
            u_total_command = u0_command
            motor_voltage = voltage  # default: classical only (safe fallback on any error)
            try:
                if residual_mode != "none":
                    demand_score = residual_gate.demand_score(
                        alpha_control, alpha_dot_sim, theta_dot_sim, voltage, float(args.voltage_limit)
                    )
                    res = residual_gate.step_gate(demand_score, alpha_control)

                # shuffled_gate: sample a TIME-MISALIGNED gate/demand (external log or in-run delay),
                # advancing the in-run buffer every tick so its timeline tracks real time.
                sg, sd = 0.0, 0.0
                if residual_mode == "shuffled_gate":
                    if shuffle_source is not None:
                        sg, sd = shuffle_source.sample(elapsed)
                    else:
                        if len(shuffle_buf) == shuffle_buf.maxlen:
                            sg, sd = shuffle_buf[0]
                        shuffle_buf.append((res["gate_state"], demand_score))

                # HARD SAFETY RULE: applied residual is nonzero ONLY during active balance.
                if residual_applied and is_active_balance:
                    scale = float(args.residual_scale)
                    if residual_mode == "gate":
                        base = residual_sign * scale * res["u_residual_candidate"]
                    elif residual_mode == "always_on":
                        # ungated: corrective direction at full (capped) magnitude, no gate/demand factor
                        base = residual_sign * scale * (residual_max_voltage * res["corrective"])
                    elif residual_mode == "shuffled_gate":
                        base = residual_sign * scale * (residual_max_voltage * res["corrective"] * sg * sd)
                    else:
                        base = 0.0
                    u_residual_applied = float(np.clip(base, -residual_max_voltage, residual_max_voltage))

                u_total_command = float(np.clip(
                    u0_command + u_residual_applied, -float(args.voltage_limit), float(args.voltage_limit)
                ))
                motor_voltage = u_total_command
            except Exception:
                # Any residual error -> classical-only command. Never crash, never unsafe.
                u_residual_applied = 0.0
                u_total_command = u0_command
                motor_voltage = voltage

            qube.write_voltage(motor_voltage)
            try:
                qube.write_led(led_for_state(control_mode, residual_mode, u_residual_applied, residual_max_voltage))
            except Exception:
                pass  # LED is cosmetic; never let it affect the control loop.

            if live_plot is not None:
                live_plot.push(
                    t=elapsed,
                    alpha_deg=math.degrees(alpha_control),
                    theta_deg=math.degrees(theta),
                    voltage=motor_voltage,
                    residual=u_residual_applied,
                )
                if elapsed - last_plot_time >= plot_period_s:
                    last_plot_time = elapsed
                    try:
                        live_plot.redraw()
                    except Exception:
                        pass  # Plotting is cosmetic; never let it affect the control loop.

            residual_energy = (res["u_residual_candidate"] ** 2) * loop_dt
            applied_residual_energy = (u_residual_applied ** 2) * loop_dt
            # "meaningful actuation" floor (1 mV): negligible residuals don't count as applied.
            applied_residual_active_flag = 1.0 if abs(u_residual_applied) > 1.0e-3 else 0.0

            info = {
                "theta_ref_deg": float(args.theta_ref_deg),
                "theta_ref_active_deg": math.degrees(theta_ref_active),
                "theta_ref_mode": args.theta_ref_mode,
                "alpha_upright_offset_deg": float(args.alpha_upright_offset_deg),
                "capture_angle_deg": float(args.capture_angle_deg),
                "capture_hysteresis_deg": float(args.capture_hysteresis_deg),
                "kp_theta": float(args.kp_theta),
                "kd_theta": float(args.kd_theta),
                "kp_alpha": float(args.kp_alpha),
                "kd_alpha": float(args.kd_alpha),
                "derivative_bandwidth_rad_s": float(args.derivative_bandwidth),
                "motor_sign": float(args.motor_sign),
                "inside_capture": float(inside_capture_now),
                "enabled": float(enabled),
                "capture_count": int(capture_count),
                "require_manual_swing": float(args.require_manual_swing),
                "manual_swing_seen": float(manual_swing_seen),
                "manual_swing_release_deg": float(args.manual_swing_release_deg),
                "theta_error_rad": theta_error,
                "alpha_raw_rad": alpha_raw,
                "alpha_control_rad": alpha_control,
                "neg_alpha_rad": neg_alpha,
                "theta_dot_sim_rad_s": theta_dot_sim,
                "alpha_dot_sim_rad_s": alpha_dot_sim,
                "max_engage_alpha_dot": float(args.max_engage_alpha_dot),
                "controller_voltage_before_motor_sign": controller_voltage_before_motor_sign,
                "raw_voltage_before_clip": raw_voltage,
                "soft_start_s": float(args.soft_start_s),
                "balance_has_engaged": float(balance_has_engaged),
                "active_latch": float(active_latch),
            }

            rows.append(
                {
                    "time_s": elapsed,
                    "mode": "simulink_balance_manual_swing",
                    "armed": int(bool(args.armed)),
                    "hardware": int(args.hardware),
                    "control_mode": control_mode,
                    "loop_dt_s": loop_dt,
                    "theta_rad": theta,
                    "theta_ref_active_rad": theta_ref_active,
                    "alpha_raw_rad": alpha_raw,
                    "alpha_control_rad": alpha_control,
                    "theta_dot_sim_rad_s": theta_dot_sim,
                    "alpha_dot_sim_rad_s": alpha_dot_sim,
                    "motor_current_a": state.motor_current_a,
                    "amplifier_fault": state.amplifier_fault,
                    "motor_stall_detected": state.motor_stall_detected,
                    "motor_stall_error": state.motor_stall_error,
                    "command_voltage": voltage,
                    "residual_mode": residual_mode,
                    "residual_scale": float(args.residual_scale),
                    "u0_command": u0_command,
                    "u_residual_candidate": res["u_residual_candidate"],
                    "u_residual_applied": u_residual_applied,
                    "u_total_command": u_total_command,
                    "demand_score": demand_score,
                    "saturation_proximity": saturation_proximity,
                    "gate_state": res["gate_state"],
                    "conductance_state": res["conductance_state"],
                    "event_activity": res["event_activity"],
                    "residual_active_flag": res["residual_active_flag"],
                    "residual_neuron": args.residual_neuron,
                    "residual_threshold": float(args.residual_threshold),
                    "residual_sign": residual_sign,
                    "residual_apply_active_only": int(bool(apply_active_only)),
                    "residual_max_voltage": residual_max_voltage,
                    "residual_energy": residual_energy,
                    "applied_residual_energy": applied_residual_energy,
                    "applied_residual_active_flag": applied_residual_active_flag,
                    "controller_info_json": json.dumps(info, default=str),
                    "state_json": json.dumps(asdict(state), default=str),
                }
            )

            if elapsed - last_print_time >= 1.0 / max(float(args.print_rate), 1e-6):
                last_print_time = elapsed
                print(
                    f"t={elapsed:5.2f}s | {control_mode:30s} | "
                    f"theta={math.degrees(theta):+7.2f} deg | "
                    f"theta_ref={math.degrees(theta_ref_active):+7.2f} deg | "
                    f"alpha_raw={math.degrees(alpha_raw):+7.2f} deg | "
                    f"alpha_ctrl={math.degrees(alpha_control):+7.2f} deg | "
                    f"adot={alpha_dot_sim:+5.2f} | V={voltage:+5.2f}",
                    end="\r",
                    flush=True,
                )

            next_tick += sample_time
            sleep_time = next_tick - time.perf_counter()
            if sleep_time > 0.0:
                time.sleep(sleep_time)
            elif sleep_time < -0.5:
                next_tick = time.perf_counter()

    finally:
        print("\nCommanding Qube to zero voltage...")
        if qube is not None:
            try:
                qube.write_led(np.array([1.0, 0.0, 0.0]))
            except Exception:
                pass
        safe_stop_qube(qube)
        if live_plot is not None:
            live_plot.close()
        with log_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Finished safely. Log saved to: {log_path}")

    return log_path


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()

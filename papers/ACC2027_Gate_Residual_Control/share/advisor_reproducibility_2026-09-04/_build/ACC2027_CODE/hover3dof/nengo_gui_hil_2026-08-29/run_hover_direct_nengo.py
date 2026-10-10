"""Run the real Quanser 3DOF Hover rig directly through the Nengo CMG-PES
worker, with NO nengo_gui dashboard/server/browser involved at all -- this
removes the GUI-thread/websocket contention that was causing the 200Hz
hardware loop to miss its deadline when a GUI was attached.

Same HoverWorker engine, same safety gates (armed requires io=q8, requires
--confirm-hardware-review, only pd/nengo-pes may be armed), same trace.csv/
neural_trace_2khz.npz/summary.json outputs as the GUI path -- verified by
reading _save() in hover_nengo_hil_gui.py directly: none of that logic
depends on nengo_gui being present.
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

CONTROLLERS = (
    "pd", "nengo-pes", "nengo-nef-pes", "nengo-cmg-fixed",
    "nengo-lif-fixed", "nengo-lif-pes",
    "nengo-alif-fixed", "nengo-alif-pes",
    "nengo-izhikevich-fixed", "nengo-izhikevich-pes",
    "nengo-lifrate-fixed", "nengo-lifrate-pes",
)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--io", choices=("emulated", "q8"), default="q8")
    p.add_argument("--armed", action="store_true")
    p.add_argument("--confirm-hardware-review", action="store_true")
    p.add_argument("--controller", choices=CONTROLLERS, required=True)
    p.add_argument("--mission", choices=("hover", "roll", "full3", "hard45", "hardstep", "yaw360"), required=True)
    p.add_argument("--duration", type=float, default=5.0)
    p.add_argument("--reference-scale", type=float, default=1.0)
    p.add_argument("--hardstep-transition-s", type=float, default=0.0)
    p.add_argument("--beta", type=float, default=0.2)
    p.add_argument("--motor-residual-cap-volts", type=float, default=0.2)
    p.add_argument("--learning-rate", type=float, default=0.0002)
    p.add_argument("--k-error", type=float, default=2.0)
    p.add_argument("--k-rate", type=float, default=0.0)
    p.add_argument("--residual-slew-v-per-s", type=float, default=1.0)
    p.add_argument("--allocation-policy", choices=("fixed-bias", "stability-priority"), default="fixed-bias")
    p.add_argument("--motor-floor-volts", type=float, default=2.0)
    p.add_argument("--max-encoder-step-deg", type=float, default=5.0)
    p.add_argument("--max-abs-pitch-deg", type=float, default=20.0)
    p.add_argument("--max-abs-roll-deg", type=float, default=20.0)
    p.add_argument("--max-consecutive-deadline-misses", type=int, default=20)
    p.add_argument("--output-root", type=Path, default=HERE / "results" / "hardware")
    a = p.parse_args()

    if a.armed and a.io != "q8":
        p.error("--armed requires --io q8")
    if a.armed and not a.confirm_hardware_review:
        p.error("--armed requires --confirm-hardware-review after the lab runbook")
    if a.armed and a.controller not in ("pd", "nengo-pes"):
        p.error("only qualified pd and nengo-pes controllers may be armed")

    os.environ.update({
        "HOVER_NENGO_IO": a.io,
        "HOVER_NENGO_ARMED": str(int(a.armed)),
        "HOVER_NENGO_CONFIRMED": str(int(a.confirm_hardware_review)),
        "HOVER_NENGO_CONTROLLER": a.controller,
        "HOVER_NENGO_MISSION": a.mission,
        "HOVER_NENGO_DURATION": str(a.duration),
        "HOVER_NENGO_STOP_AFTER": "",
        "HOVER_NENGO_REFERENCE_SCALE": str(a.reference_scale),
        "HOVER_NENGO_HARDSTEP_TRANSITION": str(a.hardstep_transition_s),
        "HOVER_NENGO_BETA": str(a.beta),
        "HOVER_NENGO_MOTOR_CAP": str(a.motor_residual_cap_volts),
        "HOVER_NENGO_LEARNING_RATE": str(a.learning_rate),
        "HOVER_NENGO_K_ERROR": str(a.k_error),
        "HOVER_NENGO_K_RATE": str(a.k_rate),
        "HOVER_NENGO_RESIDUAL_SLEW": str(a.residual_slew_v_per_s),
        "HOVER_NENGO_ALLOCATION": a.allocation_policy,
        "HOVER_NENGO_MOTOR_FLOOR": str(a.motor_floor_volts),
        "HOVER_NENGO_EXPECTED_HOME_YAW": "",
        "HOVER_NENGO_HOME_TOLERANCE": "5.0",
        "HOVER_NENGO_MAX_ENCODER_STEP_DEG": str(a.max_encoder_step_deg),
        "HOVER_NENGO_MAX_PITCH": str(a.max_abs_pitch_deg),
        "HOVER_NENGO_MAX_ROLL": str(a.max_abs_roll_deg),
        "HOVER_NENGO_MAX_MISSES": str(a.max_consecutive_deadline_misses),
        "HOVER_NENGO_HEARTBEAT_TIMEOUT": "999999",  # no GUI ever heartbeats; use our own thread instead
        "HOVER_NENGO_DISTURBANCE": "none",
        "HOVER_NENGO_DISTURBANCE_SCALE": "1.0",
        "HOVER_NENGO_EMULATION_REALTIME": "1",
        "HOVER_NENGO_OUTPUT_ROOT": str(a.output_root.resolve()),
    })

    sys.path.insert(0, str(HERE))
    print(f"Direct Nengo run (no GUI): io={a.io} armed={a.armed} controller={a.controller} mission={a.mission} duration={a.duration}s")
    import hover_nengo_hil_gui as engine  # noqa: E402  (import after env vars are set -- CFG reads them at import time)

    stop_hb = threading.Event()

    def keep_heartbeat_alive() -> None:
        while not stop_hb.is_set():
            engine.WORKER.heartbeat()
            time.sleep(0.05)

    hb_thread = threading.Thread(target=keep_heartbeat_alive, daemon=True)
    hb_thread.start()

    engine.WORKER.start()
    deadline = time.time() + a.duration + 10.0
    while engine.WORKER.thread is not None and engine.WORKER.thread.is_alive() and time.time() < deadline:
        time.sleep(0.05)
    stop_hb.set()

    if engine.WORKER.output_dir is not None:
        print(f"Saved to: {engine.WORKER.output_dir}")
    if engine.WORKER.abort_reason:
        print(f"Run ended with: {engine.WORKER.abort_reason}")
    else:
        print("Run completed cleanly.")


if __name__ == "__main__":
    main()

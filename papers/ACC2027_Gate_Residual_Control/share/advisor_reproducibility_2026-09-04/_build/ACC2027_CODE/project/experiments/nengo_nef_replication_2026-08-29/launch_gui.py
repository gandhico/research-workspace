"""Portable launcher for the Nengo CMG/PES MuJoCo GUI."""
from __future__ import annotations

import argparse
import os
import sys
import warnings
from pathlib import Path


HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("cf2-rotor", "x2"), default="x2")
    parser.add_argument(
        "--mission",
        choices=("hover", "roll", "full3", "hard45", "hardstep", "yaw360"),
        default="hard45",
    )
    parser.add_argument("--duration", type=float, default=45.0)
    parser.add_argument("--actuator-scale", type=float)
    parser.add_argument(
        "--mujoco-viewer",
        choices=("none", "neural", "baseline"),
        default="none",
        help="Open a passive 3D viewer for one synchronized MuJoCo twin.",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Pace simulation time to wall-clock time (recommended with viewer).",
    )
    parser.add_argument(
        "--viewer-fps",
        type=float,
        default=30.0,
        help="Maximum MuJoCo viewer refresh rate; control remains at 2 kHz.",
    )
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--password", help="Optional local GUI password.")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--auto-shutdown", type=float, default=2.0)
    parser.add_argument(
        "--no-save-telemetry",
        action="store_true",
        help="Do not save the default full-rate GUI-session Nengo archive on exit.",
    )
    parser.add_argument(
        "--max-log-seconds",
        type=float,
        help="Bound full-rate logging; defaults to one selected mission duration.",
    )
    parser.add_argument(
        "--telemetry-output-root",
        type=Path,
        help="Optional directory for GUI-session archives.",
    )
    args = parser.parse_args()

    actuator_scale = args.actuator_scale
    if actuator_scale is None:
        actuator_scale = 1.5 if args.platform == "cf2-rotor" else 1.0
    os.environ["GRA_GUI_PLATFORM"] = args.platform
    os.environ["GRA_GUI_MISSION"] = args.mission
    os.environ["GRA_GUI_DURATION"] = str(args.duration)
    os.environ["GRA_GUI_ACTUATOR_SCALE"] = str(actuator_scale)
    os.environ["GRA_GUI_MUJOCO_VIEWER"] = args.mujoco_viewer
    os.environ["GRA_GUI_REALTIME"] = "1" if args.realtime else "0"
    if not 1.0 <= args.viewer_fps <= 120.0:
        parser.error("--viewer-fps must be between 1 and 120")
    os.environ["GRA_GUI_VIEWER_FPS"] = str(args.viewer_fps)
    os.environ["GRA_GUI_SAVE_TELEMETRY"] = "0" if args.no_save_telemetry else "1"
    os.environ["GRA_GUI_MAX_LOG_SECONDS"] = str(
        args.duration if args.max_log_seconds is None else args.max_log_seconds
    )
    os.environ["GRA_GUI_TELEMETRY_ROOT"] = (
        "" if args.telemetry_output_root is None else str(args.telemetry_output_root.resolve())
    )
    os.chdir(HERE)
    sys.path.insert(0, str(HERE))

    gui_args = [
        "nengo_gui",
        "--backend", "nengo_dt0005_backend",
        "--port", str(args.port),
        "--auto-shutdown", str(args.auto_shutdown),
    ]
    if args.no_browser:
        gui_args.append("--no-browser")
    if args.password:
        gui_args.extend(["--password", args.password])
    gui_args.append(str(HERE / "gui_cmg_pes_mujoco.py"))
    sys.argv = gui_args
    warnings.filterwarnings(
        "ignore", message="Install the jedi module to get autocompletion.*"
    )
    import nengo_gui

    nengo_gui.main()


if __name__ == "__main__":
    main()

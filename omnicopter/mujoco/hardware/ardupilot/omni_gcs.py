"""Omnidrone ground station: one window, no Mission Planner, no RC.

    python omni_gcs.py --server <MOTIVE_PC_IP>

Needs the OptiTrack room calibration (python mocap\\omni_mocap_bridge.py --server <IP> --calibrate) and the Cube
configured for GCS-only flight (config\\stage5_gcs_only.param).  Owns UDP 14550: close Mission Planner's UDP
connection and every other tool first.

Keys: SPACE = KILL (motors stop at once) | L = LAND | arrows = nudge North/South/East/West |
      PageUp / PageDown = up / down | Q / E = yaw left / right.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from gcs_core import Config, GroundStation, Limits

HERE = Path(__file__).resolve().parent
GREEN, RED, AMBER, GREY = "#1f7a1f", "#b00020", "#b36b00", "#666666"


def hover_signs():
    """+1/-1 per ArduPilot motor: the side each rotor must hover on (generated mixer throttle column)."""
    try:
        data = json.loads((HERE / "generated" / "omnidrone_6dof_mixer.json").read_text(encoding="utf-8"))
        return [1 if data["factors_by_ap_motor"][f"Motor{k}"][3] > 0 else -1 for k in range(1, 9)]
    except (OSError, KeyError, ValueError):
        return [0] * 8


class App:
    def __init__(self, root, gs: GroundStation, step_m=0.05):
        self.root, self.gs = root, gs
        self.signs = hover_signs()
        self.shown_events = 0
        self.shown_messages = 0
        root.title("Omnidrone ground station")
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.banner = tk.Label(root, text="starting ...", font=("Segoe UI", 18, "bold"), fg="white", bg=GREY, pady=6)
        self.banner.grid(row=0, column=0, columnspan=3, sticky="ew")

        gates = ttk.LabelFrame(root, text="Pre-flight gates (all green to ARM)")
        gates.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self.gate_labels = []
        for i in range(9):
            label = tk.Label(gates, anchor="w", font=("Consolas", 10), width=58)
            label.grid(row=i, column=0, sticky="w")
            self.gate_labels.append(label)
        self.confirm = tk.BooleanVar(value=False)
        tk.Checkbutton(gates, text="Tether attached, area clear, kill person ready", variable=self.confirm,
                       command=self.on_confirm, font=("Segoe UI", 10, "bold")).grid(row=10, column=0, sticky="w")

        vehicle = ttk.LabelFrame(root, text="Vehicle")
        vehicle.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
        self.values = {}
        for i, key in enumerate(["Link", "OptiTrack", "Position (NED)", "EKF - OptiTrack", "Attitude r/p/y",
                                 "Cube - OptiTrack", "From arming spot", "Battery", "Target"]):
            tk.Label(vehicle, text=key, anchor="w", font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w")
            self.values[key] = tk.Label(vehicle, anchor="w", font=("Consolas", 10), width=40)
            self.values[key].grid(row=i, column=1, sticky="w")
        motors = tk.Frame(vehicle)
        motors.grid(row=10, column=0, columnspan=2, sticky="w", pady=4)
        self.motor_labels = []
        for k in range(8):
            label = tk.Label(motors, text=f"M{k + 1}\n----", font=("Consolas", 9), width=7, relief="groove")
            label.grid(row=0, column=k, padx=1)
            self.motor_labels.append(label)
        tk.Label(vehicle, text="motor colour: green = strong side, amber = WEAK side, grey = stopped",
                 font=("Segoe UI", 8), fg=GREY).grid(row=11, column=0, columnspan=2, sticky="w")

        cmd = ttk.LabelFrame(root, text="Commands (GUIDED)")
        cmd.grid(row=1, column=2, sticky="nsew", padx=6, pady=6)
        tk.Button(cmd, text="ARM", width=12, command=lambda: self.run(gs.arm)).grid(row=0, column=0, pady=2)
        tk.Button(cmd, text="DISARM", width=12, command=lambda: self.run(gs.disarm)).grid(row=0, column=1, pady=2)
        tk.Label(cmd, text="Takeoff height [m]").grid(row=1, column=0)
        self.height = tk.StringVar(value="0.25")
        tk.Entry(cmd, textvariable=self.height, width=8).grid(row=1, column=1)
        tk.Button(cmd, text="TAKEOFF", width=12, command=self.on_takeoff).grid(row=2, column=0, pady=2)
        tk.Button(cmd, text="LAND", width=12, command=lambda: self.run(gs.land)).grid(row=2, column=1, pady=2)
        tk.Label(cmd, text="Nudge step [m]").grid(row=3, column=0)
        self.step = tk.StringVar(value=f"{step_m:.2f}")
        tk.Entry(cmd, textvariable=self.step, width=8).grid(row=3, column=1)
        pad = tk.Frame(cmd)
        pad.grid(row=4, column=0, columnspan=2, pady=4)
        for text, r, c, args in [("N+", 0, 1, (1, 0, 0, 0)), ("W", 1, 0, (0, -1, 0, 0)), ("E", 1, 2, (0, 1, 0, 0)),
                                 ("S", 2, 1, (-1, 0, 0, 0)), ("Up", 0, 3, (0, 0, 1, 0)), ("Down", 2, 3, (0, 0, -1, 0)),
                                 ("Yaw-", 0, 4, (0, 0, 0, -10)), ("Yaw+", 2, 4, (0, 0, 0, 10))]:
            tk.Button(pad, text=text, width=5, command=lambda a=args: self.nudge(*a)).grid(row=r, column=c, padx=1)
        tk.Button(cmd, text="Twin view (MuJoCo)", width=26, command=self.on_twin).grid(row=5, column=0, columnspan=2)
        tk.Button(cmd, text="KILL  (space)", font=("Segoe UI", 16, "bold"), fg="white", bg=RED, height=2,
                  command=lambda: gs.kill("KILL button")).grid(row=6, column=0, columnspan=2, sticky="ew", pady=8)

        self.log = tk.Text(root, height=12, font=("Consolas", 9), state="disabled")
        self.log.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=6, pady=6)
        root.rowconfigure(2, weight=1)
        for c in range(3):
            root.columnconfigure(c, weight=1)

        # SPACE = KILL works everywhere. The other keys are ignored while typing in a number box,
        # otherwise an arrow key or "e" typed into the height box would move the vehicle.
        root.bind("<space>", lambda e: gs.kill("SPACE key"))
        for key, action in [("l", lambda: self.run(gs.land)),
                            ("<Up>", lambda: self.nudge(1, 0, 0, 0)), ("<Down>", lambda: self.nudge(-1, 0, 0, 0)),
                            ("<Right>", lambda: self.nudge(0, 1, 0, 0)), ("<Left>", lambda: self.nudge(0, -1, 0, 0)),
                            ("<Prior>", lambda: self.nudge(0, 0, 1, 0)), ("<Next>", lambda: self.nudge(0, 0, -1, 0)),
                            ("q", lambda: self.nudge(0, 0, 0, -10)), ("e", lambda: self.nudge(0, 0, 0, 10))]:
            root.bind(key, lambda event, act=action: None if isinstance(event.widget, tk.Entry) else act())
        self.refresh()

    # -------------------------------------------------------------- actions
    def run(self, fn, *args):
        """Commands wait for the Cube's ACK (up to ~4 s on a lossy link): never on the window thread."""
        threading.Thread(target=fn, args=args, daemon=True).start()

    def nudge(self, n, e, up, yaw):
        try:
            step = min(max(float(self.step.get()), 0.01), 0.10)
        except ValueError:
            step = 0.05
        self.run(self.gs.nudge, n * step, e * step, up * step, yaw)

    def on_confirm(self):
        self.gs.operator_confirmed = self.confirm.get()

    def on_takeoff(self):
        try:
            height = float(self.height.get())
        except ValueError:
            messagebox.showerror("Takeoff", "Height must be a number in metres")
            return
        if messagebox.askyesno("Takeoff", f"Take off to {height:.2f} m in GUIDED?"):
            self.run(self.gs.takeoff, height)

    def on_twin(self):
        subprocess.Popen([sys.executable, str(HERE / "twin_view.py"), "--port", str(self.gs.cfg.twin_port)])

    def on_close(self):
        if self.gs.armed() and not messagebox.askyesno(
                "Quit", "The vehicle is ARMED. Quitting stops the heartbeat and the OptiTrack stream; the Cube will "
                        "then LAND by itself (GCS failsafe). Quit anyway?"):
            return
        self.gs.close()
        self.root.destroy()

    # -------------------------------------------------------------- display
    def refresh(self):
        gs, s = self.gs, self.gs.status()
        link_ok = s["hb_age"] is not None and s["hb_age"] < 2.0
        if not link_ok:
            self.banner.config(text="NO CUBE LINK", bg=RED)
        else:
            state = "ARMED" if s["armed"] else "disarmed"
            colour = AMBER if s["armed"] else GREEN
            extra = f"   AUTO: {s['auto_action']}" if s["auto_action"] else ""
            self.banner.config(text=f"{state}   {s['mode']}{extra}", bg=RED if s["auto_action"] else colour)
        for label, (ok, name, detail) in zip(self.gate_labels, gs.preflight()):
            label.config(text=f"{'OK ' if ok else 'NO '} {name}: {detail}", fg=GREEN if ok else RED)

        def vec(v, scale=1.0, unit=""):
            return "-" if v is None else " ".join(f"{scale * x:+7.3f}" for x in v) + unit
        v = self.values
        v["Link"].config(text=("-" if s["hb_age"] is None else f"heartbeat {s['hb_age']:.1f} s, ")
                         + f"lost {100 * s['link_loss']:.0f} %", fg=GREEN if link_ok and s["link_loss"] < 0.25 else RED)
        v["OptiTrack"].config(text=f"{s['rate_in']:.0f} Hz in, {s['rate_out']:.0f} Hz to EKF"
                              + ("" if s["tracked"] else "   NOT TRACKED"), fg=GREEN if s["tracked"] else RED)
        v["Position (NED)"].config(text=vec(s["mocap_ned"], unit=" m"))
        v["EKF - OptiTrack"].config(text="-" if s["ekf_mocap_m"] is None else f"{100 * s['ekf_mocap_m']:.1f} cm")
        v["Attitude r/p/y"].config(text="-" if s["cube_rpy"] is None else
                                   " ".join(f"{math.degrees(x):+7.1f}" for x in s["cube_rpy"]) + " deg")
        v["Cube - OptiTrack"].config(text="-" if s["att_diff_deg"] is None else
                                     " ".join(f"{x:+6.1f}" for x in s["att_diff_deg"]) + " deg")
        if s["home"] is not None and s["mocap_ned"] is not None:
            d = s["mocap_ned"] - s["home"]
            v["From arming spot"].config(text=f"{math.hypot(d[0], d[1]):.2f} m horizontal, {-d[2]:+.2f} m up")
        else:
            v["From arming spot"].config(text="-")
        v["Battery"].config(text="no battery monitor" if s["battery"] is None else
                            f"{s['battery'][0]:.2f} V  {s['battery'][1]:.1f} A")
        v["Target"].config(text="-" if s["target"] is None or s["home"] is None else
                           vec([s["target"][k] - s["home"][k] for k in range(3)], unit=" m from spot"))
        servo = s["servo"]
        for k, label in enumerate(self.motor_labels):
            if servo is None:
                label.config(text=f"M{k + 1}\n----", bg="SystemButtonFace")
                continue
            us = servo[k]
            side = 0 if abs(us - 1500) < 15 else (1 if us > 1500 else -1)
            colour = "#dddddd" if side == 0 else ("#b8e0b8" if side == self.signs[k] else "#f5c27a")
            label.config(text=f"M{k + 1}\n{us}", bg=colour)

        lines = []
        events = gs.events
        for event in events[self.shown_events:]:
            lines.append(time.strftime("%H:%M:%S", time.localtime(event.wall)) + f"  [{event.level}] {event.text}")
        self.shown_events = len(events)
        messages = list(gs.hub.messages)
        new = messages[self.shown_messages:] if self.shown_messages <= len(messages) else messages
        for wall, severity, text in new:
            lines.append(time.strftime("%H:%M:%S", time.localtime(wall)) + f"  CUBE: {text}")
        self.shown_messages = len(messages)
        if lines:
            self.log.config(state="normal")
            self.log.insert("end", "\n".join(lines) + "\n")
            self.log.see("end")
            self.log.config(state="disabled")
        self.root.after(100, self.refresh)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--server", required=True, help="Motive PC IP address")
    p.add_argument("--local-ip", default=None)
    p.add_argument("--unicast", action="store_true")
    p.add_argument("--natnet", default=None)
    p.add_argument("--rb-name", default="Aries_Omnidrone")
    p.add_argument("--id", type=int, default=None)
    p.add_argument("--cal", default=None, help="room calibration (default mocap/omni_mocap_calib.json)")
    p.add_argument("--rate", type=float, default=30.0)
    p.add_argument("--pico-ip", default=None)
    p.add_argument("--listen-port", type=int, default=14550)
    p.add_argument("--pico-port", type=int, default=14550)
    p.add_argument("--relay", action="store_true", help="also forward telemetry to Mission Planner on UDP 14551")
    p.add_argument("--origin", default="0,0,0")
    # Defaults trigger before a tether that allows 0.5 m drift / 0.5 m height goes taut.
    p.add_argument("--tether-radius", type=float, default=0.35, help="LAND beyond this horizontal distance [m]")
    p.add_argument("--max-height", type=float, default=0.45, help="LAND above this height [m]")
    p.add_argument("--close-after", type=float, default=None, help=argparse.SUPPRESS)   # smoke tests
    a = p.parse_args()
    limits = Limits(tether_radius_m=a.tether_radius, max_height_m=a.max_height,
                    max_takeoff_m=min(0.4, a.max_height - 0.1))
    cfg = Config(server=a.server, local_ip=a.local_ip, unicast=a.unicast, natnet=a.natnet, rb_name=a.rb_name,
                 rb_id=a.id, rate=a.rate, listen_port=a.listen_port, pico_ip=a.pico_ip, pico_port=a.pico_port,
                 relay=a.relay, origin=a.origin, limits=limits, **({"cal": a.cal} if a.cal else {}))
    gs = GroundStation(cfg).start()
    root = tk.Tk()
    App(root, gs)
    if a.close_after:
        root.after(int(a.close_after * 1000), lambda: (gs.close(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()

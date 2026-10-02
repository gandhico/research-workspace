#!/usr/bin/env python3
"""Stage-5 single-axis inner-rate LQR runner; observe-only unless --engage."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backstepping"))

import Backstepping
import xpc
from run_backstepping_baseline_xp12 import (
    MEASUREMENTS, PITCH_OVERRIDE_DREF, PITCH_YOKE_DREF, ROLL_OVERRIDE_DREF,
    ROLL_YOKE_DREF, calculate_command, read_measurements, scalar,
    send_control, start_block_reasons,
)

try:
    from .delay_aware_lqr import DelayAwareRateLQR
except ImportError:
    from delay_aware_lqr import DelayAwareRateLQR


def half_sine_reference(elapsed_s: float, start_s: float, duration_s: float, amplitude: float) -> float:
    if duration_s <= 0 or elapsed_s < start_s or elapsed_s > start_s + duration_s:
        return 0.0
    return amplitude * math.sin(math.pi * (elapsed_s - start_s) / duration_s)


def abort_reason(args, pitch, roll, measurements):
    if abs(pitch) > args.max_abs_pitch_deg: return "pitch envelope exceeded"
    if abs(roll) > args.max_abs_roll_deg: return "roll envelope exceeded"
    if max(abs(measurements[k]) for k in ("p_deg_s", "q_deg_s", "r_deg_s")) > args.max_abs_rate_deg_s:
        return "body-rate envelope exceeded"
    if measurements["sim_paused"] != 0: return "simulator paused"
    if measurements["sim_speed"] <= 0: return "simulation speed zero"
    if measurements["replay_mode"] != 0: return "replay mode active"
    return ""


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--engage", action="store_true")
    p.add_argument("--axis", choices=("pitch",), default="pitch")
    p.add_argument("--duration", type=float, default=30.0); p.add_argument("--hz", type=float, default=10.0)
    p.add_argument("--pulse-start-s", type=float, default=10.0); p.add_argument("--pulse-duration-s", type=float, default=2.0)
    p.add_argument("--pulse-amplitude-deg-s", type=float, default=0.0)
    p.add_argument("--disturbance-pulse-amplitude", type=float, default=0.0005)
    p.add_argument("--target-altitude-m", type=float, default=1700); p.add_argument("--altitude-tolerance-m", type=float, default=150)
    p.add_argument("--target-ias-kts", type=float, default=39); p.add_argument("--ias-tolerance-kts", type=float, default=5)
    p.add_argument("--pitch-sp", type=float, default=1.3); p.add_argument("--roll-sp", type=float, default=0.0)
    p.add_argument("--max-start-pitch-error-deg", type=float, default=7); p.add_argument("--max-start-roll-error-deg", type=float, default=3)
    p.add_argument("--max-start-rate-deg-s", type=float, default=3); p.add_argument("--target-throttle", type=float, default=.0235)
    p.add_argument("--throttle-tolerance", type=float, default=.02)
    p.add_argument("--max-abs-pitch-deg", type=float, default=10); p.add_argument("--max-abs-roll-deg", type=float, default=10)
    p.add_argument("--max-abs-rate-deg-s", type=float, default=20)
    p.add_argument("--test-id", required=True); p.add_argument("--out", type=Path, required=True)
    p.add_argument("--host", default="127.0.0.1"); p.add_argument("--port", type=int, default=49009); p.add_argument("--timeout-ms", type=int, default=2000)
    return p


def main():
    args = parser().parse_args()
    if abs(args.pulse_amplitude_deg_s) > 0.2: raise SystemExit("rate-reference amplitude must not exceed 0.2 deg/s")
    if abs(args.disturbance_pulse_amplitude) > 0.0005: raise SystemExit("disturbance pulse must not exceed 0.0005")
    if args.duration <= args.pulse_start_s + args.pulse_duration_s: raise SystemExit("duration must include post-pulse recovery")
    roll_bs = Backstepping.Backstepping(.001, 33, .03); pitch_bs = Backstepping.Backstepping(.001, 39, .03)
    roll_bs.SetPoint = args.roll_sp; pitch_bs.SetPoint = args.pitch_sp
    fields = ["sample","t_s","dt_s","alt_m","pitch_deg","roll_deg","heading_deg","engaged","start_allowed","start_block_reason",
              "controller_mode","rate_reference_deg_s","disturbance_pulse","lqr_requested_perturbation","lqr_sent_perturbation","final_pitch_perturbation","experiment_latched_off","abort_reason",
              "captured_trim_0","captured_trim_1","backstepping_pitch_command","backstepping_roll_command","sent_ctrl_0","sent_ctrl_1",
              *(name for name,_,_ in MEASUREMENTS),"dynamic_pressure_pa","test_id"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    period=1/args.hz; started=next_tick=previous=time.monotonic(); rows=0; latched=False; reason=""; start_checked=False; allowed=not args.engage
    with xpc.XPlaneConnect(xpHost=args.host,xpPort=args.port,timeout=args.timeout_ms) as client, args.out.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        initial_ro=scalar(client.getDREF(ROLL_OVERRIDE_DREF));initial_ry=scalar(client.getDREF(ROLL_YOKE_DREF))
        initial_po=scalar(client.getDREF(PITCH_OVERRIDE_DREF));initial_py=scalar(client.getDREF(PITCH_YOKE_DREF))
        trim=tuple(float(x) for x in client.getCTRL()); lqr=DelayAwareRateLQR("pitch",trim[0]); ro=po=False
        print(f"Mode={'ENGAGED' if args.engage else 'OBSERVE-ONLY'}; output={args.out.resolve()}")
        print(f"Captured trim CTRL0={trim[0]:+.6g}, CTRL1={trim[1]:+.6g}")
        try:
            while time.monotonic()-started < args.duration:
                now=time.monotonic()
                if now<next_tick: time.sleep(min(.002,next_tick-now));continue
                next_tick+=period;pos=client.getPOSI();ctrl=client.getCTRL();m=read_measurements(client);_,_,alt,pitch,roll,heading,_=pos;elapsed=now-started
                bs=calculate_command(roll_bs,pitch_bs,roll,pitch,ctrl,"legacy",0,0,-998,control_trim=trim)
                if args.engage and not start_checked:
                    why=start_block_reasons(args,alt,pitch,roll,m);allowed=not why;start_reason="; ".join(why);start_checked=True
                    print("Start gate:","PASS" if allowed else f"BLOCKED: {start_reason}")
                elif not args.engage: start_reason="observe-only"
                if not latched:
                    reason=abort_reason(args,pitch,roll,m)
                    if reason: latched=True
                reference=0.0 if latched else half_sine_reference(elapsed,args.pulse_start_s,args.pulse_duration_s,args.pulse_amplitude_deg_s)
                disturbance=0.0 if latched else half_sine_reference(elapsed,args.pulse_start_s,args.pulse_duration_s,args.disturbance_pulse_amplitude)
                lqr.rate_reference_deg_s=reference
                _,lqr_candidate=lqr.preview(m["q_deg_s"],disturbance)
                if latched:
                    sent0=bs["sent_ctrl_0"];sent_pert=sent0-trim[0];mode="BACKSTEPPING_RECOVERY"
                else:
                    sent0,sent_pert=lqr.step(m["q_deg_s"],disturbance);mode="PITCH_RATE_LQR"
                sent1=bs["sent_ctrl_1"]
                engaged=args.engage and allowed
                if engaged:
                    if not ro: client.sendDREF(ROLL_OVERRIDE_DREF,1);ro=True;print("Roll-axis ownership: ACTIVE")
                    if not po: client.sendDREF(PITCH_OVERRIDE_DREF,1);po=True;print("Pitch-axis ownership: ACTIVE")
                    send_control(client,[sent0,sent1,0,-998],"legacy",True,True)
                writer.writerow({"sample":rows,"t_s":elapsed,"dt_s":now-previous,"alt_m":alt,"pitch_deg":pitch,"roll_deg":roll,"heading_deg":heading,
                    "engaged":engaged,"start_allowed":allowed,"start_block_reason":start_reason,"controller_mode":mode,"rate_reference_deg_s":reference,"disturbance_pulse":disturbance,
                    "lqr_requested_perturbation":lqr_candidate,"lqr_sent_perturbation":lqr_candidate,"final_pitch_perturbation":sent_pert,"experiment_latched_off":latched,"abort_reason":reason,
                    "captured_trim_0":trim[0],"captured_trim_1":trim[1],"backstepping_pitch_command":bs["sent_ctrl_0"],
                    "backstepping_roll_command":bs["sent_ctrl_1"],"sent_ctrl_0":sent0,"sent_ctrl_1":sent1,**m,"test_id":args.test_id})
                previous=now;rows+=1
                if args.engage and not allowed: break
        finally:
            if ro: client.sendDREF(ROLL_YOKE_DREF,initial_ry);client.sendDREF(ROLL_OVERRIDE_DREF,initial_ro);print("Roll-axis ownership: RESTORED")
            if po: client.sendDREF(PITCH_YOKE_DREF,initial_py);client.sendDREF(PITCH_OVERRIDE_DREF,initial_po);print("Pitch-axis ownership: RESTORED")
    print(f"Saved {rows} samples: {args.out.resolve()}")


if __name__ == "__main__": main()

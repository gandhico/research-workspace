"""
race.py  --  heterogeneous ghost time-trial: X2, CF2, Omnicopter and Y6 fly the same track at once.

Each vehicle gets its own trajectory, time-scaled to its MJCF-derived thrust-to-weight ratio
(track.Trajectory), and the shared controller (controller.py).  Vehicles leave the start line 1.5 s apart.

Logged per vehicle: position vs reference, actuator commands, saturation, gate passes
(time, lateral offset from the gate centre, clearance to the frame) and gate/ground collisions.

    python race.py [--laps 2] [--only x2,y6] [--viewer]
    -> results/race_<tag>.npz, results/race_<tag>.json
"""
import json, time, argparse, pathlib
import numpy as np
import mujoco
import mujoco.viewer

import build_scene, track
from controller import VehicleController

HERE = pathlib.Path(__file__).resolve().parent
Ry90 = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0.]])
ORDER = ["x2", "y6", "cf2", "omni"]            # start order (1.5 s apart)
# half-size of each vehicle across the gate opening [m] (measured from the MJCF, section README)
# per-vehicle planner margin (fraction of T/W the plan may use) and attitude-gain rule.
# X2: margin 0.35 with full attitude gains, chosen by results/sweep_x2.json (0.35 -> 4 cm RMSE,
# 0.45 borderline, 0.6 diverges): its yaw authority at hover is only 4.3 rad/s^2 (Y6: 19.7).
VEHICLE_CFG = {"x2":   dict(margin=0.35, auth_frac=None),
               "y6":   dict(margin=0.60, auth_frac=0.5),
               "cf2":  dict(margin=0.60, auth_frac=0.5),
               "omni": dict(margin=0.60, auth_frac=0.5)}
HALF_SPAN = {"x2": 0.32, "cf2": 0.08, "omni": 0.48, "y6": 0.36}


class GateJudge:
    """Detects passes through each gate plane and collisions with gate/ground geoms."""
    def __init__(self, m, pre, bid):
        self.m, self.pre, self.bid = m, pre, bid
        self.C = [np.array(c) for _, c, _ in track.GATES]
        self.N = [track.gate_normal(y) for _, _, y in track.GATES]
        self.prev = None
        self.passes, self.crashes = [], []
        self.vgeoms = {g for g in range(m.ngeom) if m.body_rootid[m.geom_bodyid[g]] == bid}
        self.next_gate = 0

    def step(self, d):
        p = d.xipos[self.bid]
        if self.prev is not None:
            for i, (c, n) in enumerate(zip(self.C, self.N)):
                a, b = n @ (self.prev - c), n @ (p - c)
                if a < 0 <= b:                                    # crossed the plane forwards
                    lat = (p - c) - n*(n @ (p - c))
                    off_y = abs(lat @ np.cross(E3, n)); off_z = abs(lat[2])
                    inside = max(off_y, off_z) < track.GATE_INNER/2
                    if inside:
                        clear = track.GATE_INNER/2 - max(off_y, off_z) - HALF_SPAN[self.pre]
                        self.passes.append(dict(t=round(d.time, 3), gate=i + 1, off_y=round(off_y, 3),
                                                off_z=round(off_z, 3), clearance=round(clear, 3),
                                                in_order=(i == self.next_gate)))
                        if i == self.next_gate:
                            self.next_gate = (i + 1) % len(self.C)
        self.prev = p.copy()
        for k in range(d.ncon):
            con = d.contact[k]
            g1, g2 = con.geom1, con.geom2
            if (g1 in self.vgeoms) != (g2 in self.vgeoms):
                other = g2 if g1 in self.vgeoms else g1
                bname = self.m.body(self.m.geom_bodyid[other]).name
                if bname.startswith("gate") and (not self.crashes or d.time - self.crashes[-1]["t"] > 0.5):
                    self.crashes.append(dict(t=round(d.time, 3), with_=bname))


E3 = np.array([0, 0, 1.0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laps", type=int, default=2)
    ap.add_argument("--only", default=",".join(ORDER))
    ap.add_argument("--viewer", action="store_true")
    ap.add_argument("--tag", default="fleet")
    a = ap.parse_args()
    fleet = [f for f in ORDER if f in a.only.split(",")]

    spec, m = build_scene.build(fleet=tuple(build_scene.FLEET))   # all bodies present; idle ones stay parked
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    line = track.RaceLine()
    ctrls, judges = {}, {}
    for k, pre in enumerate(fleet):
        root = build_scene.FLEET[pre][1]
        full = pre == "omni"
        cfg = VEHICLE_CFG[pre]
        probe = VehicleController(m, pre, root, track.Trajectory(line, 2.0), fully_actuated=full,
                                  R0=Ry90 if full else np.eye(3), auth_frac=cfg["auth_frac"])
        traj = track.Trajectory(line, probe.tw, laps=a.laps, margin=cfg["margin"],
                                jerk_bw=np.sqrt(probe.kR)/5.0)      # planner matched to attitude bandwidth
        c = VehicleController(m, pre, root, traj, fully_actuated=full, R0=Ry90 if full else np.eye(3),
                              t_takeoff=3.0, t_start=7.0 + 1.5*k, auth_frac=cfg["auth_frac"])
        ctrls[pre], judges[pre] = c, GateJudge(m, pre, c.bid)
        print(f"{pre:5s} alpha_max {c.alpha_max:6.0f} rad/s2  kR {c.kR:5.1f}  kW {c.kW:4.1f}")
        print(f"{pre:5s} T/W {c.tw:4.2f}  race {traj.t_race:5.1f} s  v_max {traj.v_grid.max():4.1f} m/s  "
              f"peak thrust/weight in plan {traj.tw_used:4.2f}")
    t_end = max(c.t_start + c.traj.t_grid[-1] for c in ctrls.values()) + 1.5
    # idle vehicles (not in --only): hold them on the podium with zero thrust
    n = int(t_end/m.opt.timestep)
    Q = np.zeros((n, m.nq), np.float32); T = np.zeros(n)
    viewer = None
    if a.viewer:

        viewer = mujoco.viewer.launch_passive(m, d)
    t0 = time.time()
    for k in range(n):
        for pre in fleet:
            ctrls[pre](d)
        mujoco.mj_step(m, d)
        for pre in fleet:
            judges[pre].step(d)
        Q[k], T[k] = d.qpos, d.time
        if viewer is not None and k % 8 == 0:
            viewer.sync()
            lag = d.time - (time.time() - t0)
            if lag > 0:
                time.sleep(lag)
    wall = time.time() - t0
    print(f"simulated {t_end:.1f} s in {wall:.1f} s wall")

    out = HERE / "results"; out.mkdir(exist_ok=True)
    summary, arrays = {}, dict(t=T, qpos=Q)
    for pre in fleet:
        c, j = ctrls[pre], judges[pre]
        P, Pr = np.array(c.log["p"]), np.array(c.log["p_ref"])
        tt = np.array(c.log["t"])
        race = (tt > c.t_start) & (tt < c.t_start + c.traj.t_race)
        e = np.linalg.norm(P - Pr, axis=1)
        in_order = [p for p in j.passes if p["in_order"]]
        summary[pre] = dict(
            mass_kg=round(c.mass, 4), thrust_to_weight=round(c.tw, 2), n_rotors=len(c.act),
            tilt_authority_rad_s2=round(c.alpha_max, 1), kR=round(c.kR, 1), kW=round(c.kW, 1),
            planner_margin=VEHICLE_CFG[pre]["margin"],
            lap_time_planned_s=round(c.traj.lap_time, 2), v_max_ms=round(float(c.traj.v_grid.max()), 2),
            track_rmse_cm=round(float(np.sqrt(np.mean(e[race]**2)))*100, 2),
            track_max_cm=round(float(e[race].max())*100, 2),
            saturation_pct=round(100*float(np.mean(np.array(c.log["sat"])[race])), 2),
            gates_passed_in_order=len(in_order), gates_expected=len(track.GATES)*c.traj.laps + 1,          # finish = G1 again
            race_time_planned_s=round(c.traj.t_race, 2),
            min_clearance_m=round(min((p["clearance"] for p in in_order), default=float("nan")), 3),
            gate_collisions=j.crashes, passes=j.passes)
        arrays[f"{pre}_p"], arrays[f"{pre}_pref"], arrays[f"{pre}_t"] = P, Pr, tt
        arrays[f"{pre}_u"] = np.array(c.log["u"])
        print(f"  {pre:5s} RMSE {summary[pre]['track_rmse_cm']:6.1f} cm  max {summary[pre]['track_max_cm']:6.1f} cm  "
              f"gates {len(in_order)}/{summary[pre]['gates_expected']}  min clearance {summary[pre]['min_clearance_m']} m  "
              f"collisions {len(j.crashes)}  sat {summary[pre]['saturation_pct']} %")
    summary["_meta"] = dict(gate_inner_m=track.GATE_INNER, lap_length_m=round(line.length, 1),
                            dt=m.opt.timestep, sim_s=round(t_end, 1), wall_s=round(wall, 1),
                            cf2_authority_scale=build_scene.CF2_AUTHORITY)
    np.savez_compressed(out / f"race_{a.tag}.npz", **arrays)
    (out / f"race_{a.tag}.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

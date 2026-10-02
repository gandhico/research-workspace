"""Background sweep: find a safe X2 configuration (margin, attitude gains, yaw gains)."""
import json, itertools, numpy as np, mujoco, build_scene, track, controller
from controller import VehicleController
spec, m = build_scene.build(fleet=('x2',)); line = track.RaceLine()
rows = []
for auth, mg, kry in itertools.product([100.0, 0.5], [0.35, 0.45, 0.6], [4.0, 25.0]):
    controller.VehicleController.AUTH_FRAC = auth
    d = mujoco.MjData(m); mujoco.mj_forward(m, d)
    probe = VehicleController(m, 'x2', 'x2', track.Trajectory(line, 2.0))
    tr = track.Trajectory(line, probe.tw, laps=1, margin=mg, jerk_bw=np.sqrt(probe.kR)/5)
    c = VehicleController(m, 'x2', 'x2', tr, t_takeoff=3, t_start=7, kR_yaw=kry, kW_yaw=2*0.9*np.sqrt(kry))
    for k in range(int((7 + tr.t_grid[-1])/m.opt.timestep)):
        c(d); mujoco.mj_step(m, d)
    P, R = np.array(c.log['p']), np.array(c.log['p_ref']); t = np.array(c.log['t']); race = (t > 7) & (t < 7 + tr.t_race)
    e = np.linalg.norm(P - R, axis=1)[race]
    r = dict(auth=auth, margin=mg, kR=round(c.kR, 1), kR_yaw=kry, race_s=round(tr.t_race, 1),
             rmse_cm=round(float(np.sqrt(np.mean(e**2)))*100, 1), max_cm=round(float(e.max())*100, 1),
             sat=round(100*float(np.mean(np.array(c.log['sat'])[race])), 1))
    rows.append(r); print(r, flush=True)
json.dump(rows, open('results/sweep_x2.json', 'w'), indent=1)

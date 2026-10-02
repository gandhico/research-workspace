"""
Probe: can the Adaptive HyperLIF conductance ever change the gate trajectory?

X2 sweep showed adaptive == plain bit-for-bit because alpha=50 makes the gate
switch binary, so (base_gain + gain_scaling*|I|)*r^2 never moves r.
Here we soften the sigmoid (lower alpha) and raise gain_scaling to test whether
the adaptive term then produces a measurably different residual / tracking error.
"""
import sys, json, argparse, time, copy
from pathlib import Path

ROOT = Path(r"C:\00_Research_\Neuromorphic_Embodied_AI\01_HyperLIF_Gate_Residual\v2_clean")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))

import controllers.neuron_dynamics as ND
import runners.run_rotor_level as R

def base_args(**over):
    ns = argparse.Namespace(
        quad="skydio_x2", mission="hard45", controller="classical",
        sim_time=20.0, dt=0.0005, z_ref=1.0, seed=1,
        blend=0.50, activity_mode="gate", direct_scale="control", gate_gain=100.0,
        residual_blend=0.10, u_scale=None,
        n_neurons=400, radius=1.5, synapse=0.002,
        viewer=False, viewer_sync_every=20, viewer_follow=False,
        viewer_distance=3.0, viewer_elevation=-20.0, viewer_azimuth=90.0, realtime=False,
        dashboard=False, dashboard_update_every=100, dashboard_window=10.0,
        save_csv=False, save_figures=False, save_npz=False, no_save=True, output_dir=None)
    for k, v in over.items(): setattr(ns, k, v)
    return ns

def run_one(ctrl, alpha, gain_scaling, gg, sim_time):
    # patch control-scale presets for this run
    ND._CONTROL_SCALE_PARAMS["hyperlif"] = dict(
        tau=0.05, tau_r=0.005, reset_gain=120.0, gamma=2.0,
        event_threshold=0.5, alpha=alpha)
    ND._CONTROL_SCALE_PARAMS["adaptive_hyperlif"] = dict(
        tau=0.05, tau_r=0.005, base_gain=120.0, gain_scaling=gain_scaling,
        gamma=2.0, event_threshold=0.5, alpha=alpha)
    s = R.run(base_args(controller=ctrl, gate_gain=gg, sim_time=sim_time))
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim-time", type=float, default=20.0)
    ap.add_argument("--gg", type=float, default=100.0)
    a = ap.parse_args()

    s0 = R.run(base_args(controller="classical", sim_time=a.sim_time))
    qb = s0["qerr_mean"]
    print(f"[classical] qerr={qb:.4f}", flush=True)

    conds = [
        ("plain  a=50  gs=0",   "direct_hyperlif",          50.0,  0.0),
        ("adapt  a=50  gs=30",  "direct_adaptive_hyperlif", 50.0,  30.0),
        ("plain  a=8   gs=0",   "direct_hyperlif",          8.0,   0.0),
        ("adapt  a=8   gs=300", "direct_adaptive_hyperlif", 8.0,   300.0),
        ("adapt  a=8   gs=1000","direct_adaptive_hyperlif", 8.0,   1000.0),
    ]
    out = []
    for label, ctrl, alpha, gs in conds:
        s = run_one(ctrl, alpha, gs, a.gg, a.sim_time)
        d = 100*(qb - s["qerr_mean"])/qb
        row = dict(label=label, ctrl=ctrl, alpha=alpha, gain_scaling=gs, gate_gain=a.gg,
                   qerr_mean=s["qerr_mean"], qerr_max=s["qerr_max"],
                   gate_mean=s.get("gate_mean"), score=s.get("score"), d_qerr_pct=round(d,3))
        out.append(row)
        print(f"[{label:20s}] qerr={s['qerr_mean']:.5f} d={d:+.2f}% "
              f"gate_mean={s.get('gate_mean'):.4f}", flush=True)
    Path(sys.argv[0]).with_name("adaptive_soft_probe.json").write_text(json.dumps(out, indent=2))
    print("WROTE adaptive_soft_probe.json", flush=True)

if __name__ == "__main__":
    main()

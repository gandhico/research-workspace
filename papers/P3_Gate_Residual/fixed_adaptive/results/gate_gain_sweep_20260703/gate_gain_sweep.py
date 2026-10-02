"""
Gate-gain sweep: differentiate Adaptive HyperLIF from plain HyperLIF.

Paper-1 open question (paper_narrative.md sec 9): at gate_gain=100000 the gate
saturates binary, so HyperLIF == Adaptive HyperLIF. Sweep gate_gain to find the
graded regime where the adaptive conductance (base_gain + gain_scaling*|I|) *r^2
changes the residual and the tracking error.
"""
import sys, json, argparse, time, copy
from pathlib import Path

ROOT = Path(r"C:\00_Research_\Neuromorphic_Embodied_AI\01_HyperLIF_Gate_Residual\v2_clean")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import runners.run_rotor_level as R

def base_args(**over):
    ns = argparse.Namespace(
        quad="skydio_x2", mission="hard45", controller="classical",
        sim_time=45.0, dt=0.0005, z_ref=1.0, seed=1,
        blend=0.50, activity_mode="gate", direct_scale="control", gate_gain=1.0,
        residual_blend=0.10, u_scale=None,
        n_neurons=400, radius=1.5, synapse=0.002,
        viewer=False, viewer_sync_every=20, viewer_follow=False,
        viewer_distance=3.0, viewer_elevation=-20.0, viewer_azimuth=90.0, realtime=False,
        dashboard=False, dashboard_update_every=100, dashboard_window=10.0,
        save_csv=False, save_figures=False, save_npz=False, no_save=True, output_dir=None,
    )
    for k, v in over.items():
        setattr(ns, k, v)
    return ns

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quad", default="skydio_x2")
    ap.add_argument("--mission", default="hard45")
    ap.add_argument("--sim-time", type=float, default=45.0)
    ap.add_argument("--blend", type=float, default=0.50)
    ap.add_argument("--out", default="sweep_x2_hard45.json")
    ap.add_argument("--gains", default="1,3,10,30,100,300,1000,100000")
    a = ap.parse_args()

    gains = [float(x) for x in a.gains.split(",")]
    keep = ["controller","qerr_mean","qerr_max","rmse_euler_mean","score",
            "tau_mean","z_std","gate_mean","sat_fraction","rotor_sat_fraction"]

    results = []
    # classical baseline (gate_gain irrelevant)
    t0 = time.time()
    s = R.run(base_args(quad=a.quad, mission=a.mission, sim_time=a.sim_time,
                        controller="classical"))
    base = {k: s.get(k) for k in keep}
    base["gate_gain"] = None
    base["wall_s"] = round(time.time()-t0, 1)
    results.append(base)
    q_base = s["qerr_mean"]
    print(f"[classical] qerr_mean={q_base:.4f} ({base['wall_s']}s)", flush=True)

    for ctrl in ["direct_hyperlif", "direct_adaptive_hyperlif"]:
        for g in gains:
            t0 = time.time()
            s = R.run(base_args(quad=a.quad, mission=a.mission, sim_time=a.sim_time,
                                controller=ctrl, blend=a.blend, gate_gain=g))
            row = {k: s.get(k) for k in keep}
            row["gate_gain"] = g
            row["d_qerr_pct"] = round(100.0*(q_base - s["qerr_mean"])/q_base, 3)
            row["wall_s"] = round(time.time()-t0, 1)
            results.append(row)
            print(f"[{ctrl} gg={g:>8g}] qerr={s['qerr_mean']:.4f} "
                  f"d={row['d_qerr_pct']:+.2f}% gate_mean={s.get('gate_mean'):.3f} "
                  f"({row['wall_s']}s)", flush=True)

    out = Path(sys.argv[0]).with_name(a.out)
    out.write_text(json.dumps(results, indent=2))
    print("WROTE", out, flush=True)

if __name__ == "__main__":
    main()

"""
run_realtime.py  --  fly the Y6 turbine mission LIVE in the MuJoCo viewer, paced to wall-clock time.

    python run_realtime.py                      # classical cascade PD
    python run_realtime.py --ctrl nef_lif       # spiking Nengo controller (LIF + neural allocator)
    python run_realtime.py --ctrl nef_lif --wind 4 --integral
    python run_realtime.py --speed 0.5          # slow motion (2x slower than real time)

Viewer keys (MuJoCo built-ins):   [ / ]  cycle cameras (free -> overview, side, fpv, gimbal_down, chase)
                                  Esc    back to the free camera       Tab   hide/show left panel
                                  mouse  L-drag rotate, R-drag move, scroll zoom
Added here:                        Space  pause / resume
Close the window to stop.  The log is saved to results/realtime_<ctrl>.npz (same format as the offline runs).
"""
import time, argparse, threading
import numpy as np
import mujoco, mujoco.viewer

from y6_mujoco_sim import (Y6MuJoCoPlant, OuterIntegral, shaped_ref, baseline_control, save,
                           P, G, DT, T_END)

FRAME = 1.0 / 60.0                      # viewer refresh period [s of sim time]
STEPS = int(round(FRAME / DT))          # 17 physics/neural steps per frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctrl", choices=["classical", "nef_lif", "nef_rate"], default="classical")
    ap.add_argument("--wind", type=float, default=0.0)
    ap.add_argument("--integral", action="store_true")
    ap.add_argument("--speed", type=float, default=1.0, help="1 = real time, 0.5 = slow motion")
    ap.add_argument("--n_cmd", type=int, default=3000)
    ap.add_argument("--camera", default="chase", help="start camera (chase, side, overview, fpv, free)")
    a = ap.parse_args()

    plant = Y6MuJoCoPlant(wind=a.wind)
    m, d = plant.m, plant.d
    ref = OuterIntegral(plant) if a.integral else shaped_ref

    # ---- controller: one function that advances STEPS steps ------------------------------
    if a.ctrl == "classical":
        state = {"s": plant.state12()}

        def advance():
            for _ in range(STEPS):
                omega, _ = baseline_control(state["s"], ref(d.time), P, G)
                state["s"] = plant.step(omega)
        closer = lambda: None
    else:
        import nengo
        import src.controllers_nengo.trirotor_nef as tnef
        tnef.TrirotorPlantNode = lambda dt, x0=None, P=P: plant       # MuJoCo is the plant node
        print("building Nengo network (decoders are cached after the first run) ...")
        t0 = time.time()
        net = tnef.build_network(DT, G, ref, seed=1, n_cmd=a.n_cmd,
                                 neuron_type=nengo.LIF() if a.ctrl == "nef_lif" else nengo.RectifiedLinear())
        sim = nengo.Simulator(net, dt=DT, progress_bar=False)
        print(f"  built in {time.time()-t0:.1f} s  ({sum(e.n_neurons for e in net.all_ensembles)} neurons)")

        def advance():
            sim.run_steps(STEPS)                   # each Nengo step calls plant.step() once
        closer = sim.close

    paused = threading.Event()

    def key_callback(key):
        if key == 32:                              # space bar
            paused.clear() if paused.is_set() else paused.set()

    with mujoco.viewer.launch_passive(m, d, key_callback=key_callback) as viewer:
        if a.camera != "free":
            viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
            viewer.cam.fixedcamid = m.camera(a.camera).id
        wall0, sim0, last_print = time.perf_counter(), d.time, 0.0
        while viewer.is_running() and d.time < T_END:
            if paused.is_set():
                time.sleep(0.05); wall0, sim0 = time.perf_counter(), d.time
                viewer.sync(); continue
            with viewer.lock():
                advance()
            viewer.sync()
            # pace: sim time must not run ahead of (scaled) wall time
            ahead = (d.time - sim0) / a.speed - (time.perf_counter() - wall0)
            if ahead > 0:
                time.sleep(ahead)
            if d.time - last_print >= 5.0:
                rtf = (d.time - sim0) / (time.perf_counter() - wall0)
                s = plant.log["state"][-1]
                print(f"t = {d.time:5.1f} s  pos = ({s[0]:5.2f}, {s[1]:5.2f}, {s[2]:5.2f})  "
                      f"real-time factor = {rtf:4.2f}{'  (CPU-bound, below target)' if rtf < 0.95*a.speed else ''}")
                last_print = d.time
        print("mission finished" if d.time >= T_END else "viewer closed")
    closer()
    tag = f"realtime_{a.ctrl}" + (f"_wind{a.wind:g}" if a.wind else "") + ("_int" if a.integral else "")
    save(plant, tag)


if __name__ == "__main__":
    main()

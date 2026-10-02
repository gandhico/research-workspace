"""
gui_y6_mujoco.py  --  Nengo GUI + live MuJoCo viewer, same spiking Y6 controller.

    nengo_gui gui_y6_mujoco.py        (or launchers\\3_nengo_gui.bat)

The browser shows the Nengo network (right-click an ensemble -> Spikes / Value / Firing
pattern); pressing Play also opens the MuJoCo window, where the Y6 flies the turbine
mission. The plant node paces itself to wall-clock time, so both views stay in sync.
Reset in the GUI puts the drone back on the pad.  Settings below.
"""
import sys, time, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "nengo_y6"))

import nengo
import mujoco, mujoco.viewer
from y6_mujoco_sim import Y6MuJoCoPlant, shaped_ref, P, G, DT

WIND = 0.0          # m/s mean wind at the site
N_CMD = 1000        # allocator neurons (paper exp04 = 3000; 1000 keeps the GUI responsive)
NEURON = nengo.LIF()
CAMERA = "chase"    # starting camera in the MuJoCo window; [ and ] cycle cameras


class ViewerPlant:
    """Nengo node callable: steps MuJoCo, syncs the viewer at 60 Hz, paces to real time."""
    def __init__(self):
        self.plant = Y6MuJoCoPlant(wind=WIND)
        self.viewer, self.k, self.t_last = None, 0, -1.0
        self.wall0 = self.sim0 = None

    def __call__(self, t, omega):
        if t < self.t_last:                       # GUI reset
            with self._lock():
                self.plant.reset()
            self.wall0 = None
        self.t_last = t
        s = self.plant.step(omega)
        self.k += 1
        if self.k % 17 == 0:                      # ~60 Hz display + pacing
            if self.viewer is None or not self.viewer.is_running():
                self.viewer = mujoco.viewer.launch_passive(self.plant.m, self.plant.d)
                self.viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
                self.viewer.cam.fixedcamid = self.plant.m.camera(CAMERA).id
            self.viewer.sync()
            now = time.perf_counter()
            if self.wall0 is None or now - self._last_wall > 0.5:   # (re)anchor after pause/reset
                self.wall0, self.sim0 = now, t
            ahead = (t - self.sim0) - (now - self.wall0)
            if ahead > 0:
                time.sleep(ahead)
            self._last_wall = time.perf_counter()
        return s

    def _lock(self):
        import contextlib
        return self.viewer.lock() if self.viewer is not None else contextlib.nullcontext()


import src.controllers_nengo.trirotor_nef as tnef
_vp = ViewerPlant()
tnef.TrirotorPlantNode = lambda dt, x0=None, P=P: _vp
model = tnef.build_network(DT, G, shaped_ref, neuron_type=NEURON, seed=1, n_cmd=N_CMD)

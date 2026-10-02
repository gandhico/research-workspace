# Y6 coaxial tri-rotor in MuJoCo (wind-turbine inspection demo)

Built 2026-09-23. It runs the ComRob-2026 Y6 Nengo controllers, unchanged, on a MuJoCo plant.

```
y6_hexa/
├── nengo_y6/            copy of the backup-drive project (02_Coaxial_TriRotor_Nengo):
│   ├── 01_Code_stages/  stages 1-8 (y6_model.py, NEF attitude … PES FTC … full SNN)
│   └── src/, experiments/, docs/   paper-development tree (exp04 = coaxial trirotor NEF)
├── paper_comrob/        unzipped ComRob 2026 manuscript
└── mujoco_y6/
    ├── y6_turbine_scene.xml   MJCF: Y6 airframe (Mehndiratta & Kayacan Table I) + turbine + cameras
    ├── y6_mujoco_sim.py       MuJoCo plant, mission, wind, classical / NEF runs, plant cross-check
    ├── render_video.py        4-camera mp4 + PNG stills from a logged run
    ├── make_figures.py        figures + results/summary.json
    ├── deck/                  7 NMSU-template slides (build_deck_y6.py → .pptx / .pdf)
    ├── results/               *.npz logs, summary.json
    └── media/                 videos, camera stills, figs/
```

## Run (hyperlif env: mujoco 3.11, nengo 4.1)

**Real-time / live viewer / Nengo GUI: see `GUIDE_realtime.md` and `launchers`.**

```
set PY=C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe
%PY% y6_mujoco_sim.py --validate                         # MuJoCo vs RK4 plant (same controller)
%PY% y6_mujoco_sim.py --ctrl classical                   # ~4 s
%PY% y6_mujoco_sim.py --ctrl nef_lif                     # spiking, ~1 min
%PY% y6_mujoco_sim.py --ctrl nef_lif --wind 4 [--integral]
%PY% make_figures.py
%PY% render_video.py results\nef_lif.npz "Spiking NEF (LIF) + neural allocator"   # ~3 min
C:\Research\hover3dof\.venv\Scripts\python.exe deck\build_deck_y6.py              # python-pptx lives there
```

Interactive viewer: `%PY% -m mujoco.viewer --mjcf=y6_turbine_scene.xml` (it's passive, with no controller).

## Key design points
- **Rotor map.** Each rotor is a `general` actuator on a site with `ctrl = F_i` and `gear = [0 0 1 0 0 ±Ktau/KF]`. That reproduces the τx/τy/τz equations of `coaxial_trirotor.py` exactly. Those equations put rotors 3,4 (single arm) **aft** at x = −l1, which is the standard Y6. The code comments call that arm "front", which is a naming issue only.
- **NEF controller.** `trirotor_nef.build_network` is called unchanged. The only change is that `TrirotorPlantNode` gets monkey-patched to the MuJoCo plant object.
- **Feed-forward** comes in through reference shaping, `x_cmd = x_ref + Kd/Kp·v_ref + a_ref/Kp`, so the controllers themselves stay untouched.
- **Cameras** are MJCF `<camera>` elements (`fpv`, `gimbal_down`, `chase` on the body; `side` and `overview` in the world), rendered off-screen with `mujoco.Renderer` in RGB and depth.

## Results (results/summary.json)
| | x/y/z RMSE [cm], 6–56 s |
|---|---|
| classical | 1.5 / 3.0 / 1.2 |
| spiking NEF (LIF, n_cmd 3000) | 1.7 / 3.4 / 1.3 |
| 4 m/s wind, PD (both) | ~53 / 11 / 2.5 |
| 4 m/s wind, + outer integral (Python node) | ~15 / 12 / 2.3 |

Plant cross-check: 0.48 mm max position difference against the RK4 model over 64 s.

## Not modelled yet
Propeller gyroscopic torque, motor lag, and rotor aerodynamics near the blades. The turbine has no aerodynamics and no wake, and the wind is a simple linear drag. The integral term is not neural yet.

# Y6 + MuJoCo + Nengo: real-time run guide

Written 2026-09-23. Everything below was tested on this laptop that day.

## 1. Where things are

| What | Path |
|---|---|
| Presentation (7 slides, video embedded) | `C:\Research\y6_hexa\mujoco_y6\deck\Y6_MuJoCo_Update_2026-09-23.pptx` |
| Presentation as PDF | `C:\Research\y6_hexa\mujoco_y6\deck\Y6_MuJoCo_Update_2026-09-23.pdf` |
| Video, spiking NEF controller | `C:\Research\y6_hexa\mujoco_y6\media\nef_lif.mp4` |
| Video, classical controller | `C:\Research\y6_hexa\mujoco_y6\media\classical.mp4` |
| Camera stills and figures | `C:\Research\y6_hexa\mujoco_y6\media\` and `media\figs\` |
| One-click launchers | `C:\Research\y6_hexa\mujoco_y6\launchers\` |
| Nengo project (copied from `D:\NMSU_backups\...\02_Coaxial_TriRotor_Nengo`) | `C:\Research\y6_hexa\nengo_y6\` |

## 2. Environment (the "activator")

Everything runs in the **`hyperlif`** conda env. It has Python 3.11, mujoco 3.11, nengo 4.1, nengo-gui 0.6, matplotlib and imageio. The deck builder needs python-pptx, which lives in a different env: `C:\Research\hover3dof\.venv`.

| Shell | Activate |
|---|---|
| cmd / .bat | `call "%USERPROFILE%\AppData\Local\miniconda3\Scripts\activate.bat" hyperlif` |
| PowerShell | `& "$env:USERPROFILE\AppData\Local\miniconda3\shell\condabin\conda-hook.ps1"; conda activate hyperlif` |
| Git Bash | `source ~/AppData/Local/miniconda3/Scripts/activate hyperlif` |
| No activation | `C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe <script>` |

After activating, `cd C:\Research\y6_hexa\mujoco_y6`.

**Fresh laptop:**

```
conda create -n hyperlif python=3.11
conda activate hyperlif
pip install "mujoco==3.11.*" "nengo==4.1.*" nengo-gui matplotlib imageio imageio-ffmpeg pillow
```

## 3. Launchers (double-click in `launchers\`)

| Launcher | What happens |
|---|---|
| `0_open_terminal_hyperlif.bat` | Opens a terminal with the env active, already in `mujoco_y6` |
| `1_live_classical.bat` | MuJoCo window; classical cascade PD flies the 64 s mission in real time |
| `2_live_spiking_nef.bat` | Same mission flown by the **spiking Nengo network**: 4,800 LIF neurons including the neural allocator, running in real time |
| `3_live_spiking_nef_wind_pid.bat` | Spiking controller, 4 m/s wind with gusts, plus the outer integral term |
| `4_nengo_gui_plus_mujoco.bat` | **Nengo GUI in the browser plus the live MuJoCo window**, kept in sync (section 5) |
| `5_viewer_scene_only.bat` | The scene alone, no controller. Useful for looking at the geometry and cameras, and for driving the rotor sliders by hand |
| `6_offline_rebuild_all.bat` | Re-runs every result, figure, both videos and the deck (~12 min) |

Launchers 1–3 pass any extra arguments straight through, for example `2_live_spiking_nef.bat --speed 0.5`.

## 4. The real-time runner: `run_realtime.py`

```
python run_realtime.py [--ctrl classical|nef_lif|nef_rate] [--wind 4] [--integral]
                       [--speed 1.0] [--camera chase|side|overview|fpv|gimbal_down|free] [--n_cmd 3000]
```

**How the loop works:**

```
every 1/60 s of sim time:
    17 x [ controller step (Python PD, or one Nengo step)  ->  6 rotor speeds
           -> MuJoCo mj_step (1 ms) -> 12-state back to the controller ]
    viewer.sync()                         # draw the frame
    sleep so that sim time == wall time x speed
```

- **NEF case.** `nengo.Simulator.run_steps(17)` drives it. The MuJoCo plant *is* the Nengo plant Node, so each Nengo step advances MuJoCo by exactly 1 ms. The network is built by the unchanged `trirotor_nef.build_network()`.
- **Terminal output.** Every 5 s it prints the time, position and **real-time factor**. If you see "CPU-bound", the machine can't keep up.
- **Measured on this laptop:** classical and spiking both hold RTF = 1.00 at `--speed 1`. The spiking net maxes out around 2.2× real time (tested with `--speed 4`), so there is about 2× headroom.
- **Log file.** Each run saves to `results\realtime_<ctrl>.npz`, the same format as the offline runs. You can pass it to `render_video.py`.

**Viewer controls:**

| Key / mouse | Action |
|---|---|
| `[` / `]` | Cycle cameras: overview, side, **fpv** (onboard), gimbal_down, chase |
| `Esc` | Free camera |
| Space | Pause / resume (added in this script) |
| `Tab` / `Shift+Tab` | Hide the left / right panels |
| Left-drag / right-drag / scroll | Rotate / pan / zoom |
| Right panel, "Rendering" | Show contact forces, frames, the camera frustum and more |
| Close the window | Stop; the log is saved |

## 5. Nengo GUI + MuJoCo: `gui_y6_mujoco.py`

1. Run `launchers\4_nengo_gui_plus_mujoco.bat`. The browser opens at `http://localhost:8080/?token=...`. If it doesn't, copy the token URL from the terminal.
2. Press **Play** (bottom right). A MuJoCo window opens and the Y6 takes off. The plant node paces itself to wall-clock time, so the spike plots and the drone move together.
3. Right-click any ensemble (`tau_x`, `ax_des`, `e_cmd`, …) and choose **Spikes**, **Value** or **Firing pattern** to see live neural activity.
4. **Reset** (the rewind button) puts the drone back on the pad.
5. Settings are at the top of `gui_y6_mujoco.py`:
   - `WIND`
   - `N_CMD`: allocator size. It defaults to 1000 so the GUI stays responsive; the paper's exp04 used 3000.
   - `NEURON`
   - `CAMERA`
6. The GUI saves your plot layout to `gui_y6_mujoco.py.cfg`, the same mechanism as your old `gui_y6_stage*.py` files.

## 6. What to edit

| Want to change | Where |
|---|---|
| Mission waypoints (time, x, y, z) | `WAYPOINTS` in `y6_mujoco_sim.py` |
| Hub position used by the look-at heading | `HUB` in `y6_mujoco_sim.py` |
| Wind model (mean, gusts, turbulence, drag c_d) | `class Wind` in `y6_mujoco_sim.py` |
| Controller gains | `nengo_y6\src\controllers_classical\trirotor_pd.py` (`TrirotorGains`); both controllers use them |
| NEF network (populations, radii, allocator) | `nengo_y6\src\controllers_nengo\trirotor_nef.py` |
| Airframe, rotors, cameras, turbine | `y6_turbine_scene.xml`. Keep `gear = Ktau/KF = 0.048905` if you change the rotor coefficients |
| Turbine rotor speed | `turbine_speed` argument of `Y6MuJoCoPlant` (0.8 rad/s) |

## 7. Offline (faster than real time, for results)

```
python y6_mujoco_sim.py --validate                     # MuJoCo vs RK4 plant: 0.48 mm max
python y6_mujoco_sim.py --ctrl nef_lif [--wind 4] [--integral]
python make_figures.py                                 # figs + results\summary.json
python render_video.py results\nef_lif.npz "label"     # 4-camera mp4 (~3 min)
C:\Research\hover3dof\.venv\Scripts\python.exe deck\build_deck_y6.py
```

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `UserWarning: Decoder cache could not acquire lock` | Harmless; two Nengo processes were running at once |
| RTF < 1 ("CPU-bound") | Use `--speed 0.5`, `--n_cmd 1000`, or `--ctrl nef_rate`. Close other heavy programs |
| Nengo GUI port already in use | `nengo_gui -P 8082 gui_y6_mujoco.py` |
| Browser asks for a password | Use the full `?token=...` URL printed in the terminal |
| MuJoCo window is black or fails to open | Update the GPU driver. Remote Desktop sessions often lack OpenGL; run on the laptop screen |
| `ModuleNotFoundError: src` | Run from `mujoco_y6\`; the scripts add `..\nengo_y6` to the path themselves |
| `python-pptx` missing | Use the hover3dof venv for `build_deck_y6.py` only |

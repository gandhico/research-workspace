# Research — working root

Clean, minimal working trees for the neuromorphic-control projects (kept **off** OneDrive to avoid sync churn; heavy old results/PDFs stay in `D:\NMSU_backups\Backup`).

## Layout
```
C:\Research\
├── README.md          <- this file
├── WORKFLOW.md        <- running log: setup, workflow, results, insights (start here)
├── CODE_MAP.md         <- index of every runner/launcher across the whole tree
├── aero2\              <- Aero2 — full offline/twin/hardware pipeline (most mature)
├── pendulum\           <- Qube-Servo 3 — offline/twin/hardware, see pendulum\RUNNERS.md
├── qcar\               <- QCar/QCar2 — offline (host) + hardware (on-car), see qcar\RUNNERS.md
├── qdrone\             <- QDrone/QDrone2 — offline + telemetry-only hardware, see qdrone\RUNNERS.md
├── hover3dof\          <- 3DOF Hover — vendored courseware
├── omnicopter\         <- Omnidrone: MuJoCo twin + ArduPilot 6DoF real vehicle — start at omnicopter\README.md
├── gyro3dof\ qbot\ haptic_hd\ qarm\ qarm_mini\  <- theory paper only, no code yet (see each RUNNERS.md)
├── julia_bridge\       <- cross-platform Julia<->Quanser bridge (all robots' Julia code lives here)
├── julia_env\          <- shared Julia project (Pkg environment)
├── _shared\            <- shared Python campaign module used by several platforms' offline runners
└── papers\             <- P1/P2/P3 HyperLIF paper portfolio
```

## Quick start (Aero2 digital twin)
1. Open **QLabs → Aero 2** (must listen on `localhost:18950`).
2. **Python:** `conda run -n hyperlif python aero2\runners\run_control.py --mode virtual_twin --controller pd --duration 15 --quanser-python "C:\Users\gandhico\Documents\Quanser\0_libraries\python"`
3. **MATLAB:** `matlab -sd C:\Research\aero2\matlab -batch "aero2_twin_pd(15,100)"`

For every other platform, start at **[CODE_MAP.md](CODE_MAP.md)** (top-level
runner index) or the platform's own `RUNNERS.md`. See
**[WORKFLOW.md](WORKFLOW.md)** for the full Aero2 pipeline narrative, results
table, and insights.

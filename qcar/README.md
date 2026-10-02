# QCar/QCar2 HyperLIF Residual Validation

This folder is the QCar/QCar2 branch of the cross-platform Quanser validation
campaign. The platform objective is lane following with a classical image-space
controller as the safe baseline and HyperLIF gate-state residual augmentation as
the bounded correction.

Useful existing material is preserved under `01_Code/hardware`, especially the
hardware-safe runner `qcar2_unified_lane_control_hardware_v1.py` and its logs.
New shared-campaign runners live in `runners/` and write offline outputs to
`results/offline/`.

## Quickstart

```powershell
python .\runners\run_offline_benchmark.py --duration 20
python .\runners\plot_results.py
```

Hardware tomorrow starts with perception-only mode in:

```powershell
python .\01_Code\hardware\qcar2_unified_lane_control_hardware_v1.py --mode perception --duration 30 --no-display
```

Only add `--armed` after camera, lane sign, steering sign, and log writing are
confirmed.


# QDrone/QDrone2 HyperLIF Residual Validation

This folder is the QDrone/QDrone2 branch of the cross-platform Quanser
validation campaign. The platform objective is hover/waypoint holding with a
classical cascaded attitude/altitude baseline plus bounded HyperLIF gate-state
residual corrections.

The folder previously contained the visual-control paper reference only. It now
has offline runners and documentation so QDrone can participate in the same
baseline-vs-residual campaign as QCar, Qube, and Aero2.

## Quickstart

```powershell
python .\runners\run_offline_benchmark.py --duration 20
python .\runners\plot_results.py
```

## Useful Quanser sources

- `C:\Quanser\5_research\autonomous_vehicles\qdrone2`
- `C:\Quanser\0_libraries\python\pal\products\qdrone2.py`
- `C:\Quanser\0_libraries\python\qvl\qdrone2.py`
- `C:\Quanser\3_user_manuals\qdrone2`


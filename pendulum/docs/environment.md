# Servo Pendulum Environment

## Local Environment

Create and activate:

```powershell
cd C:\00_Research_\Neuromorphic_Embodied_AI\07_ServoPendulum_SNNs
.\scripts\setup_env.ps1
.\scripts\activate_env.ps1
```

The setup script creates `.venv` with `--system-site-packages` so installed
Quanser SDK bindings remain visible. It also prepares:

- `PYTHONPATH=<project>\src;C:\Quanser\0_libraries\python;...`
- `QUANSER_PYTHON=C:\Quanser\0_libraries\python`
- a local install of `quanser_api` from `C:\Program Files\Quanser\QUARC\python`

If Quanser is installed elsewhere:

```powershell
.\scripts\setup_env.ps1 -QuanserPython D:\Quanser\0_libraries\python
.\scripts\activate_env.ps1 -QuanserPython D:\Quanser\0_libraries\python
```

If QUARC is installed elsewhere, pass `-QuanserApiWheelDir <path-to-wheels>`.

## Smoke Tests

Offline, no Quanser runtime:

```powershell
python .\runners\run_offline_benchmark.py --duration 5
```

Online virtual twin, zero voltage:

```powershell
python .\runners\run_online_qube.py --mode sensor_check --hardware 0 --duration 5
```

Online virtual twin, closed loop:

```powershell
python .\runners\run_online_qube.py --mode balance --hardware 0 --armed --duration 20
python .\runners\run_online_qube.py --mode hyperlif_residual --hardware 0 --armed --duration 20
```

Physical hardware uses the same commands with `--hardware 1`, after virtual
validation.

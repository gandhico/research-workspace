# Qube Servo/Pendulum Hardware Notes

The newer project runner is:

```powershell
python .\runners\run_online_qube.py --mode sensor_check --hardware 0 --duration 5
python .\runners\run_online_qube.py --mode balance --hardware 0 --armed --duration 20
python .\runners\run_online_qube.py --mode hyperlif_residual --hardware 0 --armed --duration 20
```

Use `--hardware 1` only after the same sequence is clean on the virtual twin.
Closed-loop modes require `--armed`; without it, the runner logs state while
commanding zero voltage.

The legacy read-only helper remains available:

```powershell
python .\hardware\run_qube_sensor_check.py --duration 10
python .\hardware\run_qube_sensor_check.py --connect --hardware 0 --duration 10
```

Do not run closed-loop residual control on physical hardware until:

- Encoder signs are verified.
- Zero-voltage sensor logs look sane.
- A low-voltage baseline balance controller has been tested.
- The virtual twin and physical rig agree on upright angle convention.
- The emergency stop procedure is clear.

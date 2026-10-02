# QDrone/QDrone2 Hardware Notes

Start with the read-only telemetry check:

```powershell
python .\hardware\run_qdrone2_telemetry_check.py --duration 10
python .\hardware\run_qdrone2_telemetry_check.py --connect --ip 192.168.2.15 --duration 10
```

The first command is a dry run. The second connects to the telemetry stream and
logs state vectors, motor commands, current, and battery status.

Do not arm flight from this folder until:

- Telemetry is stable.
- Battery and failsafe states are visible in logs.
- Baseline hover is confirmed using Quanser's standard mission server.
- Residual commands have been replayed offline against recorded baseline logs.


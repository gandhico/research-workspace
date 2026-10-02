# EHEKATL BWB LQR for X-Plane 12

This folder adds a minimal LQR controller beside the working Backstepping/PID
bridge. It reuses the already patched `xpc.py` from:

```text
../backstepping/ehekatl_xplane12_backstepping_bridge/xpc.py
```

It does not modify Backstepping or PID files.

## Health Check

```bash
cd ~/GHYN/Xplane_controllers/EHEKATL_BWB_XP12/lqr
source ../backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/activate
python health_check_xpc.py --host 127.0.0.1 --port 49009
```

## Safe First LQR Run

Use attitude mode first. It uses pitch, roll, heading, and angular rates. If
rate datarefs are unavailable, it falls back to finite differences.

```bash
python run_lqr_xp12.py \
  --duration 0 \
  --hz 20 \
  --mode attitude \
  --routing corrected \
  --pitch-sp 2 \
  --roll-sp 0 \
  --clip 0.12 \
  --throttle -998 \
  --out ../logs/lqr_attitude_safe_xp12_$(date +%Y%m%d_%H%M%S).csv
```

## Full-State First Pass

Full mode attempts to read local velocity datarefs and subtract optional trim
values. Treat this as a first integration pass until body-axis velocity mapping
is validated for the EHEKATL aircraft.

```bash
python run_lqr_xp12.py \
  --duration 0 \
  --hz 20 \
  --mode full \
  --routing corrected \
  --clip 0.25 \
  --throttle -998 \
  --out ../logs/lqr_full_xp12_$(date +%Y%m%d_%H%M%S).csv
```

## Routing

`--routing corrected` sends:

```text
[aileron, elevator, rudder, throttle]
```

`--routing legacy` sends:

```text
[elevator, aileron, rudder, throttle]
```

If the aircraft moves in the wrong control direction, stop with `Ctrl+C`, keep
the saved CSV log, and rerun with the other routing mode or a smaller `--clip`.

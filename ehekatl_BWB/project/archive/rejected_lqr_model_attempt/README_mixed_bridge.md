# EHEKATL BWB X-Plane 12 Python Bridge

This folder contains XP12 closed-loop bridges for Gandhi's original backstepping
controller and a data-identified LQR controller.

## Files

- `Backstepping.py` — original controller math from the uploaded code.
- `PID.py` — original PID helper, kept for reference.
- `xpc.py` — Python 3 compatible XPlaneConnect UDP client.
- `health_check_xpc.py` — verifies Python can read POSI/CTRL from X-Plane.
- `run_backstepping_xp12.py` — runs the original backstepping controller with CSV logging.
- `identify_lqr_model.py` — identifies a structured roll/pitch model from a flight log.
- `LQR.py` — discrete Riccati solver and roll/pitch LQR controller.
- `run_lqr_xp12.py` — runs the identified LQR with CSV logging.

## X-Plane setup

1. Install the XPlaneConnect plugin in:
   `X-Plane 12/Resources/plugins/`
2. Start X-Plane 12.
3. Load `EHEKATL BWB GHYN` on the runway or in flight.
4. Keep the aircraft unpaused and engine/throttle ready.

## Ubuntu setup

```bash
cd ~/EHEKATL_BWB_XP12_Python
python3 -m venv .venv
source .venv/bin/activate
pip install numpy matplotlib
```

Copy these files into that folder.

## Connection check

Try the uploaded-code default port first:

```bash
python health_check_xpc.py --host 127.0.0.1 --port 49009
```

If it times out, try:

```bash
python health_check_xpc.py --host 127.0.0.1 --port 49007
```

If X-Plane is on another computer, replace `127.0.0.1` with the X-Plane machine IP.

## First exact backstepping test

This reproduces the uploaded script routing behavior:

```bash
python run_backstepping_xp12.py --routing legacy --duration 60 --hz 10 --pitch-sp 6 --roll-sp 0 --out logs/backstepping_legacy.csv
```

Then test the corrected XPC control order:

```bash
python run_backstepping_xp12.py --routing corrected --duration 60 --hz 10 --pitch-sp 6 --roll-sp 0 --out logs/backstepping_corrected.csv
```

The corrected routing uses XPC order `[aileron, elevator, rudder, throttle]`.

## Data-driven LQR

Build the model from the known-good original backstepping run:

```bash
python identify_lqr_model.py /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12/logs/backstepping_original_dissertation_20260709_210205.csv --out lqr_model.json
```

Start with a conservative stick limit. The LQR always uses documented XPC actuator
order; the identifier learns from the actual logged aileron/elevator columns even
when the source controller used legacy routing.

```bash
python run_lqr_xp12.py --model lqr_model.json --duration 60 --hz 10 --roll-sp 0 --pitch-sp 6 --clip 0.25 --out logs/lqr_first.csv
```

The default weights are `Q = diag(8, 8, 0.5, 0.5)` and
`R = diag(25, 25)`. They can be changed with `--q` and `--r`. This model comes
from closed-loop data, so validate it at altitude with the conservative limit
before increasing control authority.

## Safety notes

- Use `--clip 0.25` for a soft first test if the aircraft is too sensitive.
- Use `--throttle -998` to keep the current manual throttle.
- Stop with Ctrl+C.

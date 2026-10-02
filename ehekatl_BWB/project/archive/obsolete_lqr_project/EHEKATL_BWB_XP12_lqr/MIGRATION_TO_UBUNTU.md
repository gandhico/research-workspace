# EHEKATL BWB LQR Migration to Ubuntu

Target project:

```text
/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
```

This bundle installs only new LQR files. It does not modify the working
Backstepping/PID bridge.

## 1. Copy This Bundle to Ubuntu

From Windows PowerShell, copy the folder or zip to the Ubuntu computer. Example:

```powershell
scp -r C:\00_Research_\Neuromorphic_Embodied_AI\03_LQR_BWB_Nengo\ubuntu_migration\EHEKATL_BWB_XP12_lqr ubuntu@UBUNTU_IP:/home/ubuntu/GHYN/Xplane_controllers/
```

Replace `UBUNTU_IP` with the Ubuntu machine address.

## 2. Install Into the Existing XP12 Project

On Ubuntu:

```bash
cd ~/GHYN/Xplane_controllers/EHEKATL_BWB_XP12_lqr
bash install_lqr_migration.sh /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
```

## 3. Activate the Existing Environment

```bash
cd ~/GHYN/Xplane_controllers/EHEKATL_BWB_XP12/lqr
source ../backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/activate
```

## 4. Check XPlaneConnect

```bash
python health_check_xpc.py --host 127.0.0.1 --port 49009
```

## 5. Run the Safe LQR Attitude Test

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

Stop with `Ctrl+C`. The CSV log is still saved cleanly.

## 6. Run the Full-State First Pass

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

Full mode attempts local velocity datarefs. If they are unavailable, the runner
prints the fallback and uses zero translational perturbations.

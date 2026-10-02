Connect with the Qcar

ssh nvidia@192.168.1.129

reseach folder

cd ~/Documents/Quanser/examples/sdcs/qcar2/hardware/applications/GHYN/lane__following_research
ls -lah

python3 QCar2_task_manual_drive_Joystick.py

First PID hardware controller working

python3 qcar2_unified_lane_control_hardware_v1.py \
  --mode lane \
  --controller pid \
  --armed \
  --duration 10 \
  --no-display \
  --max-throttle 0.080 \
  --base-throttle 0.070 \
  --min-throttle 0.050 \
  --max-steering 0.25 \
  --steering-sign 1.0

  PID - Stronger baseline
python3 qcar2_unified_lane_control_hardware_v1.py \
  --mode lane \
  --controller pid \
  --armed \
  --duration 15 \
  --no-display \
  --max-throttle 0.120 \
  --base-throttle 0.100 \
  --min-throttle 0.070 \
  --max-steering 0.35 \
  --pid-kp 1.8 \
  --pid-kd 0.08 \
  --pid-slope-gain 0.90 \
  --steering-sign 1.0


SMC - Stronger baseline
  python3 qcar2_unified_lane_control_hardware_v1.py \
  --mode lane \
  --controller smc \
  --armed \
  --duration 15 \
  --no-display \
  --max-throttle 0.110 \
  --base-throttle 0.095 \
  --min-throttle 0.070 \
  --max-steering 0.35 \
  --smc-error-gain 1.30 \
  --smc-slope-gain 0.70 \
  --smc-switch-gain 0.12 \
  --smc-lambda 1.60 \
  --smc-boundary 0.35 \
  --smc-surface-slope-gain 0.45 \
  --steering-sign 1.0

NMPC - image-state - stronger baseline
python3 qcar2_unified_lane_control_hardware_v1.py \
  --mode lane \
  --controller nmpc_image \
  --armed \
  --duration 15 \
  --no-display \
  --max-throttle 0.100 \
  --base-throttle 0.085 \
  --min-throttle 0.065 \
  --max-steering 0.32 \
  --nmpc-horizon 10 \
  --nmpc-candidates 11 \
  --nmpc-beam 20 \
  --nmpc-q-error 18.0 \
  --nmpc-q-slope 0.50 \
  --nmpc-r-steer 0.10 \
  --nmpc-r-dsteer 0.35 \
  --nmpc-rate-limit 0.085 \
  --steering-sign 1.0

  Adaptive HyperLIF gate - full controller, strongerpython3 qcar2_unified_lane_control_hardware_v1.py \
  --mode lane \
  --controller adaptive_hyperlif_gate \
  --armed \
  --duration 15 \
  --no-display \
  --max-throttle 0.110 \
  --base-throttle 0.095 \
  --min-throttle 0.070 \
  --max-steering 0.35 \
  --family-kp 5.0 \
  --family-kd 0.055 \
  --family-slope-gain 1.20 \
  --family-gate-gain 0.85 \
  --family-output-limit 0.35 \
  --family-adapt-gain 0.05 \
  --steering-sign 1.0

  PID + gated Adaptive HyperLIF residual — stronger residual
  python3 qcar2_unified_lane_control_hardware_v1.py \
  --mode lane \
  --controller pid_gated_adaptive_hyperlif_residual \
  --armed \
  --duration 15 \
  --no-display \
  --max-throttle 0.120 \
  --base-throttle 0.100 \
  --min-throttle 0.075 \
  --max-steering 0.35 \
  --pid-kp 1.8 \
  --pid-kd 0.08 \
  --pid-slope-gain 0.90 \
  --family-kp 5.0 \
  --family-kd 0.055 \
  --family-slope-gain 1.20 \
  --family-gate-gain 0.85 \
  --family-output-limit 0.35 \
  --family-residual-gain 0.35 \
  --family-residual-limit 0.080 \
  --residual-gate-min 0.40 \
  --steering-sign 1.0

  SMC + gated Adaptive HyperLIF residual — stronger residual
  python3 qcar2_unified_lane_control_hardware_v1.py \
  --mode lane \
  --controller smc_gated_adaptive_hyperlif_residual \
  --armed \
  --duration 15 \
  --no-display \
  --max-throttle 0.115 \
  --base-throttle 0.100 \
  --min-throttle 0.075 \
  --max-steering 0.35 \
  --smc-error-gain 1.30 \
  --smc-slope-gain 0.70 \
  --smc-switch-gain 0.12 \
  --smc-lambda 1.60 \
  --smc-boundary 0.35 \
  --smc-surface-slope-gain 0.45 \
  --family-kp 5.0 \
  --family-kd 0.055 \
  --family-slope-gain 1.20 \
  --family-gate-gain 0.85 \
  --family-output-limit 0.35 \
  --family-residual-gain 0.35 \
  --family-residual-limit 0.080 \
  --residual-gate-min 0.40 \
  --steering-sign 1.0

NMPC + gated Adaptive HyperLIF residual — strongest experimental run
python3 qcar2_unified_lane_control_hardware_v1.py \
  --mode lane \
  --controller nmpc_gated_adaptive_hyperlif_residual \
  --armed \
  --duration 15 \
  --no-display \
  --max-throttle 0.105 \
  --base-throttle 0.090 \
  --min-throttle 0.070 \
  --max-steering 0.32 \
  --nmpc-horizon 10 \
  --nmpc-candidates 11 \
  --nmpc-beam 20 \
  --nmpc-q-error 18.0 \
  --nmpc-q-slope 0.50 \
  --nmpc-r-steer 0.10 \
  --nmpc-r-dsteer 0.35 \
  --nmpc-rate-limit 0.085 \
  --family-kp 5.0 \
  --family-kd 0.055 \
  --family-slope-gain 1.20 \
  --family-gate-gain 0.85 \
  --family-output-limit 0.35 \
  --family-residual-gain 0.35 \
  --family-residual-limit 0.080 \
  --residual-gate-min 0.40 \
  --steering-sign 1.0
  

  Shut down

  sudo shutdown now



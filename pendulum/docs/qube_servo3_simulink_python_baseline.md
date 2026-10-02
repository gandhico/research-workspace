# Qube Servo 3 Python Baseline: Simulink `qs3_balance.slx` Replication

**Status:** working baseline confirmed in the virtual twin.  
**Confirmed command:** manual-swing, latched-engagement, upright-offset version.  
**Use this as the classical baseline before adding HyperLIF residual augmentation.**

---

## 1. Purpose

This document records the current working baseline for the Qube Servo 3 / rotary pendulum branch:

```text
C:\00_Research_\Neuromorphic_Embodied_AI\07_ServoPendulum_SNNs
```

The goal is to reproduce the behavior of the Quanser Simulink balance model:

```text
qs3_balance.slx
```

in Python, so that we can use it as a clean classical baseline and later add a bounded HyperLIF gate-state residual on top.

The final working behavior is:

```text
1. Python starts.
2. Motor remains at 0 V.
3. The controller waits for manual pendulum swing.
4. The controller detects that the pendulum has moved away from the rest/downward state.
5. When the pendulum returns close to the upright equilibrium region, the balance controller engages.
6. Once engaged, the controller remains active while the pendulum stays inside the capture/release band.
7. The base motion is smooth and the pendulum remains balanced.
```

---

## 2. Environment Initialization

Open PowerShell and go to the project root:

```powershell
cd C:\00_Research_\Neuromorphic_Embodied_AI\07_ServoPendulum_SNNs
```

Activate the Python environment:

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& C:\02_Research\00_Code_Ecosystem\neuromorphic-robotics-control\.venv\Scripts\Activate.ps1)
```

If local imports fail, set `PYTHONPATH`:

```powershell
$env:PYTHONPATH = "$PWD\src;$env:PYTHONPATH"
```

Quanser Python is expected at:

```text
C:\Quanser\0_libraries\python
```

If the Quanser examples require the plotting scope, install:

```powershell
python -m pip install pyqtgraph PyQt5
```

If `PyQt5` fails:

```powershell
python -m pip install pyqtgraph PySide6
```

---

## 3. Recommended Sanity Checks

List copied Quanser examples:

```powershell
python .\runners\run_quanser_provided.py --list
```

Check QUARC / Quanser runtime:

```powershell
python .\runners\run_quanser_provided.py --example test_quarc --i-understand
```

Expected output:

```text
Pass
```

Optional Quanser read/write example:

```powershell
python .\runners\run_quanser_provided.py --example read_write3 --i-understand
```

---

## 4. Current Working Baseline Runner

Use:

```text
.\runners\run_simulink_balance.py
```

which imports:

```text
.\src\servo_pendulum_snn\simulink_balance_runner.py
```

This is the Python implementation that should now be treated as the **main classical baseline**.

---

## 5. Confirmed Working Virtual-Twin Command

This is the command that worked perfectly and should be used as the current baseline:

```powershell
python .\runners\run_simulink_balance.py --hardware 0 --armed --duration 30 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05
```

Meaning:

```text
--hardware 0
    Use virtual twin.

--armed
    Allow nonzero motor voltage.

--duration 30
    Run for 30 seconds.

--require-manual-swing
    Do not engage immediately at startup.
    Wait until the user manually moves/swing the pendulum.

--manual-swing-release-deg 15
    The pendulum must first move more than 15 deg away from the initial region before the controller is allowed to engage.

--alpha-upright-offset-deg 180
    Treat raw alpha near ±180 deg as the upright equilibrium.
    This was necessary because the Python raw angle convention did not match the Simulink balance point directly.

--capture-angle-deg 10
    Engage near the upright point when the adjusted pendulum angle is within ±10 deg.

--capture-hysteresis-deg 2
    Keep the controller active until the pendulum leaves a slightly wider band.
    This avoids chattering at the switching boundary.

--engage-confirm-samples 3
    Require 3 consecutive valid samples before enabling balance.

--max-engage-alpha-dot 3.0
    Only use the velocity gate before first engagement.
    This prevents engaging while the pendulum is passing too fast through the upright region.

--theta-ref-mode current_on_engage
    At the moment of engagement, use the current base angle as the base reference.
    This avoids a sudden jump toward the Simulink fixed +30 deg reference.

--soft-start-s 0.05
    Smoothly ramps the motor command during the first 0.05 s after engagement.
```

---

## 6. Hardware Test Command

For physical hardware, start short and conservative:

```powershell
python .\runners\run_simulink_balance.py --hardware 1 --armed --duration 8 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05
```

If stable, increase duration:

```powershell
python .\runners\run_simulink_balance.py --hardware 1 --armed --duration 20 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05
```

```powershell
python .\runners\run_simulink_balance.py --hardware 1 --armed --duration 120 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05
```

Emergency stop:

```text
Ctrl+C
```

The runner sends zero voltage during shutdown.

---

## 7. Simulink Model Structure

The Simulink diagram contains the following relevant elements:

```text
Constant:
    theta_ref = 30 deg

D2R:
    theta_ref_rad = 30*pi/180

Base error:
    e_theta = theta_ref_rad - theta

Signal inversions:
    -theta
    -alpha

Filtered derivatives:
    theta_dot block: 50s / (s + 50)
    alpha_dot block: 50s / (s + 50)

Gains:
    kp_theta = -2
    kd_theta = -2
    kp_alpha = 30
    kd_alpha = 2.5

Balance switch:
    enable if |alpha| <= 10 deg

Qube block:
    Qube With Pendulum

Displays:
    Base angle in degrees
    Pendulum angle in degrees
```

---

## 8. Python Control Law

The Python baseline follows the same control idea, with additional practical gates to reproduce the virtual-twin behavior.

### 8.1 Angle Definitions

Raw measured angles:

```text
theta = rotary/base angle
alpha_raw = pendulum angle reported by the Qube interface
```

The working Python baseline uses an upright offset:

```text
alpha = wrap_to_pi(alpha_raw - pi)
```

because the virtual-twin raw angle convention places the upright balance point near `alpha_raw = ±pi`.

In command-line form:

```powershell
--alpha-upright-offset-deg 180
```

### 8.2 Base Reference

Strict Simulink behavior uses:

```text
theta_ref = 30 deg = pi/6 rad
```

The current working Python baseline uses:

```text
theta_ref_active = theta at the moment of engagement
```

because this avoids a large base jump when the controller first catches the pendulum.

In command-line form:

```powershell
--theta-ref-mode current_on_engage
```

The base error is:

```text
e_theta = theta_ref_active - theta
```

### 8.3 Filtered Derivatives

The Simulink derivative filter is:

```text
D(s) = 50s / (s + 50)
```

The Python code implements the equivalent filtered derivative behavior with:

```text
derivative_bandwidth_rad_s = 50
sample_time = 0.002 s
```

for:

```text
theta_dot_sim = filtered_derivative(-theta)
alpha_dot_sim = filtered_derivative(-alpha)
```

### 8.4 PD Balance Law

Using the Simulink gains:

```text
kp_theta = -2
kd_theta = -2
kp_alpha = 30
kd_alpha = 2.5
```

and defining:

```text
neg_alpha = -alpha
```

the internal controller voltage before the final motor sign is:

```text
u_controller =
    kp_theta * e_theta
  + kd_theta * theta_dot_sim
  + kp_alpha * neg_alpha
  + kd_alpha * alpha_dot_sim
```

The motor sign is:

```text
motor_sign = -1
```

so the command sent to the Qube is:

```text
u_motor = motor_sign * u_controller
```

The command is clipped:

```text
u_motor = clip(u_motor, -voltage_limit, +voltage_limit)
```

---

## 9. Engagement Logic

The final working logic is not just a PD controller. The switch behavior matters.

### 9.1 Startup Behavior

At startup, the motor remains at zero voltage:

```text
u = 0
```

The controller does not engage immediately, even if the measured adjusted angle appears near a capture region. It waits for manual swing.

### 9.2 Manual Swing Requirement

Before balance is allowed:

```text
manual_swing_seen = True
```

only after the pendulum has moved far enough away:

```text
|alpha_control| > manual_swing_release_deg
```

with:

```text
manual_swing_release_deg = 15 deg
```

This reproduces the useful behavior observed in Simulink: the model waits until the user rotates the pendulum and then catches it near upright.

### 9.3 Pre-Engagement Capture Conditions

The controller is allowed to engage only when:

```text
|alpha_control| <= capture_angle_deg
```

with:

```text
capture_angle_deg = 10 deg
```

and this must be true for:

```text
engage_confirm_samples = 3
```

consecutive samples.

Additionally, before engagement only:

```text
|alpha_dot_sim| <= max_engage_alpha_dot
```

with:

```text
max_engage_alpha_dot = 3.0 rad/s
```

### 9.4 Latched Engagement

Once balance has engaged, the velocity gate is no longer used to turn it off.

This was critical. The earlier version turned the controller off as soon as alpha velocity became large, even though the pendulum was inside the capture region. Simulink does not behave that way.

Final behavior:

```text
Before engagement:
    require manual swing
    require angle capture
    require alpha_dot not too fast

After engagement:
    keep controlling while inside the angle band
    do not disable only because alpha_dot becomes large
```

The hysteresis band is:

```text
release_angle = capture_angle_deg + capture_hysteresis_deg
```

with:

```text
release_angle = 10 + 2 = 12 deg
```

---

## 10. Confirmed Log Evidence

Two successful logs were provided:

```text
qube3_simulink_balance_20260612_040017.csv
qube3_simulink_balance_20260612_040101.csv
```

Both were 30-second virtual-twin tests.

Summary:

| Metric | Run `040017` | Run `040101` |
|---|---:|---:|
| Duration | 29.998 s | 29.998 s |
| Samples | 15000 | 15000 |
| Median sample time | 0.002006 s | 0.002009 s |
| Median rate | 498.4 Hz | 497.8 Hz |
| First balance engagement | 8.574 s | 8.959 s |
| Active balance samples | 10713 | 10521 |
| Waiting/capture samples | 4287 | 4479 |
| Final adjusted alpha | 0.176 deg | 0.176 deg |
| Max adjusted alpha after engagement | 10.898 deg | 10.898 deg |
| Command voltage range | -4.49 to +5.00 V | -4.52 to +5.00 V |
| RMS voltage after engagement | 0.369 V | 0.362 V |

Interpretation:

```text
The runner waits at zero voltage, detects the manual swing, engages near upright, and holds the pendulum balanced for the rest of the 30-second trial.
```

---

## 11. Comparison With Earlier Python Controller

The older generic balance runner:

```powershell
python .\runners\run_online_qube.py --mode balance ...
```

was useful for debugging, but it should not be the main baseline anymore.

The earlier generic controller exposed arbitrary gain vectors such as:

```powershell
--balance-gains 2.0 -20.0 1.2 -2.5
```

but it did not reproduce all critical Simulink details:

```text
1. Manual waiting behavior
2. Upright alpha offset
3. Simulink-style switch behavior
4. Latched engagement
5. 50s/(s+50) derivative-filter convention
6. Final motor sign convention
7. Current-on-engage base reference
8. Reduced real-time printing and end-of-run CSV writing
```

Therefore:

```text
Use run_simulink_balance.py as the classical baseline.
Keep run_online_qube.py for older debugging and generic controller experiments.
```

---

## 12. Recommended Experiment Order

### Step 1 — Confirm runtime

```powershell
python .\runners\run_quanser_provided.py --example test_quarc --i-understand
```

### Step 2 — Sensor check

```powershell
python .\runners\run_online_qube.py --mode sensor_check --hardware 0 --duration 5
```

### Step 3 — Confirm Python Simulink baseline

```powershell
python .\runners\run_simulink_balance.py --hardware 0 --armed --duration 30 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05
```

### Step 4 — Hardware short run

```powershell
python .\runners\run_simulink_balance.py --hardware 1 --armed --duration 8 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05
```

### Step 5 — Hardware longer run

```powershell
python .\runners\run_simulink_balance.py --hardware 1 --armed --duration 20 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05
```

### Step 6 — Add HyperLIF residual later

Only after the Simulink baseline is repeatable:

```text
baseline → baseline + bounded HyperLIF residual
```

The residual should not replace the balance law. It should be added as a small bounded correction:

```text
u_total = u_baseline + u_residual
```

with:

```text
|u_residual| <= 0.25 V initially
```

Recommended first residual settings later:

```text
residual_limit = 0.25
residual_blend = 0.05
```

---

## 13. Log Location

All online logs are saved to:

```text
.\results\online
```

Example:

```text
.\results\online\qube3_simulink_balance_20260612_040101.csv
```

Important columns:

```text
time_s
mode
armed
hardware
control_mode
loop_dt_s
theta_rad
theta_ref_active_rad
alpha_raw_rad
alpha_control_rad
theta_dot_sim_rad_s
alpha_dot_sim_rad_s
motor_current_a
command_voltage
controller_info_json
state_json
```

Useful control modes:

```text
waiting_for_capture_zero
waiting_for_confirm_zero
simulink_balance
```

---

## 14. Quick CSV Analysis Snippet

Use this to inspect a log:

```powershell
python - <<'PY'
import pandas as pd
import numpy as np
from pathlib import Path

path = Path(r".\results\online\qube3_simulink_balance_YYYYMMDD_HHMMSS.csv")
df = pd.read_csv(path)

dt = df["time_s"].diff().dropna()
active = df["control_mode"].eq("simulink_balance")

print("file:", path)
print("rows:", len(df))
print("duration:", df["time_s"].iloc[-1])
print("median dt:", dt.median())
print("median rate Hz:", 1.0 / dt.median())
print("control modes:")
print(df["control_mode"].value_counts())
print("first active time:", df.loc[active, "time_s"].min() if active.any() else None)
print("final alpha_control deg:", np.degrees(df["alpha_control_rad"].iloc[-1]))
print("final theta deg:", np.degrees(df["theta_rad"].iloc[-1]))
print("command voltage min/max:", df["command_voltage"].min(), df["command_voltage"].max())
PY
```

---

## 15. Baseline Statement for Research Notes

Suggested wording:

```text
The classical Python baseline reproduces the Quanser Simulink Qube Servo 3 balance-control architecture, including the upright capture switch, filtered derivative structure, proportional-derivative balance law, voltage saturation, and final motor sign convention. Additional practical gates were added to match the observed virtual-twin behavior from Simulink: manual-swing detection, engagement confirmation, upright angle offset, latched engagement, and current-on-engage base reference. This baseline reliably balances the virtual twin and will be used as the reference controller before evaluating bounded HyperLIF residual augmentation.
```

---

## 16. Current Decision

Use this as the official baseline:

```text
Python Simulink baseline:
    .\runners\run_simulink_balance.py

Core implementation:
    .\src\servo_pendulum_snn\simulink_balance_runner.py

Confirmed command:
    --require-manual-swing
    --manual-swing-release-deg 15
    --alpha-upright-offset-deg 180
    --capture-angle-deg 10
    --capture-hysteresis-deg 2
    --engage-confirm-samples 3
    --max-engage-alpha-dot 3.0
    --theta-ref-mode current_on_engage
    --soft-start-s 0.05
```

This is now the baseline for the Qube Servo 3 balance experiments.
